
from google.appengine.ext import db
from google.appengine.ext.db import djangoforms

from models import Namespace, Message

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

