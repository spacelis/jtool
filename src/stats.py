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
import sys
import logging
import json
from fileset import FileInputSet


def discrete_statistics(instream, args):
    """ Do statistics on a searious dicrete tokens
    """
    stat = dict()

    cnt = 0
    def add_token(token):
        if token in stat:
            stat[token] += 1
        else:
            stat[token] = 1

    if args.intype == 'json':
        for line in instream:
            cnt += 1
            try:
                jobj = json.loads(line)
                for idx in args.fields:
                    add_token(jobj[idx])
            except KeyError as e:
                logging.error('[%s] Field Index Out of List: %s' % (cnt, str(e)))
                if not args.ignore_index_error and not args.ignore_error:
                    exit(1)
            except ValueError as e:
                logging.error('Failed at [%s]: %s' % (cnt, str(e)))
                if not args.ignore_error:
                    exit(1)

    elif args.intype == 'csv':
        for line in instream:
            cnt += 1
            try:
                datarow = line.strip().split(args.delimiter)
                for idx in args.fields:
                    add_token(datarow[idx])
            except IndexError as e:
                logging.error('[%s] Field Index Out of List: %s' % (cnt, str(e)))
                if not args.ignore_index_error and not args.ignore_error:
                    exit(1)
            except Exception as e:
                logging.error('Failed at [%s]: %s' % (cnt, str(e)))
                if not args.ignore_error:
                    exit(1)

    else:
        for line in instream:
            cnt += 1
            try:
                datarow = line.strip()
                add_token(datarow)
            except Exception as e:
                logging.error('Failed at [%s]: %s' % (cnt, str(e)))
                if not args.ignore_error:
                    exit(1)
    return stat

def parse_parameter():
    """ Parse parameters from console
    """

    parser = argparse.ArgumentParser(description='Simple distribution calculator',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='''NOTE: If none of input types specified, each entire line
            will be used as a token''')
    parser.add_argument('-t', '--input-type', action='store', default=None, dest='intype',
            help='Choose an alternative input format', choices=['json', 'csv'])
    parser.add_argument('-f', '--field', action='append', default=None, dest='fields',
            help='Specifying the fields to be processed.')
    parser.add_argument('-d', '--delimiter', action='store', dest='delimiter',
            default='\t', help='The delimiter of input data')
    parser.add_argument('-F', '--sort-freq', action='store_true', default=False, dest='sortf',
            help='Output the statistics with sorting on frequency.')
    parser.add_argument('-K', '--sort-key', action='store_true', default=False, dest='sortk',
            help='Output the statistics with sorting on key.')
    parser.add_argument('-X', '--ignore-index-error', action='store_true', default=False,
            dest='ignore_index_error',
            help='Ignore the errors when then field index doesn\'t exist')
    parser.add_argument('-E', '--ignore-error', action='store_true', default=False,
            dest='ignore_error',
            help='Ignore all the errors when doing statistics')
    parser.add_argument('sources', metavar='file', nargs='*',
            help='Files as inputs. STDIN will be used, if no input file specified.')

    return parser.parse_args()

def main():
    """ main()
    """
    args = parse_parameter()
    logging.basicConfig(format='[%(levelname)s] %(message)s',
                        level=logging.INFO)
    logging.debug(args)

	# Determine the input of JSON streams
    if len(args.sources) > 0:
        fin = FileInputSet(args.sources)
    else:
        fin = sys.stdin

    if args.intype == 'json' and args.fields == None:
        logging.error('No fields specified for processing for a json input')
        exit(1)
    if args.intype == 'csv' and args.fields == None:
        args.fields = [0,]

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
    for key, val in stat:
        print >> sys.stdout, key + '\t' + str(val)

if __name__ == '__main__':
    main()
