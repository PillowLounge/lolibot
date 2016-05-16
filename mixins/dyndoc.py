# DYNAMIC DOCUMENTATION (dyndoc.py)

from mixin import mixin

class Dyndoc(metaclass=mixin):
    '''Allows for classes to use keywords in docstrings that will be resolved
    at runtime. Warnings can be issued for missing documentation'''
    pass

#TODO: have mixins specify docstrings for used interfaces and allow the
#implementation to optionally append info

#example: Persistent makes doc for adapter's __getitem__ and the implementation
#itself only appends useful notes
