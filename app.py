import os
from datetime import datetime, timedelta
import json
import math
from pdfer.core import pdfer

from flask import Flask, request, make_response, render_template
from raven.contrib.flask import Sentry
from app_config import SENTRY_DSN


app = Flask(__name__)

app.url_map.strict_slashes = False

sentry = Sentry(app, dsn=SENTRY_DSN)

# expects GeoJSON object as a string
# client will need to use JSON.stringify() or similar

@app.route('/', methods=['GET'])
def index():
    return render_app_template('index.html')

@app.route('/api', methods=['POST', 'GET'])
def print_page():
    if request.method == 'GET':
        data = request.args.copy()
    else: 
        data = request.form.copy()
    zoom = data.get('zoom')
    center = data.get('center')
    if not center:
        r = {
            'status': 'error',
            'message': "Please provide parameters for 'base_tiles', 'dimensions', 'zoom' and 'center'."
        }
        resp = make_response(json.dumps(r), 400)
        resp.headers['content-type'] = 'application/json'
        return resp
    page_size = (8.5,11,5,7,)
    print_data = {
        'dimensions': data.get('dimensions'),
        'zoom': data.get('zoom', 15),
        'center': data['center'].split(','),
        'shape_overlays': data.getlist('shape_overlays'),
        'point_overlays': data.getlist('point_overlays'),
        'beat_overlays': data.getlist('beat_overlays'),
    }
    
    units = data.get('units', 'inches')
    output_format = data.get('output_format', 'pdf')
    if print_data.get('dimensions'):
        if units == 'inches':
            dimensions = [(float(d) * 150) \
                    for d in print_data['dimensions'].split(',')]
        elif units == 'pixels':
            dimensions = [float(d) for d in print_data['dimensions'].split(',')]
        elif units == 'cms':
            dimensions = [(float(d) * 0.393701) * 150 \
                    for d in print_data['dimensions'].split(',')]
        print_data['dimensions'] = dimensions
        short_side, long_side = sorted(dimensions)
        tiles_across = math.ceil(short_side / 256.0)
        tiles_up = math.ceil(long_side / 256.0)
        page_size = (int(short_side), int(long_side), int(tiles_across), int(tiles_up),)
    else:
        print_data['dimensions'] = page_size[:2]
    if data.get('overlay_tiles'):
        print_data['overlay_tiles'] = data['overlay_tiles']
    if data.get('base_tiles'):
        print_data['base_tiles'] = data['base_tiles']
    path = pdfer(print_data, page_size=page_size, output=output_format)
    resp = make_response(open(path, 'rb').read())
    resp.headers['Content-Type'] = 'application/pdf'
    now = datetime.now().isoformat().split('.')[0]
    resp.headers['Content-Disposition'] = \
            'attachment; filename=lascaux_{0}.{1}'.format(now, output_format)
    return resp

# UTILITY
def render_app_template(template, **kwargs):
    '''Add some goodies to all templates.'''
    if 'config' not in kwargs:
        kwargs['config'] = app.config
    return render_template(template, **kwargs)

# INIT
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)
