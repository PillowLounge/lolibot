### Column oriented Storage ###

import math
import os

standard_bytearray_attr = 'bytes'
readint = lambda f,n: int.from_bytes(f.read(n), byteorder='little')

def add(iterable, addend):
        yield from addend + i for i in iterable



class Table(object):

    def __init__(self, tblname, *columns, path='../logs/'):
        if columns and type(columns[0]) is not str: columns = columns[0]
        self.tblname = tblname
        self.columns = list(ColumnInt(name, binary=True) for name in colname)
        #TODO: make columns more descriptive than just names
        self.path    = path
        self.files   = []

    def open(self, mode='a'):
        for col in self.columns: col.open(mode)

    def append(self, *data):
        self.open()
        for i in range(len(self.columns)):
            self.columns[i].append(data[i])

    def optimize():
        pass

class ColumnInt(object):

    def __init__(self, name, binary=False, path=''):
        self.name    = name
        self.path    = path + name
        self.file    = None
        self.binary  = binary
        self.preproc = to_binary if binary else str
        self.sorted  = True
        self.unique  = True
        self.lbound  = None # lower bound
        self.ubound  = None # upper bound

    def __iter__(self):
        assert self.open('r')
        f = self.file
        assert f.seekable()
        headersize = readint(f,2)
        f.seek(headersize, os.SEEK_CUR)
        #TODO: refactor into a separate decode method
        # get the log_2 of upper bound to get maximum bit size
        # maxbits = math.frexp(self.ubound - self.lbound)[1] \
        #     if self.lbound is not None and self.ubound is not None \
        #     else 64
        # maxbytes = math.ceil(maxbits/8)
        # uniq   = self.unique
        # sortd  = self.sorted
        # b = f.read()
        # repeats = 0
        # if sortd: yield readint(f, maxbytes)
        # while True:
        #     if b[0] & b'\x01': pass
        #     f.read()
        #     yield i
        f.read(8)

    def __getitem__(self, key):
        assert type(key) is int and key >= 0
        assert self.open()
        current = 0
        for row in self:
            if current < key: continue

    @property
    def closed(self):
        f = self.file
        return not f or f.closed

    def open(self, mode='a'):
        if self.closed or mode not in self.file.mode:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            self.file = open(self.path, mode +('b' if self.binary else ''))
        return self

    def close(self):
        if self.file: self.file.close()

    def append(self, data):
        self.open()
        data = self.preproc(data)
        f = self.file
        f.write(data)
        f.flush()

    def optimize(self):
        #TODO: generalize for non-integer type columns
        self.close()
        f = open(self.path + self.name, 'r+'+('b' if self.binary else ''))
        header = self.readheader(f)
        for row in header['iterator']:
            pass # read and parse each value then recompress using updated
            # statistics
        f.close()

    def readheader(self, readable):
        return {'iterator':()}

    @staticmethod
    def readRow(f, index):
        f.read()

def to_binary(data):
    try:
        #if object implements its own cast
        b = getattr(data, standard_bytearray_attr)
        if callable(b): b = b()
    except AttributeError:
        if type(data) is str:
            b = bytearray(data, encoding='utf-8')
        else: b = bytearray(data)
    return b

if __name__ == '__main__':
    try:
        tbl = Table('testtable', 'col', path='colstorTest/')
        while True:
            cmd = input()
            tbl.append(cmd)
    except KeyboardInterrupt:
        pass
