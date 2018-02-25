"""
Modules routing
"""
import os


class Router:
    def __init__(self, module_file):
        self.module_name = os.path.dirname(module_file)
        self.routes = {}

    def route(self, route_regex):
        def route_decorator(fn):
            self.routes[route_regex] = fn
            return fn

        return route_decorator

    @property
    def name(self):
        return self.module_name
