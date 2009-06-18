# =[ METADATA ]=================================================================


import datetime
import logging
import os
import random
import string
import sys

from types import IntType, LongType, FloatType
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.db import djangoforms
from django.core.paginator import ObjectPaginator, InvalidPage
from django.utils import simplejson 

from appengine_utilities.cache import Cache
from appengine_utilities.flash import Flash
from appengine_utilities.sessions import Session

session = Session()
cache = Cache()


# =[ CONFIGURATION ]============================================================


_DEBUG = True
_DEFAULT_REDIRECT_URL = "/"


# =[ CONSTANTS ]================================================================

LEVELS = dict()
LEVELS["debug"] = 10
LEVELS["info"] = 20
LEVELS["warn"] = 30
LEVELS["error"] = 40
LEVELS["fatal"] = 50


# =[ FUNCTIONS ]================================================================


def is_number(n):
    return n in (IntType, LongType, FloatType)


# =[ MODELS ]===================================================================


class UserPrefs(db.Model):

    user = db.UserProperty()


class Namespace(db.Model):

    name = db.StringProperty(required=True)
    auth_key = db.StringProperty()
    owner = db.UserProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)    

    def __str__(self):
        return "%s" % (self.name)

    def generate_auth_key(self, size=64):
        return ''.join([random.choice(string.letters + string.digits) for i in range(size)])


class Message(db.Model):

    namespace = db.Reference(Namespace, required=True)
    namespace_owner = db.UserProperty()
    name = db.StringProperty(required=True)
    level = db.IntegerProperty(required=True)
    body = db.TextProperty(required=True)
    auth_key = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)

    def level_string(self):
        if self.level == 10: return "debug"
        if self.level == 20: return "info"
        if self.level == 30: return "warn"
        if self.level == 40: return "error"
        if self.level == 50: return "fatal"
        return "Unknown (%i)" % (self.level)


# =[ FORMS ]====================================================================


class BaseForm(djangoforms.ModelForm):
    pass


class NamespaceCreateForm(BaseForm):
    
    class Meta:
        model = Namespace
        exclude = ["auth_key", "owner", "created", "modified"]


    def clean_name(self):

        name = self.clean_data["name"]
        name = name.lower()
        
        query = db.GqlQuery("SELECT * FROM Namespace WHERE name = :1", name)
        result_count = query.count()

        if result_count >= 1:
            raise djangoforms.forms.ValidationError("Namespace already registered")

        return name



class MessageCreateForm(BaseForm):
    
    class Meta:
        model = Message
        exclude = ["created", "modified"]

    level = djangoforms.forms.ChoiceField(choices=[
        (LEVELS["debug"], "Debug"),
        (LEVELS["info"], "Info"),
        (LEVELS["warn"], "Warn"),
        (LEVELS["error"], "Error"),
        (LEVELS["fatal"], "Fatal"),
    ])

    def clean_auth_key(self):

        namespace = self.clean_data["namespace"]
        auth_key = self.clean_data["auth_key"]
        query = db.GqlQuery("SELECT * FROM Namespace WHERE name = :1 AND auth_key = :2", str(namespace), str(auth_key))
        result_count = query.count()

        if result_count == 0:
            raise djangoforms.forms.ValidationError("Namespace '%s' authorisation failed" % (str(namespace)))        

        return auth_key
        

# =[ REQUEST HANDLERS ] ========================================================


class BaseRequestHandler(webapp.RequestHandler):

    _OUTPUT_TYPES = {
        "html": "text/html",
        "xml": "text/xml",
        "json": "application/json",
    }
    
    def generate(self, template_name, template_values={}):

        flash = Flash()

        user = users.get_current_user()
        prefs = None
        if user:
            q = db.GqlQuery("SELECT * FROM UserPrefs WHERE user = :1", user)
            prefs = q.get()
            if not prefs:
                prefs = UserPrefs(user=user)
                prefs.put()

        values = {
          "debug": os.getenv("SERVER_SOFTWARE").split("/")[0] == "Development" if os.getenv("SERVER_SOFTWARE") else False,            
          "request": self.request,
          "user": user,
          "prefs": prefs,
          "login_url": users.create_login_url(self.request.uri),
          "logout_url": users.create_logout_url("http://%s/" % (self.request.host,)),
          "application_name": "Log4GAE",
          "flash": flash,
        }

        values.update(template_values)
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join("templates", template_name))
        output_type = self._OUTPUT_TYPES[template_name.split(".")[-1]]

        self.response.headers["Content-Type"] = output_type
        self.response.out.write(template.render(path, values, debug=_DEBUG))


class PageHandler(BaseRequestHandler):


    @login_required
    def get(self, page):

        if not page: page = "homepage"
        self.generate("pages/%s.html" % page, {})


class NamespaceListHandler(BaseRequestHandler):

    def get(self):   

        query = db.GqlQuery("SELECT * FROM Namespace WHERE owner = :1", users.get_current_user())
        namespaces = query.fetch(1000)
        paginate_by = 10
        paginator = ObjectPaginator(namespaces, paginate_by) 

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

        self.generate("pages/namespace_list.html", options)


class NamespaceCreateHandler(BaseRequestHandler):

    def get(self):   

        form = NamespaceCreateForm()
        options = {"form": form}
        self.generate("pages/namespace_create.html", options)

    def post(self):

        form = NamespaceCreateForm(data=self.request.POST)

        if form.is_valid():
            entity = form.save(commit=False)
            entity.owner = users.get_current_user()
            entity.auth_key = entity.generate_auth_key()
            entity.put()
            self.redirect("/namespace/view/%s" % (entity.key()))
        else:
            self.generate("pages/namespace_create.html", {"form": form}) 
    

class NamespaceViewHandler(BaseRequestHandler):

    def get(self, key):   

        namespace = db.get(key)
        owner = (namespace.owner == users.get_current_user())

        options = {"namespace": namespace, "owner": owner}
        self.generate("pages/namespace_view.html", options)


class MessageListHandler(BaseRequestHandler):

    def get(self):   

        query = db.GqlQuery("SELECT * FROM Message WHERE namespace_owner = :1 ORDER BY created DESC", users.get_current_user())
        messages = query.fetch(1000)
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


class MessageCreateHandler(BaseRequestHandler):

    def get(self):   

        form = MessageCreateForm()
        options = {"form": form}
        self.generate("pages/message_create.html", options)

    def post(self):

        form = MessageCreateForm(data=self.request.POST)

        if form.is_valid():
            entity = form.save(commit=False)
            entity.namespace_owner = entity.namespace.owner
            entity.put()
            self.redirect("/message/view/%s" % (entity.key()))
        else:
            self.generate("pages/message_create.html", {"form": form}) 


class MessageRestFindHandler(BaseRequestHandler):

    def get(self, namespace, auth_key, name, minutes):

        try:
            minutes = int(minutes)
        except ValueError:
            minutes = 60
        
        logging.info(name)

        earliest_datestamp = datetime.datetime.now() - datetime.timedelta(minutes=int(minutes))

        errors = []
        messages = []
        query = db.GqlQuery("SELECT * FROM Namespace WHERE name = :1", namespace)
        namespace = query.get()

        if namespace:
            if namespace.auth_key == auth_key:
                query = db.Query(Message)
                query.filter("namespace =", namespace.key())
                if name != "%2A":
                    query.filter("name =", name)
                if minutes > 0:
                    query.filter("created >=", earliest_datestamp)
                query.order("-created")
                messages = query.fetch(1000)
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

        if success:
            message = Message(namespace=namespace, namespace_owner=namespace_owner, name=name, level=level_int, auth_key=auth_key, body=body)
            message.put()

        self.generate("rest/message_create.xml", {"success": success, "errors": errors}) 


class MessageViewHandler(BaseRequestHandler):

    def get(self, key):   

        message = db.get(key)

        options = {"message": message}
        self.generate("pages/message_view.html", options)


# =[ URL Mapping ] =============================================================


url_map = [
    (r'/namespace/list', NamespaceListHandler),
    (r'/namespace/view/(.*)', NamespaceViewHandler),
    (r'/namespace/create', NamespaceCreateHandler),
    (r'/message/list', MessageListHandler),
    (r'/message/view/(.*)', MessageViewHandler),
    (r'/message/create', MessageCreateHandler),
    (r'/rest/message/find/(.*)/(.*)/(.*)/(.*)', MessageRestFindHandler),
    (r'/rest/message/create', MessageRestCreateHandler),
    (r'/(.*)', PageHandler),
]


# =[ WSGI Application Definition ]==============================================


def main():

    application = webapp.WSGIApplication(url_map, debug=_DEBUG)
    run_wsgi_app(application)


# =[ Main Call ]================================================================


if __name__ == "__main__":
    main()



