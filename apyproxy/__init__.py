# pylint: disable=protected-access
import os.path
import re

from urllib.parse import urljoin, urlsplit

import requests

__all__ = ["bind", "context", "UnboundCallError", "ApyProxy"]

def bind(obj, relpath, name):
    def decorator(func):
        if obj._ApyProxy__bindings is None:
            obj._ApyProxy__bindings = {}
        obj._ApyProxy__bindings[name] = (relpath, func)
        return func
    return decorator


def context(proxy, key):
    return proxy._ApyProxy__context.group(key)


class UnboundCallError(Exception):
    pass


# pylint: disable=too-few-public-methods
class _Pattern:
    def __init__(self, pattern):
        self.pattern = pattern

    def _tr(self):
        return "%s$" % re.sub(r'\{([^/]*)\}', r'(?P<\1>[^/]*)', self.pattern)

    def match(self, relpath):
        return re.match(self._tr(), relpath)


class ApyProxy:
    __bindings = None

    def __init__(self, url, session=None, force_raise=True):
        self.__url = url
        self.__session = session or requests.Session()
        self.__parent = None
        self.__raise = force_raise
        self.__context = None

    def __enter__(self):
        self.__session.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__session.__exit__(exc_type, exc_val, exc_tb)

    # pylint: disable=unsupported-membership-test,unsubscriptable-object
    def __call__(self, *args, **kwargs):
        call = self.__url.rstrip("/").split("/")[-1]
        here = urlsplit(self.__parent._url).path
        if call in self.__bindings:
            pattern, func = self.__bindings[call]
            match = _Pattern(pattern).match(here)
            if match:
                self.__context = match
                return func(self, *args, **kwargs)
        raise UnboundCallError(f"'{call}' is not bound to '{here}'")

    def __getattr__(self, name):
        return self._(name)

    # pylint: disable=invalid-name,attribute-defined-outside-init
    def _(self, relpath):
        relpath = str(relpath)
        if relpath.startswith("/"):
            url = urljoin(self.__url, relpath)
        else:
            url = os.path.join(self.__url.rstrip("/"), relpath)
        proxy = ApyProxy(url, self.__session, self.__raise)
        proxy._ApyProxy__parent = self
        proxy._ApyProxy__bindings = self.__bindings
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

    def __str__(self):
        return self._url
