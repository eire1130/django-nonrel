from datetime import datetime, timedelta
import time
import unittest

from django.http import HttpRequest, HttpResponse, parse_cookie
from django.core.handlers.wsgi import WSGIRequest
from django.core.handlers.modpython import ModPythonRequest
from django.utils.http import cookie_date

class RequestsTests(unittest.TestCase):

    def test_httprequest(self):
        self.assertEquals(repr(HttpRequest()),
            "<HttpRequest\n"\
            "GET:{},\n"\
            "POST:{},\n"\
            "COOKIES:{},\n"\
            "META:{}>"
        )

    def test_wsgirequest(self):
        self.assertEquals(repr(WSGIRequest({'PATH_INFO': 'bogus', 'REQUEST_METHOD': 'bogus'})),
            "<WSGIRequest\n"\
            "GET:<QueryDict: {}>,\n"\
            "POST:<QueryDict: {}>,\n"\
            "COOKIES:{},\n"\
            "META:{'PATH_INFO': u'bogus', 'REQUEST_METHOD': 'bogus', 'SCRIPT_NAME': u''}>"
        )

    def test_modpythonrequest(self):
        class FakeModPythonRequest(ModPythonRequest):
           def __init__(self, *args, **kwargs):
               super(FakeModPythonRequest, self).__init__(*args, **kwargs)
               self._get = self._post = self._meta = self._cookies = {}

        class Dummy:
            def get_options(self):
                return {}

        req = Dummy()
        req.uri = 'bogus'
        self.assertEquals(repr(FakeModPythonRequest(req)),
            "<ModPythonRequest\n"\
            "path:bogus,\n"\
            "GET:{},\n"\
            "POST:{},\n"\
            "COOKIES:{},\n"\
            "META:{}>")

    def test_parse_cookie(self):
        self.assertEquals(parse_cookie('invalid:key=true'), {})

    def test_httprequest_location(self):
        request = HttpRequest()
        self.assertEquals(request.build_absolute_uri(location="https://www.example.com/asdf"),
            'https://www.example.com/asdf')

        request.get_host = lambda: 'www.example.com'
        request.path = ''
        self.assertEquals(request.build_absolute_uri(location="/path/with:colons"),
            'http://www.example.com/path/with:colons')

    def test_near_expiration(self):
        "Cookie will expire when an near expiration time is provided"
        response = HttpResponse()
        # There is a timing weakness in this test; The
        # expected result for max-age requires that there be
        # a very slight difference between the evaluated expiration
        # time, and the time evaluated in set_cookie(). If this
        # difference doesn't exist, the cookie time will be
        # 1 second larger. To avoid the problem, put in a quick sleep,
        # which guarantees that there will be a time difference.
        expires = datetime.utcnow() + timedelta(seconds=10)
        time.sleep(0.001)
        response.set_cookie('datetime', expires=expires)
        datetime_cookie = response.cookies['datetime']
        self.assertEquals(datetime_cookie['max-age'], 10)

    def test_far_expiration(self):
        "Cookie will expire when an distant expiration time is provided"
        response = HttpResponse()
        response.set_cookie('datetime', expires=datetime(2028, 1, 1, 4, 5, 6))
        datetime_cookie = response.cookies['datetime']
        self.assertEquals(datetime_cookie['expires'], 'Sat, 01-Jan-2028 04:05:06 GMT')

    def test_max_age_expiration(self):
        "Cookie will expire if max_age is provided"
        response = HttpResponse()
        response.set_cookie('max_age', max_age=10)
        max_age_cookie = response.cookies['max_age']
        self.assertEqual(max_age_cookie['max-age'], 10)
        self.assertEqual(max_age_cookie['expires'], cookie_date(time.time()+10))
