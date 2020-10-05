import requests

from apyproxy import *
from apyproxy import _Pattern


class _PatternTest(unittest.TestCase):
    def test_tr(self):
        pattern = "/this/{pattern}/that/{subs}/do"
        expected = "/this/(?P<pattern>[^/]*)/that/(?P<subs>[^/]*)/do$"
        translated = _Pattern(pattern)._tr()

        self.assertEqual(translated, expected)

    def test_match(self):
        pattern = _Pattern("/this/{pattern}/that")

        self.assertTrue(pattern.match("/this/{pattern}/that"))
        self.assertTrue(pattern.match("/this/is/that"))
        self.assertFalse(pattern.match("/this/is/not/that"))
        self.assertFalse(pattern.match("/other/is/that"))
        self.assertFalse(pattern.match("/other/is/that/"))
        self.assertFalse(pattern.match("/top/this/is/that"))
        self.assertFalse(pattern.match("/this/is/that/tail"))
        self.assertEqual(pattern.match("/this/is/that").group("pattern"), "is")


class ApyProxyTest(unittest.TestCase):
    def test_ApyProxy(self):
        baseurl = "https://httpbin.org"
        url = baseurl
        with ApyProxy(url) as r:
            self.assertEqual(repr(r), "ApyProxy(%s)" % url)

            url = "%s/anything" % url
            r = r.anything
            self.assertEqual(repr(r), "ApyProxy(%s)" % url)

            url = "%s/this" % url
            r = r.this
            self.assertEqual(repr(r), "ApyProxy(%s)" % url)

            url = "%s/get" % baseurl
            r = r._("/get")
            self.assertEqual(repr(r), "ApyProxy(%s)" % url)

            url = "%s/anything/else" % baseurl
            r = r._("/anything/else")
            self.assertEqual(repr(r), "ApyProxy(%s)" % url)

            url = "%s/than/this" % url
            r = r.than.this
            self.assertEqual(repr(r), "ApyProxy(%s)" % url)

        with ApyProxy(baseurl) as r:
            response = r._("get").get()
            self.assertEqual(response.status_code, 200)
            claimed = response.json()
            self.assertEqual(claimed["url"], "%s/get" % baseurl)

            params = {"key": "value"}
            response = r._("get").get(params)
            self.assertEqual(response.status_code, 200)
            claimed = response.json()
            self.assertEqual(claimed["args"], params)

            with self.assertRaises(requests.exceptions.HTTPError):
                r.status._("404").get()

        session = requests.Session()
        session.suffix = ".xml"
        with ApyProxy(baseurl, session) as r:
            response = r.anything.object.get()

            self.assertEqual(response.status_code, 200)
            claimed = response.json()
            self.assertEqual(claimed["url"], "%s/anything/object.xml" % baseurl)

        session = requests.Session()
        session.params = params
        with ApyProxy(baseurl, session) as r:
            response = r.anything.reasonable.get()
            self.assertEqual(response.status_code, 200)
            claimed = response.json()
            self.assertEqual(claimed["args"], params)

            params2 = params.copy()
            params2.update({"this": "that"})
            response = r.anything.unreasonable.get({"this": "that"})
            self.assertEqual(response.status_code, 200)
            claimed = response.json()
            self.assertEqual(claimed["args"], params2)

    def test_bind(self):
        baseurl = "https://httpbin.org"
        api = ApyProxy(baseurl)

        @bind(api, "/anything/{name}/chat", "say_hello")
        def say_hello(chat, msg):
            return "Hello %s, %s" % (context(chat, "name"), msg)

        self.assertEqual(api.anything.jack.chat.say_hello("kuk"), "Hello jack, kuk")
