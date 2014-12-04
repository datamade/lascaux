import os
from datetime import datetime, timedelta
import json
import math
# from pdfer.core import pdfer

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
    page_size = (1275,1650,5,7,)
    print_data = {
        'dimensions': request.args.get('dimensions'),
        'zoom': request.args.get('zoom', 15),
        'center': request.args['center'].split(','),
    }
    if print_data.get('dimensions'):
        print_data['dimensions'] = print_data['dimensions'].split(',')
        short_side, long_side = sorted(print_data['dimensions'])
        tiles_across = math.ceil(float(short_side) / 256.0)
        tiles_up = math.ceil(float(long_side) / 256.0)
        page_size = (int(short_side), int(long_side), int(tiles_across), int(tiles_up),)
    else:
        print_data['dimensions'] = page_size[:2]
    if request.args.get('overlay_tiles'):
        print_data['overlay_tiles'] = request.args['overlay_tiles']
    if request.args.get('base_tiles'):
        print_data['base_tiles'] = request.args['base_tiles']
    path = pdfer(print_data, page_size=page_size)
    resp = make_response(open(path, 'rb').read())
    resp.headers['Content-Type'] = 'application/pdf'
    now = datetime.now().isoformat().split('.')[0]
    resp.headers['Content-Disposition'] = 'attachment; filename=lascaux_%s.pdf' % now
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
