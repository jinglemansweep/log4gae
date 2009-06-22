import datetime

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required

from django.core.paginator import ObjectPaginator, InvalidPage
from django.utils import simplejson 

import dao
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

        page = self.request.get("page", 0)
        page = int(page)

        options = dao.listMessages(page=page) 

        self.generate("pages/message_list.html", options)


class MessageAjaxLatestHandler(BaseRequestHandler):
    
    @login_required
    def get(self):

        latest = memcache.get("message_latest_%s" % (users.get_current_user()))

        output = simplejson.dumps(latest)

        options = {"output": output}
        self.generate("ajax/message.json", options)


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

        if namespace:
            memcache.set("namespace_item_%s" % (namespace.key()), namespace, (60*60))
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
            if "auth_key" in post:
                auth_key = post["auth_key"]
                if namespace:
                    if auth_key != namespace.auth_key:
                        errors.append("AuthKey: not authorised")
            else:
                errors.append("AuthKey: not specified")
        else:
            errors.append("Namespace: not specified")

        if "name" in post:
            name = str(post["name"].lower())
            name = name[:100]
            if len(name) < 4:
                errors.append("Name: too short")
        else:
            errors.append("Name: not specified")

        if "level" in post:
            level = post["level"]
            if level not in ["debug", "info", "warn", "error", "fatal"]:
                level = "info"
            level_int = LEVELS[level]
        else:
            errors.append("Level: not specified")

        if "body" in post:
            body = str(post["body"])
            if len(body) < 1:
                errors.append("Body: too short")
        else:
            errors.append("Body: not specified")

        success = (len(errors) == 0)
        message_key = None
        
        if success:
            message = Message(namespace=namespace, namespace_owner=namespace_owner, name=name, level=level_int, auth_key=auth_key, body=body)
            message.put()
            message_key = str(message.key())
            memcache.set("message_latest_%s" % (namespace_owner), {"key": message_key, "namespace": namespace.name, "name": message.name, "level": message.level_string().upper(), "body": message.body, "created": message.created.strftime("%Y-%m-%d %H:%M:%S")})

        self.generate("rest/message_create.xml", {"success": success, "errors": errors, "key": message_key}) 


class MessageViewHandler(BaseRequestHandler):

    @login_required
    def get(self, key):   

        message = dao.getMessage(key)

        owner = (message.namespace_owner == users.get_current_user())

        options = {"message": message, "owner": owner}
        self.generate("pages/message_view.html", options)
