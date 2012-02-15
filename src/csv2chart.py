#!/home/wenli/devel/python/bin/python
# -*- coding: utf-8 -*-
"""File: csv2chart.py
Description:
    Generate a chart from the data provided by a csv file.
History:
    0.1.0 The first version.
"""
__version__ = '0.1.0'
__author__ = 'SpaceLis'

import matplotlib.pyplot as plt
import csv
import sys
import argparse
import fileinput
import textwrap

_COLORSET = ['r-*', 'b-+', 'g-x', 'c-^', 'm-o']

class Color(object):
    """ Define colors
    """
    def __init__(self, colorset=None):
        super(Color, self).__init__()
        if colorset:
            #TODO seems not to work
            self.colorset = colorset
        else:
            self.colorset = _COLORSET
        self._idx = -1

    def next(self):
        self._idx += 1
        return self.colorset[self._idx % len(self.colorset) ]

class LineDrawer(object):
    """ Draw a line according to the vector data
    """
    def __init__(self, color=Color()):
        super(LineDrawer, self).__init__()
        self.color = color

    def draw(self, data, label, xvec = None):
        """ Draw a set of data by drawer
        """
        if not xvec:
            xvec = range(len(data[0]))
        if len(label) > 0:
            for i, vec in enumerate(data):
                plt.plot(xvec, vec, self.color.next(), label=label[i])
        else:
            for i, vec in enumerate(data):
                plt.plot(xvec, vec, self.color.next())

class LogLogDrawer(object):
    """ Draw a line according to the vector data in LogLog scale
    """
    def __init__(self, color=Color()):
        super(LogLogDrawer, self).__init__()
        self.color = color

    def draw(self, data, label, xvec = None):
        """ Draw a set of data by drawer
        """
        if not xvec:
            xvec = range(len(data[0]))
        if len(label) > 0:
            for i, vec in enumerate(data):
                plt.loglog(xvec, vec, self.color.next(), label=label[i])
        else:
            for i, vec in enumerate(data):
                plt.loglog(xvec, vec, self.color.next())

def drawfigure(data, label, headers, drawer, **kargs):
    """ Draw the figure by drawer
    """
    if kargs['discrete']:
        xvec = range(len(headers))
    else:
        xvec = [float(x) for x in headers]
    drawer.draw(data, label, xvec)
    plt.xlabel(kargs['xlabel'])
    plt.ylabel(kargs['ylabel'])
    plt.title(kargs['title'])
    if kargs['xticks']:
        plt.xticks(xvec, headers)
    if kargs['legend'] and len(label)>0:
        plt.legend()
    plt.show()

def transpose(data, label, headers):
    _data = [list() for x in data[0]]
    for vec in data:
        for i in range(len(vec)):
            _data[i].append(vec[i])
    return _data, headers, label

def parse_args():
    """ Parse arguments from commandline
    """
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description= textwrap.dedent('''\
                This is a simple to draw curves from data, which utilizes MATPLOTLIB.
            '''),
            epilog=textwrap.dedent('''\
                Note: The data expected by this tool is in the following format:

                    <Table>\t<Header>\t<Header>\t<Header> ...
                    <Label>\t<datum11>\t<datum12>\t<datum13> ...
                    <Label>\t<datum21>\t<datum22>\t<datum23> ...
                    <Label>\t<datum31>\t<datum32>\t<datum33> ...
                    ...             ...

                Each row of data will finally represent as a curve with its label
                showing in the legend.
            '''))
    parser.add_argument('-T', '--transposed', dest='transposed', action='store_true',
            default=False, help='Transposed the data matrix before draw the curve.')
    parser.add_argument('-L', '--no-labels', dest='haslabel', action='store_false',
            default=True, help='Do not use the first column in the CSV file as labels.')
    parser.add_argument('-H', '--no-headers', dest='hasheader', action='store_false',
            default=True, help='Do not use the first row in the CSV file as headers.')
    parser.add_argument('-D', '--discrete', dest='discrete', action='store_true',
            default=False, help='Prevent header being used as x coordinate')
    parser.add_argument('-k', '--x-ticks', dest='xticks', action='store_true',
            default=False, help='Tick each point with headers in CSV.')
    parser.add_argument('-x', '--x-label', dest='xlabel', action='store',
            default='', metavar='STRING', help='The label for x axis.')
    parser.add_argument('-y', '--y-label', dest='ylabel', action='store',
            default='', metavar='STRING', help='The label for y axis.')
    parser.add_argument('-t', '--title', dest='title', action='store',
            default='', metavar='STRING', help='The title for the figure.')
    parser.add_argument('-P', '--without-legend', dest='legend', action='store_false',
            default=True, help='Do not show a legend.')
    parser.add_argument('-d', '--dilimiter', dest='dilimiter', action='store',
            default='\t', help='The dilimiter for CSV')
    parser.add_argument('-q', '--quotechar', dest='quotechar', action='store',
            default='"', help='The quotechar for CSV')
    parser.add_argument('-s', '--size', dest='size', action='store',
            default='8x6', metavar='WxH', help='The size of figures. Default: 8x6')
    parser.add_argument('-C', '--color', dest='colorset', action='append',
            default=_COLORSET, help='The color patterns used in figure.')
    parser.add_argument('--log', dest='loglog', action='store_true',
            default=False, help='Use Log scale on both x and y axex in figure.')
    parser.add_argument('sources', metavar='file', nargs='+',
            help='The file contains the data. STDIN will be used if none is given.')
    return parser.parse_args()

def main():
    """ main()
    """
    args = parse_args()

    # Configure input
    if len(args.sources) > 0:
        fin = fileinput.input(args.sources, openhook=fileinput.hook_compressed)
    else:
        fin = sys.stdin

    # Read data
    label = list()
    headers = list()
    data = list()
    reader = csv.reader(fin, delimiter=args.dilimiter, quotechar=args.quotechar)
    for row in reader:
        if args.hasheader:
            if args.haslabel:
                headers = row[1:]
            else:
                headers = row
            args.hasheader = False
            continue
        if args.haslabel:
            label.append(row[0])
            data.append([float(num) for num in row[1:]])
        else:
            data.append([float(num) for num in row])
    if args.transposed:
        data, label, headers = transpose(data, label, headers)
    print 'Data:', len(data), 'rows', ',', len(data[0]), 'columns'

    # Prepare for drawing
    if args.loglog:
        drawer = LogLogDrawer(Color(args.colorset))
    else:
        drawer = LineDrawer(Color(args.colorset))
    plt.figure(figsize=[float(s) for s in args.size.split('x')])

    # Draw
    drawfigure(data, label, headers, drawer,
            xlabel=args.xlabel, ylabel=args.ylabel, title=args.title,
            xticks=args.xticks, legend=args.legend, discrete=args.discrete)

if __name__ == '__main__':
    main()

