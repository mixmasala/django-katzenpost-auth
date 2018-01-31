#!/usr/bin/env python
from hendrix.deploy.base import HendrixDeploy
from twisted.internet import task
from twisted.python import log

from katzenauth.wsgi import application
from restapi.app import getSite

deployer = HendrixDeploy(options={'wsgi': application})
reactor = deployer.reactor
site = getSite()
reactor.listenTCP(7900, site)

expiry_loop = task.LoopingCall(site.backend.expireAccounts)
expiry_loop.start(site.backend.EXPIRY_CHECK_SEC, now=True).addErrback(log.err)

deployer.run()
