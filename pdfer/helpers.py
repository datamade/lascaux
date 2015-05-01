import requests
import os
from urlparse import urlparse
from globalmaptiles import GlobalMercator
from hashlib import md5
from multiprocessing import Pool
mercator = GlobalMercator()

def dl_write(url, base_name):
    path = urlparse(url)
    url_hash = md5(url).hexdigest()
    name = '{url_hash}_{base_name}_{parts}'\
        .format(base_name=base_name, 
                parts='-'.join(path.path.split('/')[-3:]),
                url_hash=unicode(url_hash))
    full_path = os.path.join('/tmp', name)
    try:
        f = open('/tmp/' + name)
    except IOError:
        tile = requests.get(url)
        outp = open('/tmp/' + name, 'wb')
        outp.write(tile.content)
    return name

def dl_write_all(links, base_name):
    # pool = Pool(processes=4)
    # args = [(l, base_name,) for l in links]
    # names = pool.map(dl_write, args)
    # pool.close()
    names = []
    for url in links:
        names.append(dl_write(url, base_name))
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
