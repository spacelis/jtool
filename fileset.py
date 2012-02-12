#!python
# -*- coding: utf-8 -*-
"""File: fileset.py
Description:
    A firtual file representing a set of files for reading
History:
    0.1.0 The first version.
"""
__version__ = '0.1.0'
__author__ = 'SpaceLis'

import logging
import gzip

class FileInputSet(object):
    """ A file object representing a set of files for reading
    """
    def __init__(self, srcs):
        super(FileInputSet, self).__init__()
        self._srcs = srcs
        self._current = None

    def __iter__(self):
        for src in self._srcs:
            try:
                if src.endswith('.gz'):
                    fin = gzip.open(src)
                else:
                    fin = open(src)
                cnt = 0
                self._current = src
                for line in fin:
                    yield line
                    cnt += 1
            except IOError as e:
                logging.warn('%s at %s[%d]' % (e, self.get_current(), cnt))

    def get_current(self):
        """ Get current file in the iteration
        """
        return self._current


