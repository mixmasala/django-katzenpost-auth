
from twisted.web.resource import Resource
from twisted.web.server import Site


class Command(Resource):

    isLeaf = True

    def __init__(self, store):
        self.store = store
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
        keys = request.args
        print "ADDUSER", keys
        if 'username' not in keys:
            request.setResponseCode(400)
            return 'bad request: empty username'
        if 'idkey' not in keys:
            request.setResponseCode(400)
            return 'bad request: empty idkey'
        if 'linkkey' not in keys:
            request.setResponseCode(400)
            return 'bad request: empty linkkey'

        username = keys.get('username')[0]
        idkey = keys.get('idkey')[0]
        linkkey = keys.get('linkkey')[0]

        try:
            self.store.new(username, idkey, linkkey)
        except Exception as exc:
            request.setResponseCode(500)
            return 'error: %r' % exc
        return 'ok'


class GetKeyCommand(Command):

    def render_POST(self, request):
        print "POST REQUEST", request
        return 'ok'


# TODO this should be pluggable
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


def getSite():
    root = Command(None)
    root.isLeaf = False
    
    backend = DjangoBackend()
    root.putChild('adduser', AddUserCommand(backend))
    root.putChild('getkey', GetKeyCommand(backend))
    site = Site(root)
    return site
