#!/usr/bin/python

import code
import getpass
import sys

sys.path.append("/home/louis/Data/Apps/google_appengine")
sys.path.append("/home/louis/Data/Apps/google_appengine/lib/yaml/lib")

from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.ext import db

def auth_func():
  return raw_input('Username:'), getpass.getpass('Password:')

app_id = 'log4gae'
host = '%s.appspot.com' % app_id
row_count = 250

remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)

from models import Message
q = Message.all()

while True:
  print 'Deleting %i rows...' % row_count
  e = q.fetch(row_count)
  try:
    db.delete(e)
    print "Done"
  except:
    print "Timed out, retrying"


#code.interact('App Engine interactive console for %s' % (app_id,), None, locals())
