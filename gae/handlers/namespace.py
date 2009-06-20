

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required

import dao
from handlers.base import BaseRequestHandler
from forms import NamespaceCreateForm


class NamespaceCreateHandler(BaseRequestHandler):

    @login_required
    def get(self):   

        form = NamespaceCreateForm()
        options = {"form": form}
        self.generate("pages/namespace_create.html", options)

    def post(self):

        form = NamespaceCreateForm(data=self.request.POST)

        if form.is_valid():
            key = dao.createNamespace(form.save(commit=False))
            self.redirect("/namespace/view/%s" % (key))
        else:
            self.generate("pages/namespace_create.html", {"form": form}) 


class NamespaceAuthResetHandler(BaseRequestHandler):

    @login_required
    def get(self, key):   

        dao.resetNamespaceAuthKey(key)            

        self.redirect("/namespace/view/%s" % (key))


class NamespaceListHandler(BaseRequestHandler):

    @login_required
    def get(self):   

        page = self.request.get("page", 0)

        options = dao.listNamespaces(page=page) 

        self.generate("pages/namespace_list.html", options)


class NamespaceViewHandler(BaseRequestHandler):

    @login_required
    def get(self, key):   

        namespace = dao.getNamespace(key)

        owner = (namespace.owner == users.get_current_user())

        options = {"namespace": namespace, "owner": owner}
        self.generate("pages/namespace_view.html", options)
