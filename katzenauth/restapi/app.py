import datetime
import hmac
import hashlib
import json
import time

from twisted.internet import task
from twisted.web.resource import Resource
from twisted.web.server import Site

from adjspecies import random_adjspecies


try:
    from local_settings import SECRET
except ImportError:
    # TODO get from django backend config
    SECRET = 'changethisinproduction'

REGISTRATION_HELP = """
<p>POST params: idkey, linkkey, [pre|token,hmac]

<pre>curl -X POST -d "idkey=deadbeef&linkkey=deadbeef" http://provider:7900/register</pre>

<p>You can also pass the "pre" parameter, so that the server suggests you an username, together with a verification hmac:</p>
<pre>curl -X POST -d "pre=1" localhost:7900/register</pre>
<pre>{"username": "CalmedSheep02", "token": "1517439761:calmedsheep", "hmac": "27acbbe37e891186d3be7a28887904ba5656b927"}</pre>
<p>If you like that suggested username, you can proceed with the registration:</p>
<pre>curl -X POST -d "token=1517439761:CalmedSheep22&hmac=27acbbe37e891186d3be7a28887904ba5656b927&idkey=deadbeef&linkkey=deadbeef" localhost:7900/register</pre>
<pre>{"register": "CalmedSheep22"}</pre>
"""


def make_digest(message):
    return hmac.new(SECRET, message, hashlib.sha1).hexdigest()



def success(action, result=True):
    return json.dumps({action: result})


def failure(action, request, message="", code=401):
    request.setResponseCode(code)
    return json.dumps({action: False, 'message': message})


def check_args(request, key):
    if key not in request.args:
        return False
    return True


def get_arg(request, key):
    try:
        return request.args.get(key)[0]
    except Exception:
        return None


class Command(Resource):

    isLeaf = True

    def __init__(self, backend):
        self.backend = backend
        Resource.__init__(self)

    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request)

    def render_GET(self, request):
	print "GET", request.path
        return "Katzenpost Key Management. You can POST to: register, adduser, isvalid, exists, getidkey"


class AddUserCommand(Command):

    action = 'adduser'

    def render_POST(self, request):
        print "ADDUSER", request.args
        if not check_args(request, 'username'):
            return failure(self.action, request, 'bad request: empty username', 400)
        if not check_args(request, 'idkey'):
            return failure(self.action, request, 'bad request: empty idkey', 400)
        if not check_args(request, 'linkkey'):
            return failure(self.action, request, 'bad request: empty linkkey', 400)

        username = get_arg(request, 'username')
        idkey = get_arg(request, 'idkey')
        linkkey = get_arg(request, 'linkkey')

        try:
            self.backend.new(username, idkey, linkkey)
        except Exception as exc:
            request.setResponseCode(500)
            return 'error: %r' % exc
        return success(self.action)


class RegisterCommand(Command):

    action = 'register'

    def render_GET(sef, request):
        return REGISTRATION_HELP

    def render_POST(self, request):
        pre = get_arg(request, 'pre')
        SEP = ":"
        username = None

        if pre:
            username = random_adjspecies()
            token = str(int(time.time())) + SEP + username
            hmac_token = make_digest(token)
            return json.dumps(
                {'username': username,
                 'token': token,
                 'hmac': hmac_token})

        token = get_arg(request, 'token')
        if token:
            print "TOKEN>>", token
            if not check_args(request, 'hmac'):
                return failure(self.action, request, 'bad request: empty hmac', 400)
            received_hmac = get_arg(request, 'hmac')
            ts, claimed_username = token.split(SEP)

            if ts < time.time() - 60 * 5:
                return failure(self.action, request, 'bad request: expired token', 400)

            expected = make_digest(token)
            if not hmac.compare_digest(received_hmac, expected):
                return failure(self.action, request, 'bad request: corrupted hmac', 400)
            username = claimed_username
            

        if not check_args(request, 'idkey'):
            return failure(self.action, request, 'bad request: empty idkey', 400)
        if not check_args(request, 'linkkey'):
            return failure(self.action, request, 'bad request: empty linkkey', 400)


        idkey = get_arg(request, 'idkey')
        linkkey = get_arg(request, 'linkkey')

        if not username:
            username = random_adjspecies()

        try:
            self.backend.new(username, idkey, linkkey)
        except Exception as exc:
            # XXX have retries here
            request.setResponseCode(500)
            return failure(self.action, request, 'error: %r' % exc, 500)
        return success(self.action, username)



class GetIDKeyCommand(Command):

    action = 'getidkey'

    def render_POST(self, request):
        if not check_args(request, 'username'):
            return failure(self.actoin, request, 'bad request: empty username', 400)
        username = get_arg('username')
        result = self.backend.get_idkey(username)
        return success(self.action, result)


class IsValidCommand(Command):

    action = 'isvalid'

    def render_POST(self, request):
        print('POST isvalid/', request.args)
        if not check_args(request, 'key'):
            return failure(self.action, request, 'bad request: empty key', 400)
        if not check_args(request, 'user'):
            return failure(self.action, request, 'bad request: empty user', 400)

        username = get_arg(request, 'user')
        linkkey = get_arg(request, 'key')

        result = self.backend.is_valid(linkkey, username)
        return success(self.action, result)


class ExistsCommand(Command):

    action = 'exists'

    def render_POST(self, request):
        if not check_args(request, 'user'):
            return failure(self.action, request, 'bad request: empty user', 400)

        username = get_arg(request, 'user')
        result = self.backend.exists(username)
        return success(self.action, result)

# TODO Pluggable django backend ----------------------

from katzen.models import User, IDKey, LinkKey


class DjangoBackend():

    # expire every day
    ACCOUNT_LIFETIME_SEC = 60 * 60 * 24 * 1
    # check every hour
    EXPIRY_CHECK_SEC = 60 * 60

    def __init__(self, root):
        self.root = root

        self.users = User.objects
        self.ikeys = IDKey.objects
        self.lkeys = LinkKey.objects

    def expireAccounts(self):
        cutoff = datetime.datetime.now() - datetime.timedelta(0, self.ACCOUNT_LIFETIME_SEC)
        print('>>> Expiring accounts older than: %s' % cutoff)
        self.users.filter(date_joined__lt=cutoff, is_staff=False).delete()

    def addCommand(self, endpoint, command):
        self.root.putChild(endpoint, command(self))

    def new(self, username, idkey, linkkey):
        user = self.users.create(username=username)
        user.idkey.key = idkey
        user.save()
        lkey = user.linkkey_set.all()[0]
        lkey.key = linkkey
        lkey.save()

    def get_idkey(self, username):
        user = self.users.get(username=username)
        return user.idkey.key

    def is_valid(self, link_key, username):
        user = self.users.get(username=username)
        link_keys = [lk.key.lower() for lk in user.linkkey_set.all()]
        result = link_key.lower() in link_keys
        print("VALID?", link_key, username, result)
        return result


    def exists(self, username):
        return self.users.filter(username=username).count() != 0

# ----------------------------------------------------------------



def getSite():
    root = Command(None)
    root.isLeaf = False
    
    backend = DjangoBackend(root)
    backend.addCommand('adduser', AddUserCommand)
    backend.addCommand('getidkey', GetIDKeyCommand)
    backend.addCommand('isvalid', IsValidCommand)
    backend.addCommand('exists', ExistsCommand)
    backend.addCommand('register', RegisterCommand)

    site = Site(root)
    site.backend = backend
    return site
