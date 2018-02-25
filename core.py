import os
import sys
import re
import traceback
from urllib.parse import parse_qs
from html import escape
from .errors import *
from .utils.router import Router


class Request(object):
    def __init__(self, environ):
        self.environ = environ
        self.path = environ["PATH_INFO"]
        self.method = environ['REQUEST_METHOD']
        self.headers = {k: v for k, v in environ.items() if k.startswith("HTTP_")}
        self.params = None
        self.GET = parse_qs(environ["QUERY_STRING"])
        self.POST = {}

        if self.method == "POST":
            try:
                content_length = int(environ.get("CONTENT_LENGTH", 0))
            except ValueError:
                content_length = 0

            query_string = environ["wsgi.input"].read(content_length).decode('utf-8')
            self.POST = parse_qs(query_string)


class StreamingResponse(object):
    def __init__(self, stream, request, content_type, content_disposition, content_length, status="200 OK"):
        self.status = status

        if 'wsgi.file_wrapper' in request.environ:
            self.body = request.environ['wsgi.file_wrapper'](stream, 1024)
        else:
            self.body = iter(lambda: stream.read(1024), '')

        self.headers = {
            "Content-Type": content_type,
            "Content-Length": content_length,
            "Content-Disposition": content_disposition,

        }

    @property
    def wsgi_headers(self):
        return [(k, v) for k, v in self.headers.items()]

    @property
    def return_value(self):
        return self.body


class Response(object):
    def __init__(self, status="200 OK", body="", content_type="text/html"):
        self.status = status
        self.body = str(body)
        self.headers = {
            "Content-Type": content_type,
            "Content-Length": str(len(self.body.encode('utf-8')))
        }

    @property
    def wsgi_headers(self):
        return [(k, v) for k, v in self.headers.items()]

    @property
    def return_value(self):
        return [self.body.encode('utf-8')]


class Redirect(object):
    def __init__(self, location="/"):
        self.status = "302 Found"
        self.headers = {
            "Location": location
        }

    @property
    def wsgi_headers(self):
        return [(k, v) for k, v in self.headers.items()]

    @property
    def return_value(self):
        return ["\n".encode('utf-8')]


class Ilum(object):
    def __init__(self, path):
        self.root = os.path.abspath(os.path.dirname(path))
        self.routes = {}

    def __call__(self, environ, start_response):
        response = self.dispatch(Request(environ))
        start_response(response.status, response.wsgi_headers)
        return response.return_value

    @staticmethod
    def not_found():
        return Response(
            status="404 Not Found",
            body="Page not found."
        )

    @staticmethod
    def internal_error():
        return Response(
            status="500 Internal Server Error",
            body="An error has occurred."
        )

    def route(self, route_regex):
        def route_decorator(fn):
            self.routes[route_regex] = fn
            return fn

        return route_decorator

    def dispatch(self, request):
        for regex, view_func in self.routes.items():
            match = re.search(regex, request.path)
            if match is not None:
                request.params = match.groupdict()

                try:
                    return view_func(request, **request.params)
                except Exception:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    traceback.print_tb(exc_traceback)
                    return self.internal_error()

        return self.not_found()

    def register_module(self, module):
        if not isinstance(module, Router):
            raise UnknownModule("Module {0} must be an instance of <ilum.utils.router.Router> class".format(
                module.name
            ))

        self.routes.update(module.routes)
