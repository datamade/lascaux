import os
from datetime import datetime, timedelta
import json
from pdfer.core import pdfer

from flask import Flask, request, make_response

app = Flask(__name__)

app.url_map.strict_slashes = False

# expects GeoJSON object as a string
# client will need to use JSON.stringify() or similar

@app.route('/api/print/', methods=['GET'])
def print_page():
    print_data = {
        'dimensions': request.args.getlist('dimensions'),
        'zoom': request.args['zoom'],
        'center': request.args.getlist('center'),
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
