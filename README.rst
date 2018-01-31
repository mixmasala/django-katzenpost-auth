django-katzenpost-auth
======================
admin interface for a simple katzenpost provider.

quick start
-----------
a couple of commands are needed on a first run::

  make init
  make migrations
  sudo chown -R user: /opt/katzenauth/
  make collect
  make createadmin

server
------
run hendrix with django and rest api::

  make serve

dev
---

you can destroy the development sqlite db::

  make destroydb

or do everything in one step::

  make startfresh

running hendrix
---------------
http://hendrix.readthedocs.io/en/latest/running-hendrix/
