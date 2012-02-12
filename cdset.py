#!python
# -*- coding: utf-8 -*-
"""File: cdbset.py
Description:
    Column based data set.
History:
    0.1.0 The first version.
"""
__version__ = '0.1.0'
__author__ = 'SpaceLis'

import blist

def genzero(cnt):
    """ Generate zeros
    """
    _cnt = 0
    while _cnt < cnt:
        _cnt += 1
        yield 0
    return

class Dataset(dict):
    """Dataset is a column oriented data storage. The key is the title of the
    column while the value is the list of data in the column (key) in a
    sequential order.
    """
    def __init__(self, *arg, **karg):
        super(Dataset, self).__init__(*arg, **karg)
        self._size = 0
        self.sortedkey = None
        self.sortedindex = None

    def size(self):
        """the size of the dataset, i.e., the number of rows
        """
        return self._size

    def append(self, item):
        """Add a new data item into the dataset
        This is just for mocking list().append()
        """
        for key in item.iterkeys():
            if key not in self:
                self[key] = blist.blist(genzero(self._size))
            self[key].append(item[key])
        self._size += 1

    def extend(self, itemlist):
        """Extend the dataset with the itemlist
        This is just for mocking list().extend()
        """
        for item in itemlist:
            self.append(item)

    def distinct(self, key):
        """Return the value set of the key
        """
        vset = set()
        for val in self[key]:
            vset.add(val)
        return [val for val in vset]

    def groupfunc(self, key, pkey, func):
        """Return the output of a function to the values grouped by key
        """
        rst = DataItem()
        if self.sortedkey != key:
            self.sort(key)

        temp = blist.blist()
        idx_val = type(self[key][0]).__init__()
        for idx in self.sortedindex:
            if idx_val != self[key][idx]:
                if len(temp)>0:
                    rst[idx_val] = func(temp)
                temp = blist.blist()
                idx_val = self[key][idx]
            temp.append(self[pkey][idx])
        rst[idx_val] = func(temp)
        return rst

    def sort(self, key):
        """ Sort data set according the key
        """
        if self.sortedkey == key:
            return
        self.sortedindex = blist.sortedlist(range(0, self._size),
                key=lambda x:self[key][x])
        self.sortedkey = key

    def merge(self, dset):
        """Merge the keys and values into this Dataset
        """
        if self._size != dset._size:
            raise TypeError, "size doesn't match"
        for key in dset.iterkeys():
            if key not in self:
                self[key] = dset[key]
            else:
                raise TypeError, "Key conflicting"

    def item(self, idx):
        """Return the item at the position idx
        """
        rst = DataItem()
        for key in self.iterkeys():
            rst[key] = self[key][idx]
        return rst

    def sitem(self, idx):
        """ Return an item at the position idx of the sorted key
        """
        rst = DataItem()
        for key in self.iterkeys():
            rst[key] = self[key][self.sortedindex[idx]]
        return rst

    def sorteditems(self, key):
        """docstring for sorteditems
        """
        if key != self.sortedkey:
            self.sort(key)
        for idx in self.sortedindex:
            yield self.item(idx)

    def __iter__(self):
        """Iterating items in the dataset
        """
        for idx in range(self._size):
            yield self.item(idx)

class PartialIterator(object):
    """Iterator by an index list"""
    def __init__(self, dset, idc):
        super(PartialIterator, self).__init__()
        self._dset, self._idc = dset, idc
        self._idx = 0

    def __iter__(self):
        """Make it iterative"""
        for idx in self._idc:
            yield self._dset.item(idx)

class DataItem(dict):
    """Keeps data"""
    def __init__(self, *arg, **karg):
        super(DataItem, self).__init__(*arg, **karg)

    def accum_dist(self, src):
        """merge two distribution of words"""
        for key in src.iterkeys():
            if key in self.iterkeys():
                self[key] += src[key]
            else:
                self[key] = src[key]
        return

def main():
    """ test
    """
    import random
    x = Dataset()
    for i in range(16000000):
        x.append({'id': i, 'val': random.random(), 'pc': random.random()})
    x.sort('val')
    for item in x.sorteditems('id'):
        print item
    for item in x.sorteditems('val'):
        print item


if __name__ == '__main__':
    main()
