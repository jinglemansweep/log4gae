import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users


from appengine_utilities.cache import Cache
from appengine_utilities.flash import Flash

class BaseRequestHandler(webapp.RequestHandler):

    _OUTPUT_TYPES = {
        "html": "text/html",
        "xml": "text/xml",
        "json": "application/json",
    }
    
    def generate(self, template_name, template_values={}):

        flash = Flash()

        user = users.get_current_user()

        values = {
          "debug": os.getenv("SERVER_SOFTWARE").split("/")[0] == "Development" if os.getenv("SERVER_SOFTWARE") else False,            
          "request": self.request,
          "user": user,
          "login_url": users.create_login_url(self.request.uri),
          "logout_url": users.create_logout_url("http://%s/" % (self.request.host,)),
          "application_name": "Log4GAE",
          "flash": flash,
        }

        values.update(template_values)
        path = os.path.join("templates", template_name)
        output_type = self._OUTPUT_TYPES[template_name.split(".")[-1]]

        self.response.headers["Content-Type"] = output_type
        self.response.out.write(template.render(path, values, debug=values["debug"]))
