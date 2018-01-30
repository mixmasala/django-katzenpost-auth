import json

from twisted.web.resource import Resource
from twisted.web.server import Site


def check_args(request, key):
    if key not in request.args:
        request.setResponseCode(400)
        return False
    return True

def get_arg(request, key):
    return request.args.get(key)[0]


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
        return "Katzenpost Key Management. Please POST to: adduser, getkey"


class AddUserCommand(Command):

    def render_POST(self, request):
        print "ADDUSER", request.args
        if not check_args(request, 'username'):
            return 'bad request: empty username'
        if not check_args(request, 'idkey'):
            return 'bad request: empty idkey'
        if not check_args(request, 'linkkey'):
            return 'bad request: empty linkkey'

        username = get_arg(request, 'username')
        idkey = get_arg(request, 'idkey')
        linkkey = get_arg(request, 'linkkey')

        try:
            self.backend.new(username, idkey, linkkey)
        except Exception as exc:
            request.setResponseCode(500)
            return 'error: %r' % exc
        return 'ok'


class GetIDKeyCommand(Command):

    def render_POST(self, request):
        if not check_args(request, 'username'):
            return 'bad request: empty username'
        username = get_arg('username')
        idkey = self.backend.get_idkey(username)
        response = {'key': idkey}
        return json.dumps(response)


class IsValidCommand(Command):

    def render_POST(self, request):
        if not check_args(request, 'linkkey'):
            return 'bad request: empty linkkey'
        if not check_args(request, 'username'):
            return 'bad request: empty username'
        username = get_arg(request, 'username')
        linkkey = get_arg(request, 'linkkey')

        idkey = self.backend.is_valid(linkkey, username)
        response = {'isvalid': idkey}
        return json.dumps(response)

# TODO Pluggable django backend ----------------------

from katzen.models import User, IDKey, LinkKey


class DjangoBackend():

    def __init__(self):
        self.users = User.objects
        self.ikeys = IDKey.objects
        self.lkeys = LinkKey.objects

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
        link_keys = [lk.key for lk in user.linkkey_set.all()]
        return link_key in link_keys

    def exists(self, username):
        return self.users.filter(username=username).count() != 0

# ----------------------------------------------------------------



def getSite():
    root = Command(None)
    root.isLeaf = False
    
    backend = DjangoBackend()
    root.putChild('adduser', AddUserCommand(backend))
    root.putChild('getidkey', GetIDKeyCommand(backend))
    root.putChild('isvalid', IsValidCommand(backend))
    site = Site(root)
    return site
