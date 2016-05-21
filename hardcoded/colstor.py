### Column oriented Storage ###

import os

standard_bytearray_attr = 'bytes'

class Table(object):

    def __init__(self, tblname, *columns, path='../logs/'):
        self.tblname  = tblname
        self.colnames = []
        for colname in columns:
            if type(colname) in (tuple, list):
                for colname2 in colname:
                    self.colnames.append(colname2)
            else: self.colnames.append(colname)
        self.path   = path
        self.opened = False
        self.files  = []

    def open(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        for col in self.colnames:
            self.files.append(open(self.path + self.tblname + col, 'ab'))
        self.opened = True

    def append(self, *data):
        if not self.opened: self.open()
        for i in range(len(self.files)):
            f = self.files[i]
            f.write(binary(data[i]))
            f.flush()

    def optimize():
        pass

class Column(object):

    def __init__(self, name, binary=False, path=''):
        self.name    = name
        self.path    = path
        self.file    = None
        self.opened  = False
        self.binary  = binary
        self.preproc = to_binary if binary else str
        self.sorted  = True
        self.boundU  = 0 # upper bound (integers only)
        self.boundL  = 0 # lower bound (integers only)

    def open(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.file = open(self.path + self.name,
        'a'+('b' if self.binary else ''))
        self.opened = True

    def close(self):
        if self.file: self.file.close()
        self.opened = False

    def append(self, data):
        if not self.opened: self.open()
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
