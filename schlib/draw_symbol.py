#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import svgwrite
import sys, os
import re
import math

common = os.path.abspath(os.path.join(sys.path[0], '..','common'))

if not common in sys.path:
    sys.path.append(common)

from schlib import *

#enable windows wildcards
from glob import glob

parser = argparse.ArgumentParser(description='Checks KiCad library files (.lib) against KiCad Library Convention (KLC) rules. You can find the KLC at http://kicad-pcb.org/libraries/klc/')
parser.add_argument('libfiles', nargs='+')
parser.add_argument('-c', '--component', help='check only a specific component (implicitly verbose)', action='store')
parser.add_argument('-p', '--pattern', help='Check multiple components by matching a regular expression', action='store')
parser.add_argument('-v', '--verbose', help='Enable verbose output. -v shows brief information, -vv shows complete information', action='count')
parser.add_argument('--png', help='Run rsvg-convert to create a png imediately', action='count')
parser.add_argument('-n', '--name', help='Add component name to svg', action='count')

args = parser.parse_args()

# Set verbosity globally
verbosity = 0
if args.verbose:
    verbosity = args.verbose

#grab list of libfiles (even on windows!)
libfiles = []

for libfile in args.libfiles:
    libfiles += glob(libfile)

(maxx, maxy, minx, miny) = (0, 0, 0, 0)
font = "osifont"

def get_fill_style(polyl):
  fill_opacity = 1
  if polyl['fill'] == 'F':
    fill = "#840000"
  elif polyl['fill'] == 'f':
    fill = "#FFFFC0"
  else:
    fill = "none"
    fill_opacity = 0
  return (fill, fill_opacity)

def get_tickness(polyl):
  thickness = 0
  if thickness in polyl:
    thickness = int(polyl['thickness'])
  if thickness == 0:
    thickness = 8 
  return(thickness)

def get_pin_coords(pin):
  x = int(pin['posx'])
  y = int(pin['posy']) * -1
  l = int(pin['length'])
  start = (x, y)
  mir = 1
  if pin['direction'] == "R":
    stop = (x+l, y)
    mid = (x+l/2, y)
    text_o = (x - 10, y)
    text_a = "end"
    text_rot = "rotate(0)"
    text_orig_name = (x + l + pin_offset, y)
  elif pin['direction'] == "L":
    stop = (x-l, y)
    mid = (x-l/2, y)
    text_o = (x + 10, y)
    text_a = "start"
    text_rot = "rotate(0)"
    text_orig_name = (x - l - pin_offset, y)
  elif pin['direction'] == "D":
    stop = (x+l, y)
    mid = (x+l/2, y)
    text_o = (x + 10, y)
    text_a = "end"
    text_rot = "rotate(90, " + str(x) + ", " + str(y) + ")"
    text_orig_name = (x + l +  pin_offset, y)
  elif pin['direction'] == "U":
    stop = (x+l, y)
    mid = (x+l/2, y)
    text_o = (x - 10, y)
    text_a = "end"
    text_rot = "rotate(270, " + str(x) + ", " + str(y) + ")"
    text_orig_name = (x + l + pin_offset, y)
    mir = -1
  return (start, stop, mid, text_o, text_orig_name, text_a, text_rot, mir)

def get_electrical_type(pin):
  if pin['electrical_type'] == "P":
    return ("Passive")
  elif pin['electrical_type'] == "O":
    return ("Output")
  elif pin['electrical_type'] == "I":
    return ("Input")
  elif pin['electrical_type'] == "W":
    return ("PowerInput")
  return (pin['electrical_type'])
  
def get_points(polyl):
  p = []
  i = iter(polyl['points'])
  try:
    while True:
      x = int(next(i))
      y = int(next(i)) * -1
      p.append((x,y))
  except StopIteration:
    pass 
  return (p)

def update_minmax(start, o = 0):
  global maxx, minx, maxy, miny
  maxx = max(maxx, start[0] + o)
  minx = min(minx, start[0] - o)
  maxy = max(maxy, start[1] + o)
  miny = min(miny, start[1] - o)

for libfile in libfiles:
    lib = SchLib(libfile)

    # Remove .lib from end of name
    lib_name = os.path.basename(libfile)[:-4]

    # Print library name
    if len(libfiles) > 1:
        printer.purple('Library: %s' % libfile)

    for component in lib.components:
        #simple match
        match = True
        if args.component:
            match = match and args.component.lower() == component.name.lower()

        #regular expression match
        if args.pattern:
            match = match and re.search(args.pattern, component.name, flags=re.IGNORECASE)

        if not match: continue

        print ("working on " + lib_name + ":" + component.name)

        # generic settings
        pin_offset = int(component.definition['text_offset'])

        # convert to svg
        dwg = svgwrite.Drawing(filename=component.name + ".svg")
        padding = 250

        for rect in component.draw['rectangles']:
          if int(rect['unit']) > 1:
            continue
          thickness = get_tickness(rect)
          (fill, fill_opacity) = get_fill_style(rect)
          size = (int(rect['endx'])  - int(rect['startx']), int(rect['starty'])  - int(rect['endy']))
          insert = (int(rect['startx']), -1 * int(rect['starty'])) 

          # update min/max to find the bounding box
          update_minmax(insert)

          dwg.add(dwg.rect(insert=insert, size=size, fill_opacity=fill_opacity, fill=fill, stroke="#840000", stroke_width=thickness, stroke_opacity=1, stroke_linejoin="round", stroke_linecap="round"))

        for arc in component.draw['arcs']:
          if int(arc['unit']) > 1:
            continue

          thickness = get_tickness(arc)
          (fill, fill_opacity) = get_fill_style(arc)
          r = math.sqrt((int(arc['posx']) - int(arc['startx']))**2 + (int(arc['posy']) - int(arc['starty']))**2)
          ccw = 1 if int(arc['start_angle']) > int(arc['end_angle']) else 0
          d = "M %d %d A %d %d 0 0 %d %d %d" % (int(arc['startx']), -1 * int(arc['starty']), r, r, ccw, int(arc['endx']), -1*int(arc['endy']))
          center = (int(arc['posx']), -1 * int(arc['posy']))
          update_minmax(center, r)
          dwg.add(dwg.path(d=d, fill_opacity=fill_opacity, fill=fill, stroke="#840000", stroke_width=thickness, stroke_opacity=1, stroke_linejoin="round", stroke_linecap="round"))

        for circ in component.draw['circles']:
          if int(circ['unit']) > 1:
            continue
          thickness = get_tickness(circ)
          (fill, fill_opacity) = get_fill_style(circ)
          radius = circ['radius']
          center = (int(circ['posx']), -1 * int(circ['posy']))
          update_minmax(center, int(radius))
          dwg.add(dwg.circle(center=center, r=radius, fill_opacity=fill_opacity, fill=fill, stroke="#840000", stroke_width=thickness, stroke_opacity=1, stroke_linejoin="round", stroke_linecap="round"))

        for polyl in component.draw['polylines']:
          if int(polyl['unit']) > 1:
            continue
          points = get_points(polyl)
          thickness = get_tickness(polyl)
          (fill, fill_opacity) = get_fill_style(polyl)

          # update min/max to find the bounding box
          for p in points:
            update_minmax(p)

          dwg.add(dwg.polyline(points, fill_opacity=fill_opacity, fill=fill, stroke="#840000", stroke_width=thickness, stroke_opacity=1, stroke_linejoin="round", stroke_linecap="round"))

        for pin in component.draw['pins']:
          if int(pin['unit']) > 1:
            continue
          thickness = get_tickness(pin)
          (start, stop, mid, text_orig_etype, text_orig_name, text_a, rot, mir) = get_pin_coords(pin)
          etype = get_electrical_type(pin)
          fontsize_name = int(pin['name_text_size'])
          fontsize_num = int(pin['num_text_size'])

          # update min/max to find the bounding box
          update_minmax(stop)
          update_minmax(start)

          # add everything to a group so we can rotate if as group
          p = dwg.add(dwg.g(transform=rot))
          p.add(dwg.circle(center=start, r=10, fill="none", stroke="#840000", stroke_width=1, stroke_opacity=1, stroke_linejoin="round", stroke_linecap="round"))
          p.add(dwg.line(start=start, end=stop, stroke="#840000", stroke_width=thickness, stroke_opacity=1, stroke_linejoin="round", stroke_linecap="round"))
          p.add(dwg.text(etype, text_orig_etype, text_anchor=text_a, dominant_baseline="middle", font_size=50, font_family=font, fill="#000084"))
          if component.definition['draw_pinname'] == 'Y':
            if pin_offset == 0:
              tpos = (mid[0], mid[1] - fontsize_num*0.2)
              p.add(dwg.text(pin['name'], tpos, text_anchor="middle", dominant_baseline="middle", font_size=fontsize_name, font_family=font, fill="#008484"))
            else:
              anchor = "end" if text_a == "start" else "start"
              tpos = (text_orig_name[0], text_orig_name[1] + fontsize_name/2)
              p.add(dwg.text(pin['name'], tpos, text_anchor=anchor, font_size=fontsize_name, font_family=font, fill="#008484"))
          if component.definition['draw_pinnumber'] == 'Y':
            tpos = (mid[0], mid[1] + fontsize_num*1) if pin_offset == 0 else (mid[0], mid[1] - fontsize_num*0.2)
            p.add(dwg.text(pin['num'], tpos, text_anchor="middle", dominant_baseline="middle", font_size=fontsize_num, font_family=font, fill="#840000"))

        for t in component.draw['texts']:
          if int(t['unit']) > 1:
            continue
          start = (int(t['posx']), -1 * int(t['posy']) + int(t['text_size'])/2)
          dwg.add(dwg.text(t['text'], start, text_anchor="middle", dominant_baseline="middle", font_size=t['text_size'], font_family=font, fill="#840000"))

	# add name
        if args.name:
          tsize = 50
          dwg.add(dwg.text(lib_name + ":" + component.name, (0, maxy + padding - tsize), text_anchor="middle", dominant_baseline="middle", font_size=tsize, font_weight="bold", font_family=font, fill="#000000"))
          
        #print(component.draw)
        minx -= padding
        miny -= padding
        maxx += padding
        maxy += padding

	# adjust viewport
        dwg.viewbox(minx,miny,maxx - minx,maxy-miny)
        dwg.fit(horiz='center', vert='middle', scale='slice')
        dwg.save()
        if args.png:
         ret = os.system("rsvg-convert " + component.name + ".svg -o " + component.name + ".png")

sys.exit(0);
