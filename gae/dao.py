from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users

from django.core.paginator import ObjectPaginator, InvalidPage

from models import Namespace, Message


def getNamespace(key):

    namespace = cacheGet(key, 3600)

    return namespace


def listNamespaces(page=0, page_size=10):

    namespaces = memcache.get("namespace_list")
    if not namespaces:
        query = db.GqlQuery("SELECT * FROM Namespace WHERE owner = :1", users.get_current_user())
        namespaces = query.fetch((page_size * 10))
        memcache.set("namespace_list", namespaces, (60*1))

    paginator = ObjectPaginator(namespaces, page_size) 

    try:
        items = paginator.get_page(page)
    except InvalidPage:
        raise http.Http404     

    options = {
        "items": items,
        "is_paginated": True,
        "results_per_page" : page_size,
        "has_next": paginator.has_next_page(page),
        "has_previous": paginator.has_previous_page(page),
        "page": page + 1,
        "next": page + 1,
        "previous": page - 1,
        "pages": paginator.pages,
    }

    return options


def createNamespace(namespace):

    namespace.owner = users.get_current_user()
    namespace.auth_key = namespace.generate_auth_key()
    namespace.put()

    memcache.set("item_%s" % (namespace.key()), namespace, (60*60))

    return namespace.key()    


def resetNamespaceAuthKey(key):

    namespace = db.get(key)

    if namespace.owner == users.get_current_user():

        namespace.auth_key = namespace.generate_auth_key()
        namespace.put()

        memcache.set("item_%s" % (namespace.key()), namespace, (60*60))


def getMessage(key):

    message = cacheGet(key, 3600)

    return message


def listMessages(page=0, page_size=10):

    messages = memcache.get("message_list_%s" % (users.get_current_user()))
    if not messages:
        query = db.GqlQuery("SELECT * FROM Message WHERE namespace_owner = :1 ORDER BY created DESC", users.get_current_user())
        messages = query.fetch((page_size * 10))
        memcache.set("message_list_%s" % (users.get_current_user()), messages, (60*1))

    paginator = ObjectPaginator(messages, page_size) 

    try:
        items = paginator.get_page(page)
    except InvalidPage:
        raise http.Http404     

    options = {
        "items": items,
        "is_paginated": True,
        "results_per_page" : page_size,
        "has_next": paginator.has_next_page(page),
        "has_previous": paginator.has_previous_page(page),
        "page": page + 1,
        "next": page + 1,
        "previous": page - 1,
        "pages": paginator.pages,
    }

    return options


def cacheGet(key, duration=300):

    object = memcache.get("item_%s" % (key))

    if not object:
        object = db.get(key)
        memcache.set("item_%s" % (key), object, duration)

    return object
    
    
