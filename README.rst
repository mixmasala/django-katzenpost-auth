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


supported by
============

.. image:: https://katzenpost.mixnetworks.org/_static/images/eu-flag-tiny.jpg

This project has received funding from the European Union’s Horizon 2020
research and innovation programme under the Grant Agreement No 653497, Privacy
and Accountability in Networks via Optimized Randomized Mix-nets (Panoramix).
