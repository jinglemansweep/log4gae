

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required

from django.core.paginator import ObjectPaginator, InvalidPage

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
            entity = form.save(commit=False)
            entity.owner = users.get_current_user()
            entity.auth_key = entity.generate_auth_key()
            entity.put()
            self.redirect("/namespace/view/%s" % (entity.key()))
        else:
            self.generate("pages/namespace_create.html", {"form": form}) 


class NamespaceAuthResetHandler(BaseRequestHandler):

    @login_required
    def get(self, key):   

        namespace = db.get(key)
        if namespace.owner == users.get_current_user():
            namespace.auth_key = namespace.generate_auth_key()
            namespace.put()
            memcache.set("namespace_item_%s" % (namespace.key()), namespace, (60*60))
            

        self.redirect("/namespace/view/%s" % (namespace.key()))


class NamespaceListHandler(BaseRequestHandler):

    @login_required
    def get(self):   

        namespaces = memcache.get("namespace_list")
        if not namespaces:
            query = db.GqlQuery("SELECT * FROM Namespace WHERE owner = :1", users.get_current_user())
            namespaces = query.fetch(1000)
            memcache.set("namespace_list", namespaces, (60*1))

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


class NamespaceViewHandler(BaseRequestHandler):

    @login_required
    def get(self, key):   

        namespace = memcache.get("namespace_item_%s" % (key))
        if not namespace:
            namespace = db.get(key)
            memcache.set("namespace_item_%s" % (key), namespace, (60*60))
       
        owner = (namespace.owner == users.get_current_user())

        options = {"namespace": namespace, "owner": owner}
        self.generate("pages/namespace_view.html", options)
