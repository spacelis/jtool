#!/home/wenli/devel/python/bin/python
# -*- coding: utf-8 -*-
"""File: stats.py
Description:
    Get statistics from input.
History:
    0.1.1 + Sorting option for outputs.
    0.1.0 The first version.
"""
__version__ = '0.1.1'
__author__ = 'SpaceLis'

import argparse
import re
import fileinput
import sys
import logging
from datetime import datetime

_SPACES = re.compile(r'\s+')
__M__ = sys.modules[__name__]

def SpaceTokenizer():
    return _SPACES.split

#TODO integrate this class into parameters
class BinLabelerFactory(object):
    """ Use a set of numbers to form a serious bin bounded by numbers.
        E.g. bins = [1, 2, 3, 4], label= = ['<1', '1..2', '2..3', '3..4', '>4']
        The len(labels) should be one more then len(bins). The order is attained
        for dispatching, be sure they are in chronical order.
    """
    def __init__(self, bins, labels, converter=lambda x: x):
        super(BinLabelerFactory, self).__init__()
        if not len(labels) == len(bins) + 1:
            raise ValueError('The len(labels) doesn\'t equals to len(bins)+1')
        self._bins = bins
        self._labels = labels
        self._converter = converter

    def __call__(self, item):
        """ return the label for the token
        """
        item = self._converter(item)
        if item <= self._bins[0]:
            return self._labels[0]
        for label, floor in zip(self._labels[1:], self._bins):
            if item <= floor:
                return label

def twittertime(timestr):
    """ Convert string format of timestamp in tweets to datetime objects
    """
    return datetime.strptime(timestr[4:], '%b %d %H:%M:%S +0000 %Y')

def TimeLabelerFactory(fmt, converter=lambda x: x):
    """ Return a labeler according to time format
    """
    return lambda x: converter(x).strftime(fmt)

WeekLabeler = TimeLabelerFactory('%Y-%U', twittertime)
PWeekLabeler = TimeLabelerFactory('%A', twittertime)
DayLabeler = TimeLabelerFactory('%Y-%m-%d', twittertime)
PYearLabeler = TimeLabelerFactory('%j', twittertime)
MonthLabeler = TimeLabelerFactory('%Y-%m', twittertime)
PMonthLabeler = TimeLabelerFactory('%d', twittertime)
PYearMonthLabeler = TimeLabelerFactory('%m', twittertime)


def parse_parameter():
    """ Parse parameters from console
    """
    lbs = ', '.join([lb for lb in __M__.__dict__ if lb.endswith('Labeler')])

    parser = argparse.ArgumentParser(description='Simple distribution calculator',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='Available Labelers:\n' + lbs)
    parser.add_argument('-t', '--tokenizer', action='store', dest='tokenizer',
            help='Tokenize the input line before doing statistics, useful for '
            'text.')
    parser.add_argument('-p', '--pipeline', action='append', dest='pipeline',
            metavar='labeler',
            help='Tokenize the input line before doing statistics, useful for '
            'text.')
    parser.add_argument('-d', '--delimiter', action='store', default=' ', dest='delimiter',
            help='The delimiter used in output file to separate the token and '
            'frequency.')
    parser.add_argument('-s', '--sort-freq', action='store_true', default=False, dest='sortf',
            help='Output the statistics with sorting on frequency.')
    parser.add_argument('-S', '--sort-key', action='store_true', default=False, dest='sortk',
            help='Output the statistics with sorting on key.')
    parser.add_argument('sources', metavar='file', nargs='*',
            help='Files as inputs. STDIN will be used, if no input file specified.')
    return parser.parse_args()



class Pipeline(object):
    """ A labelers pipeline for processing labels
    """
    def __init__(self, lbnames):
        super(Pipeline, self).__init__()
        self._lbnames = lbnames
        self._lbpipeline = list()
        for lbname in lbnames:
            if lbname.endswith('Labeler'):
                self._lbpipeline.append(getattr(__M__, lbname))

    def __call__(self, item):
        """ Run the item through the pipeline.
        """
        for lb in self._lbpipeline:
            item = lb(item)
        return item



def discrete_statistics(instream, args):
    """ Do statistics on a searious dicrete tokens
    """
    stat = dict()

    if args.pipeline:
        pipeline = Pipeline(args.pipeline)
    else:
        pipeline = lambda x: x

    if args.tokenizer:
        try:
            tokenizer = getattr(__M__, args.tokenizer)
            for line in instream:
                tokens = tokenizer(line)
                for token in tokens[0:-1]:
                    lb = pipeline(token)
                    if lb in stat:
                        stat[lb] += 1
                    else:
                        stat[lb] = 1
        except AttributeError:
            logging.error('Tokenizer %s not found.' % (args.tokenizer,))
            exit(1)
    else:
        for line in instream:
            try:
                lb = pipeline(line.strip())
                if lb in stat:
                    stat[lb] += 1
                else:
                    stat[lb] = 1
            except Exception:
                pass
    return stat

def main():
    """ main()
    """
    args = parse_parameter()

	# Determine the input of JSON streams
    if len(args.sources) > 0:
        fin = fileinput.input(args.sources, openhook = fileinput.hook_compressed)
    else:
        fin = sys.stdin

    # Do statistics
    stat = discrete_statistics(fin, args)

    # Sort results
    if args.sortf:
        stat = [(v, k) for k, v in stat.iteritems()]
        stat.sort()
        stat.reverse()
        stat = [(k, v) for v, k in stat]
    elif args.sortk:
        stat = [(k, v) for k, v in stat.iteritems()]
        stat.sort()
    else:
        stat = [(k, v) for k, v in stat.iteritems()]

    # Print results
    if args.delimiter:
        for key, val in stat:
            print >> sys.stdout, key + args.delimiter + str(val)

def test():
    """docstring for test
    """
    print PWeekLabeler('Wed Feb 01 13:22:07 +0000 2012')


if __name__ == '__main__':
    main()
