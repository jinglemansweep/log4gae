from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from models import Namespace, Message
from forms import NamespaceCreateForm

from handlers.base import *
from handlers.namespace import *
from handlers.message import *
from handlers.page import *

DEFAULT_REDIRECT_URL = "/"
DEBUG = True

url_map = [
    (r"/namespace/list", NamespaceListHandler),
    (r"/namespace/view/(.*)", NamespaceViewHandler),
    (r"/namespace/create", NamespaceCreateHandler),
    (r"/namespace/auth_reset/(.*)", NamespaceAuthResetHandler),
    (r"/message/list", MessageListHandler),
    (r"/message/view/(.*)", MessageViewHandler),
    (r"/rest/message/find/(.*)/(.*)/(.*)/(.*)/(.*)/(.*)", MessageRestFindHandler),
    (r"/rest/message/create", MessageRestCreateHandler),
    (r"/(.*)", PageHandler),
]

def main():

    application = webapp.WSGIApplication(url_map, debug=DEBUG)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()



