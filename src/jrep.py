#!/home/wenli/devel/python/bin/python
# -*- coding: utf-8 -*-
"""File: jrep.py
Description:
    A tool for manipulating JSON file
History:
    0.2.5 x performance boosting and rearrange console parameters
    0.2.4 + processing CSV format as input
    0.2.3 x fix a bug of outputing jsons, fix a bug of outputing degug info
    0.2.2 + if no list element specified then output full json instead
    0.2.1 + feature to select json object with inner elements specified in a file
    0.2.0 + feature to ignore malformed json and gzip file
    0.1.1 + output whole json objects and '<=' for condition
    0.1.0 The first version.
"""
__version__ = '0.2.5'
__author__ = 'SpaceLis'

import re
import json
import argparse
import sys
import gzip
import operator
import logging
from fileset import FileInputSet

_ARGS = None

NUMBER = re.compile(r'^\d+(\.\d+)?$')

class Extractor(object):
    """ Extract an element from an object by a path
    """
    def __init__(self, elempath):
        """ Format path for lambda
            In a path, child element is connected to its parent element with '.'.
            If a child element is in a list, then it should be named as '@' + its
            position. Finally this function gives a python representation for the
            path and will be further used as a part of lambda expression.
        """
        super(Extractor, self).__init__()
        self.ppath = str()
        self.path = elempath
        if elempath.startswith(':'):
            self.parse = eval('lambda x: x\'' + elempath[1:] + '\'')
            logging.debug('Transform Path: %s => %s' % (self.path, self.ppath))
            return
        for elem in elempath.split('.'):
            if elem.startswith('@'):
                elem = elem[1:]
            else:
                elem = '\'' + elem + '\''
            self.ppath += '[' + elem + ']'
        logging.debug('Transform Path: %s => %s' % (self.path, self.ppath))
        self.parse = eval('lambda x: x' + self.ppath)


class MatchCondition(object):
    """ A Conditioning object for selecting JSONs
        The constructor will take a string defining the condition and
        also a boolean indicating whether it is a match when a JSON
        fulfill the condition.
        A condition string contains 2 or 3 parts:
        ELEMPATH [OPER REFVAL]
        ELEMPATH is a path for accessing a specific element in a JSON.
        OPER is a operator including ==, >=, <=, <<, which means equality,
            greater than (inclusive), less then (inclusive), and contained in.
        REFVAL is the reference value for comparison. The CONTAINED_IN operator
            uses REFVAL to indicate the file holding the set of reference values.
    """
    def __init__(self, condstr, ispositive, nullstr='NULL', iscsv=False):
        super(MatchCondition, self).__init__()
        self.ispositive = ispositive
        self.nullstr = nullstr
        self.firstmatch = True
        if condstr.find('==') > 0:
            self.elem, self.refval = condstr.split('==', 1)
            # due to the parameter sequence of operator.contains
            # all mfuncstr is literally inversion of mfunc
            self.mfunc = operator.eq
            self.mfuncstr = '=='
            if iscsv:
                self.match = self.match_csv_value
            else:
                self.match = self.match_json_value
        elif condstr.find('<=') > 0:
            self.elem, self.refval = condstr.split('<=', 1)
            self.mfunc = lambda x, y: x <= y
            self.mfuncstr = '<='
            if iscsv:
                self.match = self.match_csv_value
            else:
                self.match = self.match_json_value
        elif condstr.find('>=') > 0:
            self.elem, self.refval = condstr.split('>=', 1)
            self.mfunc = lambda x, y: x >= y
            self.mfuncstr = '>='
            if iscsv:
                self.match = self.match_csv_value
            else:
                self.match = self.match_json_value
        elif condstr.find('<<') > 0:
            self.elem, setfile = condstr.split('<<', 1)
            self.refval = open(setfile)
            self.mfunc = lambda x, y: x in y
            self.mfuncstr = '<<'
            if iscsv:
                self.match = self.match_csv_set
            else:
                self.match = self.match_json_set
        else:
            self.elem = condstr
            self.mfuncstr = 'select'
            self.refval = None
            if iscsv:
                self.match = self.match_csv_having
            else:
                self.match = self.match_json_having
        self.pfunc = Extractor(self.elem)

        if self.mfuncstr != 'select':
            if not self.refval:
                raise ValueError('Wrong Condition String: %s' % (condstr,))
            self.str = 'Matching %s%s%s%s' % ('I' if ispositive else 'X',
                    self.elem, self.mfuncstr,
                    self.refval.name if isinstance(self.refval, file) else self.refval)
        else:
            self.str = 'Selecting %s%s' % ('I' if ispositive else 'X', self.elem)
        logging.debug(self.str)

    def match_json_having(self, jobj):
        """ Check whether the JSON should be select for output as
            having an specified element.
        """
        try:
            val = self.pfunc.parse(jobj)
            return self.ispositive
        except KeyError:
            return not self.ispositive

    def match_csv_having(self, obj):
        """ Check whether the obj should be select for output as
            having an specified element.
        """
        val = self.pfunc.parse(obj)
        if val == self.nullstr:
            return not self.ispositive
        return self.ispositive

    def match_json_value(self, jobj):
        """ Check whether the JSON should be selected for output
        """
        try:
            val = self.pfunc.parse(jobj)
            if self.firstmatch:
                self.refval = type(val)(self.refval)
                self.firstmatch = False
            matched = self.mfunc(val, self.refval)
            logging.debug('Condition [%s]: %s [%s]' % (self.str, str(val),
                '+' if self.ispositive==matched else '-'))
            return self.ispositive == matched
        except KeyError:
            return False

    def match_csv_value(self, obj):
        """ Check whether the CSV row should be selected for output
        """
        val = self.pfunc.parse(obj)
        if val == self.nullstr:
            return False

        if self.firstmatch:
            if NUMBER.match(self.refval):
                self.refval = float(self.refval)
            self.firstmatch = False
        matched = self.mfunc(type(self.refval)(val), self.refval)
        logging.debug('Condition [%s]: %s [%s]' % (self.str, str(val),
            '+' if self.ispositive==matched else '-'))
        return self.ispositive == matched

    def match_json_set(self, jobj):
        """ Check whether the JSON should be selected for output
        """
        try:
            val = self.pfunc.parse(jobj)
            if self.firstmatch:
                self.refval = set([type(val)(v) for v in self.refval])
                self.firstmatch = False
            logging.debug('Condition [%s]: %s %s' % (self.str, str(val),
                [v for v in self.refval]))
            if val in self.refval:
                return self.ispositive
            else:
                return not self.ispositive
        except KeyError:
            return False

    def match_csv_set(self, obj):
        """ Check whether the CSV row should be selected for output
        """
        val = self.pfunc.parse(obj)
        if val == self.nullstr:
            return False

        if self.firstmatch:
            self.refval = set([v.strip() for v in self.refval])
            self.firstmatch = False
        logging.debug('Condition [%s]: %s %s' % (self.str, str(val),
            [v for v in self.refval]))
        if val in self.refval:
            return self.ispositive
        else:
            return not self.ispositive


class GotoNextLineException(BaseException):
    """ Drop current line and try the next line instead.
    """
    def __init__(self):
        super(GotoNextLineException, self).__init__()

class DataPrinter(object):
    """ A printing object
    """
    def __init__(self, fout, extractors, iscsv=False,
            is_force_in_oneline=False, nullstr='NULL', delimiter='\n'):
        super(DataPrinter, self).__init__()
        self.extractors = extractors
        self.iscsv = iscsv
        self.is_force_in_oneline = is_force_in_oneline
        self.nullstr = nullstr
        self.fout = fout
        self.delimiter = delimiter
        if self.iscsv:
            if len(extractors) > 0:
                if is_force_in_oneline:
                    self.prints = self.print_csv_oneline
                else:
                    self.prints = self.print_csv
            else:
                if is_force_in_oneline:
                    self.prints = self.printall_csv_oneline
                else:
                    self.prints = self.printall_csv
        else:
            if len(extractors) > 0:
                self.prints = self.print_json
            else:
                self.prints = self.printall_json


    def print_json(self, jobj):
        """ Print json with respect to extractors
        """
        output = list()
        for elem in self.extractors:
            try:
                val = elem.parse(jobj)
                output.append((elem.path, unicode(val)))
            except KeyError:
                output.append((elem.path, unicode(self.nullstr)))
        print >> self.fout, (json.dumps(dict(output)).encode('utf-8', errors='ignore'))

    def print_csv(self, obj):
        """ Print obj with respect to extractors
        """
        output = list()
        for elem in self.extractors:
            try:
                val = elem.parse(obj)
                output.append(unicode(val))
            except KeyError:
                output.append(unicode(self.nullstr))
        print >> self.fout, (self.delimiter.join(output)).\
            encode('utf-8', errors='ignore')

    def print_csv_oneline(self, obj):
        """ Print obj with respect to extractors and in one line
        """
        output = list()
        for elem in self.extractors:
            try:
                val = elem.parse(obj)
                output.append(unicode(val))
            except KeyError:
                output.append(unicode(self.nullstr))
        print >> self.fout, (self.delimiter.join(output).replace('\n','')).\
            encode('utf-8', errors='ignore')

    def printall_json(self, jobj):
        """ Print the entire json
        """
        print >> self.fout, json.dumps(jobj).encode('utf-8', errors='ignore')

    def printall_csv(self, obj):
        """ Print the entire obj
        """
        print >> self.fout, self.delimiter.join(obj).encode('utf-8', errors='ignore')

    def printall_csv_oneline(self, obj):
        """ Print the entire obj in one line
        """
        print >> self.fout, (self.delimiter.join(obj).replace('\n','')).\
            encode('utf-8', errors='ignore')

def parse_parameter():
    """ Parse the argument
    """
    parser = argparse.ArgumentParser(description='Extract data from JSON objects which stored '
            'in files as lines. or check the integrity of JSON collections.',
            epilog='Note: Malformed JSON string or GZIP ending will be safely '
            'skipped with a warning to stderr. Condition INCLUDE are all processed before EXCLUDE.' )
    parser.add_argument('-f', '--field', dest='fields', action='append', metavar='ELEM', default=list(),
            help='Elements path extracted from JSON as output. E.g. -f"user.id"')
    parser.add_argument('-i', '--include', dest='include', action='append', metavar='COND', default=list(),
            help='Only list JSON that has INCLUDE as a member, or/and the '
            'member {==|>=|<=} a given value. E.g. -i"user.id==123"')
    parser.add_argument('-x', '--exclude', dest='exclude', action='append', metavar='COND', default=list(),
            help='Only list JSON that doesn\'t has EXCLUDE as a member, or/and '
            'the member {==|>=|<=|<<} a given value. E.g. -x"user.id==123"')
    parser.add_argument('-o', '--output', dest='output', action='store', metavar='file',
            default=None, help='The output file, gzipped if the name ends with .gz')
    parser.add_argument('-J', '--outjson', dest='outjson', action='store_true',
            default=False, help='Output each element in json format.')
    parser.add_argument('-C', '--incsv', dest='incsv', action='store_true', default=False,
            help='Use CSV file as input and output format.')
    parser.add_argument('-n', '--num', dest='num', action='store', type=int,
            default=-1, help='Output only the first NUM JSON objects.')
    parser.add_argument('--delimiter', dest='delimiter', action='store',
            default='\t', help='The object delimiter used in csv format.')
    parser.add_argument('--check', dest='check', action='store_true',
            default=False, help='Check the integrity of JSON collection with errors '
            'to stderr')
    parser.add_argument('--oneline', dest='oneline', action='store_true',
            default=False, help='Force each item of outputs in one line.')
    parser.add_argument('--nullstr', dest='nullstr', action='store', default='NULL',
            help='The NULL string used when the member is null '
            'or not found.')
    parser.add_argument('--debug', dest='debug', action='store_true', default=False,
            help='Run jrep in debug mode')
    parser.add_argument('sources', metavar='file', nargs='*',
            help='Input files. Those end with .gz will be open as GZIP files.')
    args = parser.parse_args()
    if len(args.sources) > 0:
        args.fin = FileInputSet(args.sources)
    else:
        args.fin = sys.stdin

    if args.output:
        if args.output.endswith('.gz'):
            args.fout = gzip.open(args.output, 'wb')
        else:
            args.fout = open(args.output, 'w')
    else:
        args.fout = sys.stdout
    return args

def json_check(fin, num):
    """ Check the integrity of the JSONs in the files
    """
    cnt = 0
    if num >= 0:
        for line in fin:
            try:
                obj = json.loads(line)
            except ValueError as ve:
                logging.warn(ve + '\nAt %s[%d], %s' % (fin.get_current(), cnt, line.strip()))
    else:
        for line in fin:
            cnt += 1
            if cnt > num:
                break
            try:
                obj = json.loads(line)
            except ValueError as ve:
                logging.warn(ve + '\nAt %s[%d], %s' % (fin.get_current(), cnt, line.strip()))

def main():
    """ Main function of this tool which deals with parameter mapping.
    """
    args = parse_parameter()
    logging.basicConfig(format='%(message)s', level=logging.DEBUG if args.debug else logging.WARNING)
    logging.debug('Version=' + __version__)
    logging.debug(args)

    conds = list()
    if args.include:
        for elem in args.include:
            conds.append(MatchCondition(elem, True, args.nullstr, args.incsv))
    if args.exclude:
        for elem in args.exclude:
            conds.append(MatchCondition(elem, False, args.nullstr, args.incsv))

    extractors = list()
    for elem in args.fields:
        extractors.append(Extractor(elem))

    dataprinter = DataPrinter(args.fout, extractors, not args.outjson,
                            args.oneline, args.nullstr, args.delimiter)

    if not args.check:
        cnt = 0
        if not args.incsv:
            for line in args.fin:
                cnt += 1
                if args.num >= 0 and cnt > args.num:
                    break
                try:
                    obj = json.loads(line)
                    for cond in conds:
                        if not cond.match(obj):
                            raise GotoNextLineException
                    dataprinter.prints(obj)
                except GotoNextLineException:
                    pass
                except ValueError as ve:
                    logging.warn(ve + '\nAt %s[%d], %s' % (args.fin.get_current(), cnt, line.strip()))
        else:
            for line in args.fin:
                cnt += 1
                if args.num >= 0 and cnt > args.num:
                    break
                try:
                    obj = line.strip().split(args.delimiter)
                    for cond in conds:
                        if not cond.match(obj):
                            raise GotoNextLineException
                    dataprinter.prints(obj)
                except GotoNextLineException:
                    pass
                except ValueError as ve:
                    logging.warn(ve + '\nAt %s[%d], %s' % (args.fin.get_current(), cnt, line.strip()))
    else:
        json_check(args.fin, args.num)


if __name__ == '__main__':
    main()
