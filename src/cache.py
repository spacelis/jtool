#!/bin/python
# -*- coding: utf-8 -*-
"""File: cache.py
Description:
    Cache classes for objects
History:
    0.1.0 The first version.
"""
__version__ = '0.1.0'
__author__ = 'SpaceLis'

import time

class Cache(object):
    """ A chach object will maintain a list of key-value pairs for
        quickly returning values or forming a pool of useful resources.
    """
    class CacheItem(object):
        """ A chech item will contain all information needed for response
            to a request, pool maintaining.
        """
        def __init__(self, key, value):
            super(Cache.CacheItem, self).__init__()
            self.key = key
            self.value = value
            self.timestamp = time.time()

    def __init__(self, poolsize=10, default_method=lambda x:x):
        super(Cache, self).__init__()
        self.pool = dict()
        self.poolsize = poolsize
        self.default_method = default_method

    def set_default_method(self, func):
        """ Set the default method for a unkown key, which should take
            only one argument.
        """
        self.default_method = func

    def _add(self, item):
        """ Add a new cache item in to the pool
        """
        self.pool[item.key] = item

    def remove(self, key):
        """ remove a cache item from the pool
        """
        del self.pool[key]

    def add(self, item):
        """ Add a new item with the replacing strategy.
        """
        return self.add_LRU(item)

    def add_LRU(self, item):
        """ Add a new item replacing the least recently used item if necessary.
        """
        if len(self.pool) >= self.poolsize:
            rm_key = min(self.pool, key=lambda x: self.pool[x].timestamp)
            self.remove(rm_key)
            print 'replace', rm_key
        self._add(item)

    def request(self, key):
        """ request a key. If the key is not in the pool then use default_method
            create a new one for it.
        """
        val = None
        try:
            val = self.pool[key].value
            print 'hit'
        except KeyError:
            val = self.default_method(key)
            self.add(Cache.CacheItem(key, val))
            print 'add new', key, val
        return val


class CachedFunction(object):
    """ A function with no side effects can be cached to improve time-efficiency
        However, only functions with parameters that fit repr() can be applied to.
    """
    def __init__(self, poolsize=1000):
        super(CachedFunction, self).__init__()
        self._cache = Cache(poolsize)

    def __call__(self, func):
        default_method = lambda key: func(*eval(key.split('@#$', 1)[0]),
                **eval(key.split('@#$', 1)[1]))
        self._cache.set_default_method(default_method)

        def wrapper(*args, **kargs):
            key = repr(args) + '@#$' + repr(kargs)
            return self._cache.request(key)
        return wrapper



def testCache():
    a = Cache(3, lambda x: 'id'+str(x))
    assert a.request(1) == 'id1'
    assert a.request(2) == 'id2'
    assert a.request(3) == 'id3'
    assert a.request(4) == 'id4'
    assert a.request(2) == 'id2'

def testCachedFunction():
    @CachedFunction(3)
    def testfunc(a, **kargs):
        return a, kargs['id']

    assert testfunc(1, id=1) == (1, 1)
    assert testfunc(2, id=2) == (2, 2)
    assert testfunc(3, id=3) == (3, 3)
    assert testfunc(4, id=4) == (4, 4)
    assert testfunc(2, id=2) == (2, 2)
    assert testfunc(3, id=3) == (3, 3)

if __name__ == '__main__':
    testCachedFunction()
