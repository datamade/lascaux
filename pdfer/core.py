import requests
from globalmaptiles import GlobalMercator
from tilenames import tileXY, tileEdges
from operator import itemgetter
from itertools import groupby
import cv2
import numpy as np
import cairocffi as cairo
import os
from helpers import dl_write_all, hex_to_rgb, get_pixel_coords
from datetime import datetime
from shapely.geometry import box, Polygon, MultiPolygon, Point

mercator = GlobalMercator()

PAGE_SIZES = {
    'letter': (1275,1650,5,7,),
    'tabloid': (2550,3300,10,14,),
}

def generateLinks(pattern, *args):
    zoom, min_tile_x, min_tile_y, max_tile_x, max_tile_y = args
    links = []
    for ty in range(min_tile_y, max_tile_y + 1):
        for tx in range(min_tile_x, max_tile_x + 1):
            links.append(pattern.format(z=zoom, x=tx, y=ty))
    return links

def pdfer(data, page_size=PAGE_SIZES['letter']):
    overlays = data.get('overlays')
    grid = {'zoom': data.get('zoom')}
    center_lon, center_lat = data['center']
    center_tile_x, center_tile_y = tileXY(float(center_lat), float(center_lon), int(data['zoom']))
    dim_across, dim_up = data['dimensions']
    if dim_across > dim_up:
        page_height, page_width, tiles_up, tiles_across = page_size
        orientation = 'landscape'
    else:
        page_width, page_height, tiles_across, tiles_up = page_size
        orientation = 'portrait'
    min_tile_x = center_tile_x - (tiles_across / 2)
    min_tile_y = center_tile_y - (tiles_up / 2)
    max_tile_x = min_tile_x + tiles_across
    max_tile_y = min_tile_y + tiles_up

    # Get base layer tiles
    base_pattern = 'http://a.tiles.mapbox.com/v3/datamade.hnmob3j3/{z}/{x}/{y}.png'
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
    arrays = []
    for k,g in groupby(base_image_names, key=itemgetter(1)):
        images = list(g)
        fnames = ['/tmp/%s' % ('-'.join(f)) for f in images]
        array = []
        for img in fnames:
            i = cv2.cvtColor(cv2.imread(img), cv2.COLOR_RGB2RGBA)
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
                i = cv2.cvtColor(cv2.imread(img, -1), cv2.COLOR_RGB2RGBA)
                array.append(i)
            arrays.append(np.vstack(array))
        outp = np.hstack(arrays)
        cv2.imwrite(overlay_outp_name, outp)
        base = cv2.imread(outp_name, -1)
        overlay = cv2.imread(overlay_outp_name, -1)
        # merged = base + overlay
        for c in range(0,3):
            base[0:0+overlay.shape[0], 0:0+overlay.shape[1], c] = overlay[:,:,c] * (overlay[:,:,3]/255.0) +  base[0:0+overlay.shape[0], 0:0+overlay.shape[1], c] * (1.0 - overlay[:,:,3]/255.0)
        cv2.imwrite(outp_name, base)

    ###########################################################################
    # Code below here is for drawing vector layers within the PDF             #
    # Leaving it in just because it was a pain to come up with the first time #
    ###########################################################################
    
    # for parts in image_names:
    #     parts = parts[3:]
    #     parts[-1] = parts[-1].rstrip('.png')
    #     key = '-'.join(parts[-3:])
    #     grid[key] = {'bbox': tileEdges(float(parts[1]),float(parts[2]),int(parts[0]))}
    # d = {}
    # keys = sorted(grid.keys())
    # if overlays:
    #     polys = []
    #     for k,v in grid.items():
    #         try:
    #             one,two,three,four = grid[k]['bbox']
    #             polys.append(box(two, one, four, three))
    #         except TypeError:
    #             pass
    #     mpoly = MultiPolygon(polys)
    #     bb_poly = box(*mpoly.bounds)
    #     min_key = keys[0]
    #     max_key = keys[-2]
    #     bminx, bminy = grid[min_key]['bbox'][0], grid[min_key]['bbox'][1]
    #     bmaxx, bmaxy = grid[max_key]['bbox'][2], grid[max_key]['bbox'][3]
    #     bmin_mx, bmin_my = mercator.LatLonToMeters(bminx, bminy)
    #     bmax_mx, bmax_my = mercator.LatLonToMeters(bmaxx, bmaxy)
    #     bmin_px, bmin_py = mercator.MetersToPixels(bmin_mx,bmin_my,float(grid['zoom']))
    #     bmax_px, bmax_py = mercator.MetersToPixels(bmax_mx,bmax_my,float(grid['zoom']))
    #     bmin_rx, bmin_ry = mercator.PixelsToRaster(bmin_px,bmin_py,int(grid['zoom']))
    #     im = cairo.ImageSurface.create_from_png(outp_name)
    #     ctx = cairo.Context(im)
    #     if overlays.get('shape_overlay'):
    #         shape_overlay = overlays['shape_overlay']
    #         color = hex_to_rgb('#f06eaa')
    #         coords = shape_overlay['coordinates'][0]
    #         x, y = get_pixel_coords(coords[0], grid['zoom'], bmin_rx, bmin_ry)
    #         ctx.move_to(x,y)
    #         ctx.set_line_width(4.0)
    #         red, green, blue = [float(c) for c in color]
    #         ctx.set_source_rgba(red/255, green/255, blue/255, 0.3)
    #         for p in coords[1:]:
    #             x, y = get_pixel_coords(p, grid['zoom'], bmin_rx, bmin_ry)
    #             ctx.line_to(x,y)
    #         ctx.close_path()
    #         ctx.fill()
    #         ctx.set_source_rgba(red/255, green/255, blue/255, 0.5)
    #         for p in coords[1:]:
    #             x, y = get_pixel_coords(p, grid['zoom'], bmin_rx, bmin_ry)
    #             ctx.line_to(x,y)
    #         ctx.close_path()
    #         ctx.stroke()
    #     ctx.set_line_width(2.0)
    #     for point_overlay in overlays.get('point_overlays'):
    #         color = hex_to_rgb(point_overlay['color'])
    #         for p in point_overlay['points']:
    #             if p[0] and p[1]:
    #                 pt = Point((float(p[0]), float(p[1])))
    #                 if bb_poly.contains(pt):
    #                     nx, ny = get_pixel_coords(p, grid['zoom'], bmin_rx, bmin_ry)
    #                     red, green, blue = [float(c) for c in color]
    #                     ctx.set_source_rgba(red/255, green/255, blue/255, 0.6)
    #                     ctx.arc(nx, ny, 5.0, 0, 50) # args: center-x, center-y, radius, ?, ?
    #                     ctx.fill()
    #                     ctx.arc(nx, ny, 5.0, 0, 50)
    #                     ctx.stroke()
    #     im.write_to_png(outp_name)
    # scale = 1
    pdf_name = outp_name.rstrip('.png') + '.pdf'
    pdf = cairo.PDFSurface(pdf_name, page_width, page_height)
    ctx = cairo.Context(pdf)
    image = cairo.ImageSurface.create_from_png(outp_name)
    ctx.set_source_surface(image, 0, 0)
    ctx.paint()
    pdf.finish()
    print pdf_name
    return pdf_name

