from handlers.base import BaseRequestHandler


class PageHandler(BaseRequestHandler):


    def get(self, page):

        if not page: page = "homepage"
        self.generate("pages/%s.html" % page, {})
