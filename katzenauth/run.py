#!/usr/bin/env python
from hendrix.deploy.base import HendrixDeploy
from katzenauth.wsgi import application
from restapi.app import getSite

deployer = HendrixDeploy(options={'wsgi': application})
reactor = deployer.reactor
reactor.listenTCP(7900, getSite())

deployer.run()
