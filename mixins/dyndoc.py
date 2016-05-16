# DYNAMIC DOCUMENTATION (dyndoc.py)

from mixin import mixin

class Dyndoc(metaclass=mixin):
    '''Allows for classes to use keywords in docstrings that will be resolved
    at runtime. Warnings can be issued for missing documentation'''
    pass
