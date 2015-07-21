import requests
import math
import json
from globalmaptiles import GlobalMercator
from tilenames import tileXY, tileEdges, latlon2xy
from operator import itemgetter
from itertools import groupby
import cv2
import numpy as np
import cairocffi as cairo
import os
import random
from helpers import dl_write_all, hex_to_rgb, get_pixel_coords
from datetime import datetime
from shapely.geometry import box, Polygon, MultiPolygon, Point, \
        LineString, MultiPoint


PAGE_SIZES = {
    'letter': (1275,1650,5,7,),
    'tabloid': (2550,3300,10,14,),
}

def generateLinks(pattern, *args):
    zoom, min_tile_x, min_tile_y, max_tile_x, max_tile_y = args
    links = []
    for ty in range(min_tile_y, max_tile_y + 1):
        for tx in range(min_tile_x, max_tile_x + 1):
            
            # handle {s} parameter in tile links for load balancing
            if "{s}" in pattern:
                links.append(pattern.format(s=random.choice(["a", "b", "c"]), 
                                            z=zoom, x=tx, y=ty))
            else:
                links.append(pattern.format(z=zoom, x=tx, y=ty))
    return links

def pdfer(data, page_size=PAGE_SIZES['letter'], output='pdf'):
    
    shape_overlays = data.get('shape_overlays')
    point_overlays = data.get('point_overlays')

    grid = {'zoom': data.get('zoom')}
    center_lon, center_lat = data['center']
    center_tile_x, center_tile_y = tileXY(float(center_lat), 
                                          float(center_lon), 
                                          int(data['zoom']))

    dim_across, dim_up = data['dimensions']
    
    if dim_across > dim_up:
        page_height, page_width, tiles_up, tiles_across = page_size
    else:
        page_width, page_height, tiles_across, tiles_up = page_size
    
    min_tile_x = center_tile_x - (tiles_across / 2)
    min_tile_y = center_tile_y - (tiles_up / 2)
    max_tile_x = min_tile_x + tiles_across
    max_tile_y = min_tile_y + tiles_up

    # Get base layer tiles
    base_pattern = 'http://d.tile.stamen.com/toner/{z}/{x}/{y}.png'
    if data.get('base_tiles'):
        base_pattern = data['base_tiles']

    base_links = generateLinks(base_pattern, 
                               grid['zoom'], 
                               min_tile_x, 
                               min_tile_y, 
                               max_tile_x, 
                               max_tile_y)

    base_names = dl_write_all(base_links, 'base')
    
    # Get overlay tiles
    overlay_pattern = None
    if data.get('overlay_tiles'):
        overlay_pattern = data['overlay_tiles']
        overlay_links = generateLinks(overlay_pattern, 
                                      grid['zoom'], 
                                      min_tile_x, 
                                      min_tile_y, 
                                      max_tile_x, 
                                      max_tile_y)

        overlay_names = dl_write_all(overlay_links, 'overlay')

    now = datetime.now()
    date_string = datetime.strftime(now, '%Y-%m-%d_%H-%M-%S')
    outp_name = os.path.join('/tmp', '{0}.png'.format(date_string))
    base_image_names = ['-'.join(l.split('/')[-3:]) for l in base_names]
    base_image_names = sorted([i.split('-')[-3:] for i in base_image_names], key=itemgetter(1))
    
    for parts in base_image_names:
        z,x,y = parts
        y = y.rstrip('.png').rstrip('.jpg')
        z = z.rsplit('_', 1)[1]
        key = '-'.join([z,x,y])
        grid[key] = {'bbox': tileEdges(float(x),float(y),int(z))}
    
    keys = sorted(grid.keys())
    
    mercator = GlobalMercator()
    bb_poly = None
    
    bmin_rx = None
    bmin_ry = None

    if shape_overlays or point_overlays:
        polys = []
        for k,v in grid.items():
            try:
                one,two,three,four = grid[k]['bbox']
                polys.append(box(two, one, four, three))
            except TypeError:
                pass
        mpoly = MultiPolygon(polys)
        bb_poly = box(*mpoly.bounds)
        min_key = keys[0]
        max_key = keys[-2]
        bminx, bminy = grid[min_key]['bbox'][0], grid[min_key]['bbox'][1]
        bmaxx, bmaxy = grid[max_key]['bbox'][2], grid[max_key]['bbox'][3]
        bmin_mx, bmin_my = mercator.LatLonToMeters(bminx, bminy)
        bmax_mx, bmax_my = mercator.LatLonToMeters(bmaxx, bmaxy)
        bmin_px, bmin_py = mercator.MetersToPixels(bmin_mx,bmin_my,float(grid['zoom']))
        bmax_px, bmax_py = mercator.MetersToPixels(bmax_mx,bmax_my,float(grid['zoom']))
        bmin_rx, bmin_ry = mercator.PixelsToRaster(bmin_px,bmin_py,int(grid['zoom']))
        
        if shape_overlays:
            all_polys = []
            for shape_overlay in shape_overlays:
                shape_overlay = json.loads(shape_overlay)
                if shape_overlay.get('geometry'):
                    shape_overlay = shape_overlay['geometry']
                coords = shape_overlay['coordinates'][0]
                all_polys.append(Polygon(coords))
            mpoly = MultiPolygon(all_polys)
            
            one, two, three, four, five = list(box(*mpoly.bounds).exterior.coords)
            
            left, right = LineString([one, two]), LineString([three, four])
            top, bottom = LineString([two, three]), LineString([four, five])

            left_to_right = left.distance(right)
            top_to_bottom = top.distance(bottom)

            if left_to_right > top_to_bottom:
                page_height, page_width, _, _ = page_size
            else:
                page_width, page_height, _, _ = page_size

            center_lon, center_lat = list(mpoly.centroid.coords)[0]


        if point_overlays:
            all_points = []
            
            for point_overlay in point_overlays:
                point_overlay = json.loads(point_overlay)
                for p in point_overlay['points']:
                    if p[0] and p[1]:
                        all_points.append(p)
            
            mpoint = MultiPoint(all_points)
            center_lon, center_lat = list(mpoint.centroid.coords)[0]
            
            one, two, three, four, five = list(box(*mpoint.bounds).exterior.coords)
            
            left, right = LineString([one, two]), LineString([three, four])
            top, bottom = LineString([two, three]), LineString([four, five])

            left_to_right = left.distance(right)
            top_to_bottom = top.distance(bottom)

            if left_to_right > top_to_bottom:
                page_height, page_width, _, _ = page_size
            else:
                page_width, page_height, _, _ = page_size
            
            center_lon, center_lat = list(mpoint.centroid.coords)[0]

            print(center_lon, center_lat)
        
    arrays = []
    for k,g in groupby(base_image_names, key=itemgetter(1)):
        images = list(g)
        fnames = ['/tmp/%s' % ('-'.join(f)) for f in images]
        array = []
        for img in fnames:
            i = cv2.imread(img, -1)
            if isinstance(i, type(None)):
                i = np.zeros((256,256,4), np.uint8)
            elif i.shape[2] != 4:
                i = cv2.cvtColor(cv2.imread(img), cv2.COLOR_BGR2BGRA)
            array.append(i)
        arrays.append(np.vstack(array))
    outp = np.hstack(arrays)
    cv2.imwrite(outp_name, outp)
    if overlay_pattern:
        overlay_outp_name = os.path.join('/tmp', 'overlay_{0}.png'.format(date_string))
        overlay_image_names = ['-'.join(l.split('/')[-3:]) for l in overlay_names]
        overlay_image_names = sorted([i.split('-')[-3:] for i in overlay_image_names], key=itemgetter(1))
        arrays = []
        for k,g in groupby(overlay_image_names, key=itemgetter(1)):
            images = list(g)
            fnames = ['/tmp/%s' % ('-'.join(f)) for f in images]
            array = []
            for img in fnames:
                i = cv2.imread(img, -1)
                if isinstance(i, type(None)):
                    i = np.zeros((256,256,4), np.uint8)
                elif i.shape[2] != 4:
                    i = cv2.cvtColor(cv2.imread(img), cv2.COLOR_BGR2BGRA)
                array.append(i)
            arrays.append(np.vstack(array))
            nuked = [os.remove(f) for f in fnames]
        outp = np.hstack(arrays)
        cv2.imwrite(overlay_outp_name, outp)
        base = cv2.imread(outp_name, -1)
        overlay = cv2.imread(overlay_outp_name, -1)
        overlay_g = cv2.cvtColor(overlay, cv2.COLOR_BGR2GRAY)
        ret, mask = cv2.threshold(overlay_g, 10, 255, cv2.THRESH_BINARY)
        inverted = cv2.bitwise_not(mask)
        overlay = cv2.bitwise_not(overlay, overlay, mask=inverted)

        base_alpha = 0.55
        overlay_alpha = 1
 
        for channel in range(3):
            x,y,d = overlay.shape
            base[:,:,channel] = (base[:,:,channel] * base_alpha + \
                                     overlay[:,:,channel] * overlay_alpha * \
                                     (1 - base_alpha)) / \
                                     (base_alpha + overlay_alpha * (1 - base_alpha))
        
        cv2.imwrite(outp_name, base)

    ###########################################################################
    # Code below here is for drawing vector layers within the PDF             #
    # Leaving it in just because it was a pain to come up with the first time #
    ###########################################################################
    
    if shape_overlays or point_overlays:
        
        im = cairo.ImageSurface.create_from_png(outp_name)
        ctx = cairo.Context(im)

        if shape_overlays:
            for shape_overlay in shape_overlays:
                shape_overlay = json.loads(shape_overlay)
                if shape_overlay.get('geometry'):
                    shape_overlay = shape_overlay['geometry']
                color = hex_to_rgb('#f06eaa')
                coords = shape_overlay['coordinates'][0]
                x, y = get_pixel_coords(coords[0], grid['zoom'], bmin_rx, bmin_ry)
                ctx.move_to(x,y)
                ctx.set_line_width(4.0)
                red, green, blue = [float(c) for c in color]
                ctx.set_source_rgba(red/255, green/255, blue/255, 0.3)
                for p in coords[1:]:
                    x, y = get_pixel_coords(p, grid['zoom'], bmin_rx, bmin_ry)
                    ctx.line_to(x,y)
                ctx.close_path()
                ctx.fill()
                ctx.set_source_rgba(red/255, green/255, blue/255, 0.5)
                for p in coords[1:]:
                    x, y = get_pixel_coords(p, grid['zoom'], bmin_rx, bmin_ry)
                    ctx.line_to(x,y)
                ctx.close_path()
                ctx.stroke()
        ctx.set_line_width(2.0)

        if point_overlays:
            for point_overlay in point_overlays:
                point_overlay = json.loads(point_overlay)
                color = hex_to_rgb(point_overlay['color'])
                for p in point_overlay['points']:
                    if p[0] and p[1]:
                        pt = Point((float(p[0]), float(p[1])))
                        if bb_poly.contains(pt):
                            nx, ny = get_pixel_coords(p, grid['zoom'], bmin_rx, bmin_ry)
                            red, green, blue = [float(c) for c in color]
                            ctx.set_source_rgba(red/255, green/255, blue/255, 0.6)
                            ctx.arc(nx, ny, 5.0, 0, 50) # args: center-x, center-y, radius, ?, ?
                            ctx.fill()
                            ctx.arc(nx, ny, 5.0, 0, 50)
                            ctx.stroke()
        im.write_to_png(outp_name)
    scale = 1
    
    # Crop image from center

    center_point_x, center_point_y = latlon2xy(float(center_lat), 
                                               float(center_lon), 
                                               float(data['zoom']))

    offset_x = (center_point_x - float(center_tile_x)) + 50
    offset_y = (center_point_y - float(center_tile_y)) - 50

    outp_image = cv2.imread(outp_name, -1)
    pixels_up, pixels_across, channels = outp_image.shape
    center_x, center_y = (pixels_across / 2) + offset_x, (pixels_up / 2) + offset_y
    start_y, end_y = center_y - (page_height / 2), center_y + (page_height / 2)
    start_x, end_x = center_x - (page_width / 2), center_x + (page_width / 2)

    cv2.imwrite(outp_name, outp_image[start_y:end_y, start_x:end_x])

    if output == 'pdf':
        outp_file_name = outp_name.rstrip('.png') + '.pdf'

        pdf = cairo.PDFSurface(outp_file_name, page_width, page_height)
        ctx = cairo.Context(pdf)
        image = cairo.ImageSurface.create_from_png(outp_name)
        ctx.set_source_surface(image)
        ctx.paint()
        pdf.finish()
    elif output == 'jpeg':
        outp_file_name = outp_name.rstrip('.png') + '.jpg'
        jpeg = cv2.cvtColor(cv2.imread(outp_name, -1), cv2.COLOR_RGBA2RGB)
        cv2.imwrite(outp_file_name, jpeg)
    return outp_file_name

