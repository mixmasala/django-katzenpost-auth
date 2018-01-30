# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class IDKey(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    key = models.TextField(max_length=500, blank=True)

    def __str__(self):
        if self.key:
            _key = '%s...'  % self.key
        else:
            _key = 'NOKEY'
        return 'Identity for %s (%s)' % (self.user, _key)


class LinkKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    key = models.TextField(max_length=500, blank=True)

    def __str__(self):
        if self.key:
            _key = '%s...'  % self.key
        else:
            _key = 'NOKEY'
        return 'Link key for %s (%s)' % (self.user, _key)


@receiver(post_save, sender=User)
def create_or_update_user_idkey(sender, instance, created, **kwargs):
    if created:
        IDKey.objects.create(user=instance)
        LinkKey.objects.create(user=instance)
    if hasattr(instance, 'idkey'):
        if len(instance.idkey.key) != 0:
            instance.idkey.save()
