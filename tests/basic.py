#!/usr/bin/env python

import datetime
import unittest
import urllib
import urllib2

URL="http://localhost:8080"

NAMESPACE = "test"
AUTH_KEY = "apNlkM0Twuipyn21cmdJU8xWYnOIKBgzQnk8shVwV3X4VOHq4ynLOx4pCivOpmQl"
NAME = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
LEVEL = "info"


class TestRestService(unittest.TestCase):

    def setUp(self):
        pass

    def test_create_missing_params_namespace(self):
        url = "%s/rest/message/create" % (URL)
        params = {"auth_key": AUTH_KEY, "name": NAME, "level": LEVEL, "body": "Test"}
        response = self.http(url, params)
        self.assertTrue("not specified" in response)

    def test_create_missing_params_auth_key(self):
        url = "%s/rest/message/create" % (URL)
        params = {"namespace": NAMESPACE, "name": NAME, "level": LEVEL, "body": "Test"}
        response = self.http(url, params)
        self.assertTrue("not specified" in response)

    def test_create_missing_params_name(self):
        url = "%s/rest/message/create" % (URL)
        params = {"namespace": NAMESPACE, "auth_key": AUTH_KEY, "level": LEVEL, "body": "Test"}
        response = self.http(url, params)
        self.assertTrue("not specified" in response)

    def test_create_missing_params_level(self):
        url = "%s/rest/message/create" % (URL)
        params = {"namespace": NAMESPACE, "auth_key": AUTH_KEY, "name": NAME, "body": "Test"}
        response = self.http(url, params)
        self.assertTrue("not specified" in response)

    def test_create_missing_params_body(self):
        url = "%s/rest/message/create" % (URL)
        params = {"namespace": NAMESPACE, "auth_key": AUTH_KEY, "name": NAME, "level": LEVEL}
        response = self.http(url, params)
        self.assertTrue("not specified" in response)

    def test_create_blank_namespace(self):
        url = "%s/rest/message/create" % (URL)
        params = {"namespace": "", "auth_key": AUTH_KEY, "name": NAME, "level": LEVEL, "body": "Test"}
        response = self.http(url, params)
        self.assertTrue("not found" in response)

    def test_create_blank_auth_key(self):
        url = "%s/rest/message/create" % (URL)
        params = {"namespace": NAMESPACE, "auth_key": "", "name": NAME, "level": LEVEL, "body": "Test"}
        response = self.http(url, params)       
        self.assertTrue("not authorised" in response)

    def test_create_invalid_auth_key(self):
        url = "%s/rest/message/create" % (URL)
        params = {"namespace": NAMESPACE, "auth_key": "Th1sIsInval!d2009", "name": NAME, "level": LEVEL, "body": "Test"}
        response = self.http(url, params)       
        self.assertTrue("not authorised" in response)

    def test_create_blank_name(self):
        url = "%s/rest/message/create" % (URL)
        params = {"namespace": NAMESPACE, "auth_key": AUTH_KEY, "name": "", "level": LEVEL, "body": "Test"}
        response = self.http(url, params)       
        self.assertTrue("too short" in response)

    def test_create_blank_level(self):
        url = "%s/rest/message/create" % (URL)
        params = {"namespace": NAMESPACE, "auth_key": AUTH_KEY, "name": NAME, "level": "", "body": "Test"}
        response = self.http(url, params)       
        self.assertTrue("success" in response)

    def test_create_invalid_level(self):
        url = "%s/rest/message/create" % (URL)
        params = {"namespace": NAMESPACE, "auth_key": AUTH_KEY, "name": NAME, "level": "ThisIsInvalid", "body": "Test"}
        response = self.http(url, params)       
        self.assertTrue("success" in response)

    def test_create_blank_body(self):
        url = "%s/rest/message/create" % (URL)
        params = {"namespace": NAMESPACE, "auth_key": AUTH_KEY, "name": NAME, "level": LEVEL, "body": ""}
        response = self.http(url, params)       
        self.assertTrue("too short" in response)

    def test_create_messages_debug(self):
        url = "%s/rest/message/create" % (URL)
        params = {"namespace": NAMESPACE, "auth_key": AUTH_KEY, "name": NAME}

        for i in range(1, 25):
            params["level"] = "debug"
            params["body"] = "Message %i" % (i)
            response = self.http(url, params)
            self.assertTrue("success" in response)

    def test_create_messages_info(self):
        url = "%s/rest/message/create" % (URL)
        params = {"namespace": NAMESPACE, "auth_key": AUTH_KEY, "name": NAME}

        for i in range(1, 25):
            params["level"] = "info"
            params["body"] = "Message %i" % (i)
            response = self.http(url, params)
            self.assertTrue("success" in response)

    def http(self, url, params=None):
        if params:
            params = urllib.urlencode(params)
        request = urllib2.Request(url, params)
        response = urllib2.urlopen(request)
        return response.read()

if __name__ == '__main__':
    unittest.main()

