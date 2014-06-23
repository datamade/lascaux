import os
from datetime import datetime, timedelta
import json
import requests
from urlparse import parse_qs, urlparse
from urllib import unquote
from cStringIO import StringIO
from itertools import groupby
from operator import itemgetter
from pdfer.core import pdfer

from flask import Flask, request, make_response, g, current_app
from functools import update_wrapper
# from raven.contrib.flask import Sentry

app = Flask(__name__)

# app.config['SENTRY_DSN'] = os.environ['CRIME_SENTRY_URL']
# sentry = Sentry(app)

app.url_map.strict_slashes = False

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True): # pragma: no cover
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

# expects GeoJSON object as a string
# client will need to use JSON.stringify() or similar

@app.route('/api/print/', methods=['GET'])
def print_page():
    query = urlparse(request.url).query.replace('query=', '')
    params = json.loads(unquote(query))
    print_data = {
        'dimensions': params['dimensions'],
        'zoom': params['zoom'],
        'center': params['center'],
        'overlays': {
          'shape_overlays': [],
          'point_overlays': [],
        },
    }
    path = pdfer(print_data)
    resp = make_response(open(path, 'rb').read())
    resp.headers['Content-Type'] = 'application/pdf'
    now = datetime.now().isoformat().split('.')[0]
    resp.headers['Content-Disposition'] = 'attachment; filename=Crime_%s.pdf' % now
    return resp

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
