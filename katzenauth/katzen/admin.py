# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import IDKey
from .models import LinkKey


class IDKeyInline(admin.StackedInline):
    model = IDKey 
    can_delete = True
    verbose_name_plural = 'ID Keys'
    fk_name = 'user'

class LinkKeyInline(admin.StackedInline):
    model = LinkKey 
    can_delete = True
    verbose_name_plural = 'Link Keys'
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):
    inlines = (IDKeyInline, LinkKeyInline)
    list_display = ('username', 'email', 'is_staff', 'has_idkey', 'has_linkkey')

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

    def has_idkey(self, user):
        return len(user.idkey.key) != 0

    def has_linkkey(self, user):
        return any([lk.key for lk in user.linkkey_set.all()])

    has_idkey.boolean = True
    has_linkkey.boolean = True


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
