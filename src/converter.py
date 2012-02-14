#!/home/wenli/devel/python/bin/python
# -*- coding: utf-8 -*-
"""File: labeler.py
Description:
    Manipulate field data.
History:
    0.2.0 + Introducing parametered converter with parameters from console
    0.1.0 The first version.
"""
__version__ = '0.1.0'
__author__ = 'SpaceLis'

from datetime import datetime
import re
import logging
import argparse
from fileset import FileInputSet

import sys
__M__ = sys.modules[__name__]

CONVERTERNAME = re.compile(r'(?P<name>.*Converter)(\[(?P<para>.*)\])?$')

class DiscreteLabelConverter(object):
    """ Use a set of numbers to form a serious bin bounded by numbers.
        E.g. bins = [1, 2, 3, 4], label= = ['<1', '1..2', '2..3', '3..4', '>4']
        The len(labels) should be one more then len(bins). The order is attained
        for dispatching, be sure they are in chronical order.
    """
    def __init__(self, paraline):
        super(DiscreteLabelConverter, self).__init__()
        self._bins, self._labels = [v.split(',') for v in paraline.split('|')]
        self._bins = [float(v) for v in self._bins]
        if not len(self._labels) == len(self._bins) + 1:
            raise ValueError('The len(labels) doesn\'t equals to len(bins)+1')

    def __call__(self, val):
        """ return the label for the token
        """
        # convert the val into the same type
        val = float(val)
        for label, floor in zip(self._labels[:-1], self._bins):
            if val <= floor:
                return label
        return self._labels[-1]

def twittertime(timestr):
    """ Convert string format of timestamp in tweets to datetime objects
    """
    try:
        return datetime.strptime(timestr[4:], '%b %d %H:%M:%S +0000 %Y')
    except ValueError as e:
        logging.error(e)
        exit(1)


def TwitterTimeConverterFactory(fmt, converter=lambda x: x):
    """ Return a labeler according to time format
    """
    return lambda x: converter(x).strftime(fmt)

TT2WeekConverter = TwitterTimeConverterFactory('%Y-%U', twittertime)
TT2PWeekConverter = TwitterTimeConverterFactory('%A', twittertime)
TT2DayConverter = TwitterTimeConverterFactory('%Y-%m-%d', twittertime)
TT2PYearConverter = TwitterTimeConverterFactory('%j', twittertime)
TT2MonthConverter = TwitterTimeConverterFactory('%Y-%m', twittertime)
TT2PMonthConverter = TwitterTimeConverterFactory('%d', twittertime)
TT2PYearMonthConverter = TwitterTimeConverterFactory('%m', twittertime)

class Pipeline(object):
    """ A labelers pipeline for processing labels
    """
    def __init__(self, cv_list):
        super(Pipeline, self).__init__()
        self._cv_list = cv_list
        self._cv_pipeline = list()
        for cvname in cv_list:
            m = CONVERTERNAME.match(cvname)
            if m.group('name').endswith('Converter'):
                if m.group('para'):
                    self._cv_pipeline.append(getattr(__M__, m.group('name'))(m.group('para')))
                    logging.debug('[Converter] %s %s' % (m.group('name'), m.group('para')))
                else:
                    self._cv_pipeline.append(getattr(__M__, m.group('name')))
                    logging.debug('[Converter] %s' % (m.group('name'),))
            else:
                raise ValueError('No labeler named %s found' % (cvname,))

    def __call__(self, item):
        """ Run the item through the pipeline.
        """
        for lb in self._cv_pipeline:
            item = lb(item)
        return item

class FieldProcesser(object):
    """ Preprocess the field data before doing statistics
    """
    def __init__(self):
        super(FieldProcesser, self).__init__()
        self.processer = dict()

    def add_field_converter(self, field, pipeline):
        """ Add a new process to a field
        """
        self.processer[field] = pipeline

    def process(self, row):
        """ Process a line of data
        """
        logging.debug('Processing data')
        for f in self.processer.iterkeys():
            logging.debug('Processing [%s]' % (f,))
            row[f] = self.processer[f](row[f])
        return row

def parse_arg():
    """ Parse the arguments from commandline
    """
    cvnames = ', '.join([cvname for cvname in __M__.__dict__ if cvname.endswith('Converter')])
    parser = argparse.ArgumentParser(description='Simple Text Converter with support to fields.',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='Available Converter:\n' + cvnames)
    parser.add_argument('-f', '--fields', action='append', dest='fields',
            metavar='labeler', default=list(),
            help='Specifying a pipeline should be used on a field.')
    parser.add_argument('-d', '--delimiter', action='store', dest='delimiter',
            default='\t', help='The delimiter of input and output data format.')
    parser.add_argument('--debug', action='store_true', dest='debug', default=False,
            help='Run converter in debug mode.')
    parser.add_argument('sources', metavar='file', nargs='*',
            help='Files as inputs. STDIN will be used, if no input file specified.')
    return parser.parse_args()

def main():
    """ Console command
    """
    args = parse_arg()
    logging.basicConfig(format='%(message)s', level=logging.DEBUG if args.debug else logging.WARNING)
    logging.debug(args)

	# Determine the input of JSON streams
    if len(args.sources) > 0:
        fin = FileInputSet(args.sources)
    else:
        fin = sys.stdin

    fproc = FieldProcesser()
    for p in args.fields:
        field, plname = p.split(':', 1)
        fproc.add_field_converter(int(field), Pipeline(plname.split(':')))

    for line in fin:
        data = line.strip().split(args.delimiter)
        ndata = fproc.process(data)
        print >> sys.stdout, args.delimiter.join(ndata)

def test():
    """docstring for test
    """
    p = Pipeline(['TT2DayConverter',])
    print p('Wed Feb 01 13:22:07 +0000 2012')


if __name__ == '__main__':
    main()
