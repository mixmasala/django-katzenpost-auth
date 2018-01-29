
from twisted.web.resource import Resource
from twisted.web.server import Site


class Command(Resource):

    isLeaf = True

    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request)

    def render_GET(self, request):
	print "GET", request.path
        return "Katzenpost Key Management. Please POST to: adduser, getkey"


class AddUserCommand(Command):

    def render_POST(self, request):
        pass


class GetKeyCommand(Command):

    def render_POST(self, request):
        pass


def getSite():
    root = Command()
    root.isLeaf = False
    root.putChild('adduser', Command())
    root.putChild('getkey', Command())
    site = Site(root)
    return site
