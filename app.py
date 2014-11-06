import os
from datetime import datetime, timedelta
import json
import math
from pdfer.core import pdfer

from flask import Flask, request, make_response

app = Flask(__name__)

app.url_map.strict_slashes = False

# expects GeoJSON object as a string
# client will need to use JSON.stringify() or similar

@app.route('/', methods=['GET'])
def print_page():
    dimensions = request.args.getlist('dimensions')
    print_data = {
        'dimensions': dimensions,
        'zoom': request.args['zoom'],
        'center': request.args.getlist('center'),
    }
    if request.args.get('survey'):
        print_data['survey'] = request.args['survey']
        print_data['survey_filter'] = request.args.get('survey_filter')
        print_data['survey_filter_value'] = request.args.get('survey_filter_value')
    short_side, long_side = sorted(dimensions)
    tiles_across = math.ceil(float(short_side) / 256.0)
    tiles_up = math.ceil(float(long_side) / 256.0)
    page_size = (int(short_side), int(long_side), int(tiles_across), int(tiles_up),)
    path = pdfer(print_data, page_size=page_size)
    resp = make_response(open(path, 'rb').read())
    resp.headers['Content-Type'] = 'application/pdf'
    now = datetime.now().isoformat().split('.')[0]
    resp.headers['Content-Disposition'] = 'attachment; filename=lascaux_%s.pdf' % now
    return resp

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
