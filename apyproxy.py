import os.path
import re
import unittest

from urllib.parse import urljoin, urlsplit

import requests


def bind(cls, relpath, name):
    def decorator(fn):
        if cls._ApyProxy__bindings is None:
            cls._ApyProxy__bindings = {}
        cls._ApyProxy__bindings[name] = (relpath, fn)
        return fn
    return decorator


def context(proxy, key):
    return proxy._ApyProxy__context.group(key)


class UnboundCallError(Exception):
    pass


class _Pattern:
    def __init__(self, pattern):
        self.pattern = pattern

    def _tr(self):
        return "%s$" % re.sub('\{([^/]*)\}', r'(?P<\1>[^/]*)', self.pattern)

    def match(self, relpath):
        return re.match(self._tr(), relpath)


class ApyProxy:
    __bindings = None

    def __init__(self, url, session=None, force_raise=True):
        self.__url = url
        self.__session = session or requests.Session()
        self.__parent = None
        self.__raise = force_raise

    def __enter__(self):
        self.__session.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__session.__exit__(exc_type, exc_val, exc_tb)

    def __call__(self, *args, **kwargs):
        call = self.__url.rstrip("/").split("/")[-1]
        here = urlsplit(self.__parent._url).path
        if call in self.__bindings:
            pattern, fn = self.__bindings[call]
            match = _Pattern(pattern).match(here)
            if match:
                self.__context = match
                return fn(self, *args, **kwargs)
        raise UnboundCallError(f"'{call}' is not bound to '{here}'")

    def __getattr__(self, name):
        return self._(name)

    def _(self, relpath):
        relpath = str(relpath)
        if relpath.startswith("/"):
            url = urljoin(self.__url, relpath)
        else:
            url = os.path.join(self.__url.rstrip("/"), relpath)
        proxy = ApyProxy(url, self.__session)
        proxy._ApyProxy__parent = self
        return proxy

    @property
    def _url(self):
        url = self.__url
        if hasattr(self.__session, "suffix") and not url.endswith("/"):
            url = f"{url}{self.__session.suffix}"
        return url

    def request(self, method, **kwargs):
        response = self.__session.request(method, self._url, **kwargs)
        if self.__raise:
            response.raise_for_status()
        return response

    def get(self, params=None, **kwargs):
        return self.request("GET", params=params, **kwargs)

    def head(self, **kwargs):
        return self.request("HEAD", **kwargs)

    def patch(self, data=None, **kwargs):
        return self.request("PATCH", data=data, **kwargs)

    def post(self, data=None, json=None, **kwargs):
        return self.request("POST", data=data, json=json, **kwargs)

    def put(self, data=None, **kwargs):
        return self.request("PUT", data=data, **kwargs)

    def __repr__(self):
        return "ApyProxy(%s)" % self._url
