from ilum.core import Response


def redirect(location="/"):
    response = Response()
    response.headers["Location"] = location
    return response
