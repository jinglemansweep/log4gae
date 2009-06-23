import datetime

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required

from django.core.paginator import ObjectPaginator, InvalidPage
from django.utils import simplejson 

import dao
from utils import *
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


class MessageRestHandler(BaseRequestHandler):

    def get(self, method):

        errors = list()
        messages = list()
        params = dict()
        include_list = False

        mandatory_params = ["namespace", "auth_key",]

        if method not in ["find", "count",]:
            errors.append("Invalid method: %s" % (method))

        params["namespace"] = self.request.get("namespace")
        params["auth_key"] = self.request.get("auth_key")
        params["name"] = self.request.get("name")
        params["level"] = self.request.get("level")
        params["minutes"] = self.request.get("minutes", 0)
        params["records"] = self.request.get("records", 1000)

        # Validation

        if method == "find":
            include_list = True
        if method == "count":
            include_list = False

        for mandatory_param in mandatory_params:
            if not params.get(mandatory_param):
                errors.append("Missing parameter: %s" % (mandatory_param))
               
        try:
            params["minutes"] = int(params["minutes"])
        except TypeError:
            errors.append("Invalid parameter value for '%s': %i" % ("minutes", params["minutes"]))

        try:
            params["records"] = int(params["records"])
        except TypeError:
            errors.append("Invalid parameter value for '%s': %i" % ("records", params["records"]))

        if params["level"]:
            params["level"] = params["level"].lower()
            params["level_int"] = level_string_to_number(params["level"])

        cache_key = "message_list_%s_%s_%s_%s_%s" % (params["namespace"], params["name"], params["level"], params["minutes"], params["records"])

        # Query

        earliest_datestamp = datetime.datetime.now() - datetime.timedelta(minutes=int(params["minutes"]))

        if len(errors) == 0:

            # Get Namespace

            cache_namespace = memcache.get("namespace_item_%s" % (params["namespace"]))

            if not cache_namespace:        
                query = db.GqlQuery("SELECT * FROM Namespace WHERE name = :1", params["namespace"])
                namespace = query.get()

            if namespace:
                memcache.set("namespace_item_%s" % (namespace.key()), namespace, (60*60))
                if namespace.auth_key == params["auth_key"]:
                    messages = memcache.get(cache_key)
                    if not messages:
                        query = db.Query(Message)
                        query.filter("namespace =", namespace.key())
                        if params["name"]:
                            query.filter("name =", params["name"])
                        if params["level"]:
                            query.filter("level =", params["level_int"])
                        if params["minutes"] > 0:
                            query.filter("created >=", earliest_datestamp)
                        query.order("-created")               
                        messages = query.fetch(params["records"])
                        memcache.set(cache_key, messages, (60*1))
                else:
                    errors.append("Invalid namespace authentication")
            else:
                errors.append("Namespace not found")

        # Render

        self.generate("rest/message_list.xml", {"include_list": include_list, "messages": messages, "errors": errors}) 


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
            level_int = level_string_to_number(level)
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
