#!/home/wenli/devel/python/bin/python
# -*- coding: utf-8 -*-
"""File: jrep.py
Description:
    A tool for manipulating JSON file
History:
    0.2.1 + feature to select json object with inner elements specified in a file
    0.2.0 + feature to ignore malformed json and gzip file
    0.1.1 + output whole json objects and '<=' for condition
    0.1.0 The first version.
"""
__version__ = '0.2.0'
__author__ = 'SpaceLis'

import json
import argparse
import sys
import gzip
import operator
import logging
from fileset import FileInputSet

_ARGS = None

def formatpath(elempath):
    """ Format path for lambda
        In a path, child element is connected to its parent element with '.'.
        If a child element is in a list, then it should be named as '@' + its
        position. Finally this function gives a python representation for the
        path and will be further used as a part of lambda expression.
    """
    path = str()
    for elem in elempath.split('.'):
        if elem.startswith('@'):
            elem = elem[1:]
        else:
            elem = '\'' + elem + '\''
        path += '[' + elem + ']'
    return path

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
    def __init__(self, condstr, ispositive):
        super(MatchCondition, self).__init__()
        self.ispositive = ispositive
        if condstr.find('==') > 0:
            self.elem, self.refval = condstr.split('==')
            # due to the parameter sequence of operator.contains
            # all mfuncstr is literally inversion of mfunc
            self.mfunc = operator.eq
            self.mfuncstr = '='
        elif condstr.find('<=') > 0:
            self.elem, self.refval = condstr.split('<=')
            self.mfunc = operator.ge
            self.mfuncstr = '<='
        elif condstr.find('>=') > 0:
            self.elem, self.refval = condstr.split('>=')
            self.mfunc = operator.le
            self.mfuncstr = '>='
        elif condstr.find('<<') > 0:
            self.elem, setfile = condstr.split('<<')
            self.refval = open(setfile)
            self.mfunc = operator.contains
            self.mfuncstr = '<<'
        else:
            self.elem = condstr
            self.refval = None
        self.pfunc = eval('lambda x: x' + formatpath(self.elem))


    def match(self, jobj):
        """ to see weather the JSON object match the rule
        """
        try:
            val = self.pfunc(jobj)
        except Exception:
            val = None
        if isinstance(self.refval, file):
            self.refval = set([type(val)(v) for v in self.refval])
        if self.refval and val:
            if type(self.refval) != type(val):
                self.refval = type(val)(self.refval)
            matched = self.mfunc(self.refval, val)
            return self.ispositive == matched
        else:
            if val:
                matched = True
            else:
                matched = False
            return self.ispositive == matched
        if self.setval:
            if val in self.setval:
                return self.ispositive
            else:
                return not self.ispositive


class GotoNextLineException(BaseException):
    """ Drop current line and try the next line instead.
    """
    def __init__(self):
        super(GotoNextLineException, self).__init__()

def printelems(jobj, showlist):
    """ Print out the elements specified by the paramenter -l
    """
    global _ARGS
    output = list()


    # output the whole json object and this will override any -l options.
    if _ARGS.whole:
        print >> _ARGS.fout, json.dumps(jobj).encode('utf-8', errors='ignore')
        return

    # output the json elements specified by -l options
    if _ARGS.json:
        for elem in showlist:
            try:
                obj = elem(jobj)
                output.append(unicode(json.dumps(obj)))
            except:
                output.append(unicode(_ARGS.nullstr))

    else:
        for elem in showlist:
            try:
                obj = elem(jobj)
                output.append(unicode(obj))
            except:
                output.append(unicode(_ARGS.nullstr))

    if _ARGS.oneline:
        print >> _ARGS.fout, (_ARGS.separator.join(output).replace('\n','') + _ARGS.delimiter).\
            encode('utf-8', errors='ignore'),
    else:
        print >> _ARGS.fout, (_ARGS.separator.join(output) + _ARGS.delimiter).\
            encode('utf-8', errors='ignore'),

def parse_parameter():
    """ Parse the argument
    """
    global _ARGS
    parser = argparse.ArgumentParser(description='Extract data from JSON objects which stored '
            'in files as lines. or check the integrity of JSON collections.',
            epilog='Note: Malformed JSON string or GZIP ending will be safely '
            'skipped with a warning to stderr. Condition INCLUDE are all processed before EXCLUDE.' )
    parser.add_argument('-l', '--list', dest='show', action='append', metavar='ELEM',
            help='Elements path extracted from JSON as output. E.g. -l user.id')
    parser.add_argument('-L', '--whole', dest='whole', action='store_true',
            default=False, help='output the whole json, override the -l options.')
    parser.add_argument('-i', '--include', dest='include', action='append', metavar='COND',
            help='Only list JSON that has INCLUDE as a member, or/and the '
            'member {==|>=|<=} a given value. E.g. -i user.id==123')
    parser.add_argument('-I', '--inset', dest='inset', action='store', metavar='file',
            help='Only list JSON that with the indicated elements in the set '
            'specified in a file')
    parser.add_argument('-x', '--exclude', dest='exclude', action='append', metavar='COND',
            help='Only list JSON that doesn\'t has EXCLUDE as a member, or/and '
            'the member {==|>=|<=} a given value. E.g. -e user.id==123')
    parser.add_argument('-D', '--delimiter', dest='delimiter', action='store',
            default='\n', help='The object delimiter used in output format.')
    parser.add_argument('-S', '--separator', dest='separator', action='store',
            default='\t', help='The separator used between members in output '
            'format.')
    parser.add_argument('-N', '--nullstr', dest='nullstr', action='store',
            default='NULL', help='The NULL string used when the member is null '
            'or not found.')
    parser.add_argument('-o', '--output', dest='output', action='store', metavar='file',
            default=None, help='The output file, gzipped if the name ends with '
            '.gz')
    parser.add_argument('-J', '--json', dest='json', action='store_true',
            default=False, help='Output each element in json format.')
    parser.add_argument('-n', '--num', dest='num', action='store',
            default=-1, help='Output only the first NUM JSON objects.')
    parser.add_argument('-c', '--check', dest='check', action='store_true',
            default=False, help='Check the integrity of JSON collection with errors '
            'to stderr')
    parser.add_argument('-1', '--oneline', dest='oneline', action='store_true',
            default=False, help='Force each item of outputs in one line.')
    parser.add_argument('sources', metavar='file', nargs='*',
            help='Input files. Those end with .gz will be open as GZIP files.')
    _ARGS = parser.parse_args()
    if len(_ARGS.sources) > 0:
        _ARGS.fin = FileInputSet(_ARGS.sources)
    else:
        _ARGS.fin = sys.stdin

    if _ARGS.output:
        if _ARGS.output.endswith('.gz'):
            _ARGS.fout = gzip.open(_ARGS.output, 'wb')
        else:
            _ARGS.fout = open(_ARGS.output, 'w')
    else:
        _ARGS.fout = sys.stdout

def json_check():
    """ Check the integrity of the JSONs in the files
    """
    global _ARGS
    cnt = 0
    for line in _ARGS.fin:
        cnt += 1
        if _ARGS.num >= 0 and cnt > _ARGS.num:
            break
        try:
            obj = json.loads(line)
        except ValueError as ve:
            logging.warn(ve)
            logging.warn('At %s[%d], %s' % (_ARGS.fin.get_current(), cnt, line.strip()))

def main():
    """ Main function of this tool which deals with parameter mapping.
    """
    global _ARGS
    parse_parameter()

    conds = list()
    if _ARGS.include:
        for elem in _ARGS.include:
            conds.append(MatchCondition(elem, True))
    if _ARGS.exclude:
        for elem in _ARGS.exclude:
            conds.append(MatchCondition(elem, False))

    showlist = list()
    if _ARGS.show:
        for elem in _ARGS.show:
            if elem.startswith(':'):
                showlist.append(eval('lambda x: \'' + elem[1:] + '\''))
            else:
                showlist.append(eval('lambda x: x' + formatpath(elem)))

    if not _ARGS.check:
        cnt = 0
        for line in _ARGS.fin:
            cnt += 1
            if _ARGS.num >= 0 and cnt > _ARGS.num:
                break
            try:
                obj = json.loads(line)
                for cond in conds:
                    if not cond.match(obj):
                        raise GotoNextLineException
                printelems(obj, showlist)
            except GotoNextLineException:
                pass
            except ValueError as ve:
                logging.warn(ve)
                logging.warn('At %s[%d], %s' % (_ARGS.fin.get_current(), cnt, line.strip()))
    else:
        json_check()


if __name__ == '__main__':
    main()