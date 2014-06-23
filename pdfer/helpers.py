import requests
import os
from urlparse import urlparse
from globalmaptiles import GlobalMercator
mercator = GlobalMercator()

def dl_write(url):
    path = urlparse(url)
    name = path.path.replace('/', '-')
    full_path = os.path.join('/tmp', name)
    try:
        f = open('/tmp/' + name)
    except IOError:
        tile = requests.get(url)
        outp = open('/tmp/' + name, 'wb')
        outp.write(tile.content)
    return name

def dl_write_all(links):
    names = []
    for link in links:
        names.append(dl_write(link))
    return names

def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))

def get_pixel_coords(p, zoom, bmin_rx, bmin_ry):
    mx, my = mercator.LatLonToMeters(float(p[1]), float(p[0]))
    px, py = mercator.MetersToPixels(mx,my,float(zoom))
    rx, ry = mercator.PixelsToRaster(px,py,int(zoom))
    return int(rx - bmin_rx), int(ry - (bmin_ry - 256))
