import json

from twisted.web.resource import Resource
from twisted.web.server import Site

from adjspecies import random_adjspecies


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

    def render_POST(self, request):
        if not check_args(request, 'idkey'):
            return failure(self.action, request, 'bad request: empty idkey', 400)
        if not check_args(request, 'linkkey'):
            return failure(self.action, request, 'bad request: empty linkkey', 400)

        idkey = get_arg(request, 'idkey')
        linkkey = get_arg(request, 'linkkey')

        username = random_adjspecies()
        try:
            self.backend.new(username, idkey, linkkey)
        except Exception as exc:
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

    def __init__(self, root):
        self.root = root

        self.users = User.objects
        self.ikeys = IDKey.objects
        self.lkeys = LinkKey.objects

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
    return site
