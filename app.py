import os
from datetime import datetime, timedelta
import json
import math
from pdfer.core import pdfer

from flask import Flask, request, make_response, render_template

app = Flask(__name__)

app.url_map.strict_slashes = False

# expects GeoJSON object as a string
# client will need to use JSON.stringify() or similar

@app.route('/', methods=['GET'])
def index():
    return render_app_template('index.html')

@app.route('/api', methods=['GET'])
def print_page():
    zoom = request.args.get('zoom')
    center = request.args.get('center')
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
        'dimensions': request.args.get('dimensions'),
        'zoom': request.args.get('zoom', 15),
        'center': request.args['center'].split(','),
    }
    units = request.args.get('units', 'inches')
    output_format = request.args.get('output_format', 'pdf')
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
    if request.args.get('overlay_tiles'):
        print_data['overlay_tiles'] = request.args['overlay_tiles']
    if request.args.get('base_tiles'):
        print_data['base_tiles'] = request.args['base_tiles']
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
