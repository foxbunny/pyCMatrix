#!/usr/bin/env python

import colorsys

from pysvg.structure import svg
from pysvg.style import style
from pysvg.builders import rect


def cconv(i):
    """ Converts integer value into 2-digit hex value """
    if i < 0 and i > 255:
        return '00'
    h = hex(i)[2:] # removes leading `0x`
    return len(h) == 1 and '0%s' % h or h

def scale(i, imin, imax, tmin, tmax):
    """ Scale i from imim-imax system to tmin-tmax system """
    # Find the location of i within imin-imax range
    irange = imax - imin
    iloc = (i - imin) / irange

    # Find the location of i within tmin-tmax range
    trange = tmax - tmin
    tloc = trange * iloc

    # Return the absolute location of i within tmin-tmax range
    return tmin + tloc

def floatrgb(v):
    """ Convert 0-255 value to 0-1.0 floats """
    return v / 255.0

def getcol(i, imin, imax, cmin, cmax):
    """ Calculate the hex color string for value v """
    hmin, smin, vmin = colorsys.rgb_to_hsv(*[floatrgb(v) for v in cmin])
    hmax, smax, vmax = colorsys.rgb_to_hsv(*[floatrgb(v) for v in cmax])
    hval = scale(i, imin, imax, hmin, hmax)
    sval = scale(i, imin, imax, smin, smax)
    vval = scale(i, imin, imax, vmin, vmax)
    rval, gval, bval = colorsys.hsv_to_rgb(hval, sval, vval)
    rhex = cconv(int(rval * 255))
    ghex = cconv(int(gval * 255))
    bhex = cconv(int(bval * 255))
    return '#%s%s%s' % (rhex, ghex, bhex)

def rgbparse(s):
    """ Extract RGB values from config """
    return tuple([int(i.strip()) for i in s.split(',')])

# Read the source data
def load_data(filename='test.csv'):
    f = open(filename, 'r')
    data = f.read()
    f.close()

    # Split into lines
    lines = data.split('\n')
    lines = [line.split(',') for line in lines]

    # Check if last line is empty
    if len(lines[0]) != len(lines[-1:]):
        # Last line is probably a left-over newline
        lines.pop(len(lines) - 1)

    # Determine the matrix length and width
    has_x_labels = lines[0][0] == ''
    matrix_width = has_x_labels and len(lines[0]) - 1 or len(lines[0])
    matrix_height = has_x_labels and len(lines) - 1 or len(lines)
    print "Original data contains %s by %s matrix." % (matrix_width, matrix_height)
    has_y_labels = lines[1][0] != ''

    # Collect labels
    x_labels = has_x_labels and lines[0][1:] or []
    y_labels = has_y_labels and [l[0] for l in lines[1:]] or []
    print "X labels: %s" % x_labels and ', '.join(x_labels) or 'none'
    print "Y labels: %s" % y_labels and ', '.join(y_labels) or 'none'

    # matrix data
    matrix = []
    row_offset = has_x_labels and 1 or 0
    column_offset = has_y_labels and 1 or 0
    for y in column_offset and range(len(lines) - 1) or range(len(lines)):
        row_data = []
        for x in row_offset and range(len(lines[0]) - 1) or range(len(lines[0])):
            # Index offset
            x_real = row_offset + x
            y_real = column_offset + y
            # Coordinates in the graphical grid
            x_coord = x * 10
            y_coord = y * 10
            data_sample = (lines[y_real][x_real], (x_coord, y_coord))
            row_data.append(data_sample)
        matrix.append(row_data)

    return dict(matrix=matrix, xlabels=x_labels, ylabels=y_labels)

def create_graph(matrix, colordict, xlabels, ylabels):
    # Create graphics
    graph = svg('Test graph')

    # Color data
    cstart = colordict['scolor']
    cend = colordict['ecolor']

    # Min max values
    matrixdata = [float(i[0]) for row in matrix for i in row]
    matrixmin = min(matrixdata)
    matrixmax = max(matrixdata)
    print "Working on range from %s to %s" % (matrixmin, matrixmax)

    for row in matrix:
        for sample in row:
            r = rect(x=sample[1][0],
                     y=sample[1][1],
                     width=10,
                     height=10)
            r.set_fill(getcol(float(sample[0]),
                              matrixmin,
                              matrixmax,
                              cstart,
                              cend))
            graph.addElement(r)
    return graph
    
def save_graph(g, ofile):
    g.save(ofile)

def main(parser=None):
    if not parser:
        ifile = 'matrix.csv'
        output = 'matrix.svg'
        colordict = {
            'scolor': (128,102,0),
            'ecolor': (255,204,0),
        }
    else:
        ifile = parser.get('Config', 'data')
        output = parser.get('Config', 'output')
        scolor = rgbparse(parser.get('Config', 'scolor'))
        ecolor = rgbparse(parser.get('Config', 'ecolor'))
        colordict = dict(scolor=scolor, 
                         ecolor=ecolor)

    data = load_data(ifile)
    graph = create_graph(data['matrix'],
                         colordict,
                         data['xlabels'],
                         data['ylabels'])
    save_graph(graph, output)

if __name__ == '__main__':
    import os
    import ConfigParser

    config_file = 'matrix.ini'

    if os.path.exists(config_file):
        # load the .ini file and parse the options
        parser = ConfigParser.RawConfigParser()
        parser.read(config_file)
        main(parser)
    else:
        main()
