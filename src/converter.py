#!/home/wenli/devel/python/bin/python
# -*- coding: utf-8 -*-
"""File: labeler.py
Description:
    Manipulate field data.
History:
    0.1.0 The first version.
"""
__version__ = '0.1.0'
__author__ = 'SpaceLis'

from datetime import datetime
import logging
import argparse
import json
from fileset import FileInputSet

import sys
__M__ = sys.modules[__name__]

class DiscreteLabelCoverter(object):
    """ Use a set of numbers to form a serious bin bounded by numbers.
        E.g. bins = [1, 2, 3, 4], label= = ['<1', '1..2', '2..3', '3..4', '>4']
        The len(labels) should be one more then len(bins). The order is attained
        for dispatching, be sure they are in chronical order.
    """
    def __init__(self, bins, labels):
        super(DiscreteLabelCoverter, self).__init__()
        if not len(labels) == len(bins) + 1:
            raise ValueError('The len(labels) doesn\'t equals to len(bins)+1')
        self._bins = bins
        self._labels = labels

    def __call__(self, item):
        """ return the label for the token
        """
        # convert the item into the same type
        item = type(self.bins[0])(item)
        if item <= self._bins[0]:
            return self._labels[0]
        for label, floor in zip(self._labels[1:], self._bins):
            if item <= floor:
                return label

def twittertime(timestr):
    """ Convert string format of timestamp in tweets to datetime objects
    """
    return datetime.strptime(timestr[4:], '%b %d %H:%M:%S +0000 %Y')

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
            if cvname.endswith('Converter'):
                self._cv_pipeline.append(getattr(__M__, cvname))
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
    parser.add_argument('-p', '--pipeline', action='append', dest='pipelines',
            metavar='labeler',
            help='Tokenize the input line before doing statistics, useful for '
            'text.')
    parser.add_argument('-d', '--delimiter', action='store', dest='delimiter',
            default='\t', help='The separator of input data')
    parser.add_argument('-j', '--json', action='store_true', default=False, dest='json',
            help='Use json format as input')
    parser.add_argument('sources', metavar='file', nargs='*',
            help='Files as inputs. STDIN will be used, if no input file specified.')
    return parser.parse_args()

def main():
    """ Console command
    """
    args = parse_arg()
    logging.basicConfig(format='%(message)s', level=logging.INFO)
    logging.debug(args)

	# Determine the input of JSON streams
    if len(args.sources) > 0:
        fin = FileInputSet(args.sources)
    else:
        fin = sys.stdin

    fproc = FieldProcesser()
    if args.json and args.pipelines:
        for p in args.pipelines:
            field, plname = p.split(':', 1)
            fproc.add_field_converter(field, Pipeline(plname.split(':')))
    elif args.pipelines:
        for p in args.pipelines:
            field, plname = p.split(':', 1)
            fproc.add_field_converter(int(field), Pipeline(plname.split(':')))

    if args.json:
        for line in fin:
            jobj = json.loads(line)
            njobj = fproc.process(jobj)
            print >> sys.stdout, njobj.dumps()
    else:
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
