# apyproxy

Python REST client library inspired by xmlrpclib

```
>>> from apyproxy import ApyProxy

>>> httpbin = ApyProxy("http://httpbin.org")
>>> httpbin.anything.get()
<Response [200]>
>>> httpbin.anything.get().url
'http://httpbin.org/anything'

>>> httpbin.anything.special.get(params={"arg": 0})
<Response [200]>
>>> httpbin.anything.special.get(params={"arg": 0}).url
'http://httpbin.org/anything/special?arg=0'

>>> httpbin.status._(201).get()
<Response [201]>

>>> httpbin._("get").get()
<Response [200]>
>>> httpbin._("get").get().url
'http://httpbin.org/get'

>>> httpbin._("/anything/else").get()
<Response [200]>
>>> httpbin._("/anything/else").get().url
'http://httpbin.org/anything/else'

>>> httpbin.status._(404).get()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/gana/src/apyproxy/apyproxy/__init__.py", line 98, in get
    return self.request("GET", params=params, **kwargs)
  File "/home/gana/src/apyproxy/apyproxy/__init__.py", line 94, in request
    response.raise_for_status()
  File "/usr/lib/python3.8/site-packages/requests/models.py", line 940, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: NOT FOUND for url: http://httpbin.org/status/404

>>> anything = httpbin.anything
>>> anything.available.here.get()
<Response [200]>
>>> anything.available.here.get().url
'http://httpbin.org/anything/available/here'
>>>
```
