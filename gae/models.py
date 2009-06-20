import random
import string

from google.appengine.ext import db


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
