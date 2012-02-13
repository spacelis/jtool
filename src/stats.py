#!/home/wenli/devel/python/bin/python
# -*- coding: utf-8 -*-
"""File: stats.py
Description:
    Get statistics from input.
History:
    0.2.0 + Ability of converting a field of an item before statistics
    0.1.1 + Sorting option for outputs.
    0.1.0 The first version.
"""
__version__ = '0.1.1'
__author__ = 'SpaceLis'

import argparse
import re
import sys
import logging
import json
from fileset import FileInputSet
from labeler import Pipeline

_SPACES = re.compile(r'\s+')
__M__ = sys.modules['labeler']

def SpaceTokenizer():
    return _SPACES.split

class FieldConverter(object):
    """ Preprocess the field data before doing statistics
    """
    def __init__(self):
        super(FieldConverter, self).__init__()
        self.processer = dict()

    def add_field_processer(self, field, pipeline):
        """ Add a new process to a field
        """
        self.processer[field] = pipeline

    def process(self, datum):
        """ Process a line of data
        """
        logging.debug('Processing data')
        for f in self.processer.iterkeys():
            logging.debug('Processing [%s]' % (f,))
            datum[f] = self.processer[f](datum[f])
        return datum


def discrete_statistics(instream, fproc, args):
    """ Do statistics on a searious dicrete tokens
    """
    stat = dict()

    cnt = 0
    if args.json:
        for line in instream:
            cnt += 1
            try:
                bdatum = json.loads(line)
                datum = fproc.process(bdatum)
                token = json.dumps(datum)
                logging.debug('%s => %s' % (datum, token))
                if token in stat:
                    stat[token] += 1
                else:
                    stat[token] = 1
            except Exception as e:
                logging.warn('Failed at [%s]: %s' % (cnt, str(e)))

    else:
        for line in instream:
            cnt += 1
            try:
                bdatum = line.strip().split(args.separator)
                datum = fproc.process(bdatum)
                token = args.separator.join(datum)
                logging.debug('%s => %s' % (bdatum, token))
                if token in stat:
                    stat[token] += 1
                else:
                    stat[token] = 1
            except Exception as e:
                logging.warn('Failed at [%s]: %s' % (cnt, str(e)))
    return stat

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
    parser.add_argument('-p', '--pipeline', action='append', dest='pipelines',
            metavar='labeler',
            help='Tokenize the input line before doing statistics, useful for '
            'text.')
    parser.add_argument('-s', '--separator', action='store', dest='separator',
            default='\t', help='The separator of input data')
    parser.add_argument('-j', '--json', action='store_true', default=False, dest='json',
            help='Use json format as input')
    parser.add_argument('-f', '--sort-freq', action='store_true', default=False, dest='sortf',
            help='Output the statistics with sorting on frequency.')
    parser.add_argument('-k', '--sort-key', action='store_true', default=False, dest='sortk',
            help='Output the statistics with sorting on key.')
    parser.add_argument('sources', metavar='file', nargs='*',
            help='Files as inputs. STDIN will be used, if no input file specified.')
    return parser.parse_args()

def main():
    """ main()
    """
    args = parse_parameter()
    logging.basicConfig(format='%(message)s', level=logging.INFO)
    logging.debug(args)

	# Determine the input of JSON streams
    if len(args.sources) > 0:
        fin = FileInputSet(args.sources)
    else:
        fin = sys.stdin

    fp = FieldConverter()
    if args.json:
        for p in args.pipelines:
            field, plname = p.split(':', 1)
            fp.add_field_processer(field, Pipeline(plname.split(':')))
    else:
        for p in args.pipelines:
            field, plname = p.split(':', 1)
            fp.add_field_processer(int(field), Pipeline(plname.split(':')))
    # Do statistics
    stat = discrete_statistics(fin, fp, args)

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
    for key, val in stat:
        print >> sys.stdout, key + '\t' + str(val)

if __name__ == '__main__':
    main()
