from handlers.base import BaseRequestHandler


class PageHandler(BaseRequestHandler):


    def get(self, page):

        if not page: page = "homepage"
        if page not in ["homepage"]:
            page = "404"        

 
        self.generate("pages/%s.html" % page, {})
