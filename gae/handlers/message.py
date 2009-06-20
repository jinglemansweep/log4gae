from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required

from django.core.paginator import ObjectPaginator, InvalidPage

from models import Message
from handlers.base import BaseRequestHandler

LEVELS = dict()
LEVELS["debug"] = 10
LEVELS["info"] = 20
LEVELS["warn"] = 30
LEVELS["error"] = 40
LEVELS["fatal"] = 50


class MessageListHandler(BaseRequestHandler):

    @login_required
    def get(self):   

        messages = memcache.get("message_list")
        if not messages:
            query = db.GqlQuery("SELECT * FROM Message WHERE namespace_owner = :1 ORDER BY created DESC", users.get_current_user())
            messages = query.fetch(1000)
            memcache.set("message_list", messages, (30*1))

        paginate_by = 10
        paginator = ObjectPaginator(messages, paginate_by) 

        try:
            page = int(self.request.get("page", 0))
            items = paginator.get_page(page)
        except InvalidPage:
            raise http.Http404     

        options = {
            "items": items,
            "is_paginated": True,
            "results_per_page" : paginate_by,
            "has_next": paginator.has_next_page(page),
            "has_previous": paginator.has_previous_page(page),
            "page": page + 1,
            "next": page + 1,
            "previous": page - 1,
            "pages": paginator.pages,
        }

        self.generate("pages/message_list.html", options)



class MessageRestFindHandler(BaseRequestHandler):


    def get(self, namespace_name, auth_key, name, level, minutes, record_limit):

        try:
            minutes = int(minutes)
            earliest_datestamp = datetime.datetime.now() - datetime.timedelta(minutes=int(minutes))
        except ValueError:
            minutes = "%2A"

        try:
            record_limit = int(record_limit)
        except ValueError:
            record_limit = 100

        if record_limit < 0: record_limit = 100
        if record_limit > 500: record_limit = 500
        
        level = level.lower()

        if level not in ["debug", "info", "warn", "error", "fatal", "*"]:
            level = "%2A"

        cache_key = "message_list_%s_%s_%s_%s_%s" % (namespace_name, name, level, minutes, record_limit)

        errors = []
        messages = []
        
        namespace = memcache.get("namespace_item_%s" % (namespace_name))
        if not namespace:        
            query = db.GqlQuery("SELECT * FROM Namespace WHERE name = :1", namespace_name)
            namespace = query.get()
            memcache.set("namespace_item_%s" % (namespace.key()), namespace, (60*60))

        if namespace:
            if namespace.auth_key == auth_key:
                messages = memcache.get(cache_key)
                if not messages:
                    query = db.Query(Message)
                    query.filter("namespace =", namespace.key())
                    if name != "%2A":
                        query.filter("name =", name)
                    if level != "%2A":
                        query.filter("level =", LEVELS[level])
                    if minutes != "%2A":
                        query.filter("created >=", earliest_datestamp)
                    query.order("-created")
                    messages = query.fetch(record_limit)
                    memcache.set(cache_key, messages, (60*1))
            else:
                errors.append("Namespace: not authorised")
        else:           
            errors.append("Namespace: not found")

        self.generate("rest/message_list.xml", {"messages": messages}) 


class MessageRestCreateHandler(BaseRequestHandler):

    def post(self):

        errors = list()
        post = self.request.POST

        if "namespace" in post:
            namespace_name = post["namespace"].lower()
            query = db.GqlQuery("SELECT * FROM Namespace WHERE name = :1", namespace_name)
            namespace = query.get()
            if not namespace:
                errors.append("Namespace: not found")
            else:
                namespace_owner = namespace.owner
        else:
            errors.append("Namespace: not specified")

        if "name" in post:
            name = post["name"].lower()
            name = name[:100]
        else:
            errors.append("Name: not specified")

        if "level" in post:
            level = post["level"]
            if level not in ["debug", "info", "warn", "error", "fatal"]:
                level = "info"
            level_int = LEVELS[level]
        else:
            errors.append("Level: not specified")

        if "auth_key" in post:
            auth_key = post["auth_key"]
            if namespace:
                if auth_key != namespace.auth_key:
                    errors.append("AuthKey: not authorised")
        else:
            errors.append("AuthKey: not specified")

        if "body" in post:
            body = post["body"]
        else:
            errors.append("Body: not specified")

        success = (len(errors) == 0)
        message_key = None
        
        if success:
            message = Message(namespace=namespace, namespace_owner=namespace_owner, name=name, level=level_int, auth_key=auth_key, body=body)
            message.put()
            message_key = message.key()

        self.generate("rest/message_create.xml", {"success": success, "errors": errors, "key": message_key}) 


class MessageViewHandler(BaseRequestHandler):

    @login_required
    def get(self, key):   

        message = memcache.get("message_item_%s" % (key))
        if not message:
            message = db.get(key)
            memcache.set("message_item_%s" % (key), message, (60*60))

        options = {"message": message}
        self.generate("pages/message_view.html", options)
