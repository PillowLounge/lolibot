# log moments (mean, variance, skewness, kurtosis) and quantiles

# why am I spending time creating a complex quantile and histogram
# estimator when I only need average, so far

from math import sqrt
from bisect import bisect_left
import scipy.stats as st

maxlong = 9223372036854775807
class RunningStat(object):
    '''Gather single-pass statistical data from an iterable'''

    __slots__ = ('count', 'moments', 'min', 'max')

    def __init__(object, moments=1, buckets=1, sorted=False):
        self.count       = 0
        self.moments     = [0] * moments # statistical moments
        #self.buckets     = [0] * buckets # count of items in each bucket
        #self.percentiles = [0] * (buckets + 1) # border values between buckets
        #self.vk = 0
        self.min = None
        self.max = None

    def __call__(self, iterable, quantifier=float):
        '''Wrap an iterable'''
        item = next(iterable)
        self.count += 1
        num = quantifier(item)
        if num < self.min: self.min = num
        else if num > self.max: self.max = num
        #index = bisect_left(self.percentiles, num)
        #self.bucket[index] += 1

        yield item

    def add_to_moments(self, num):
        oldmean = self.moments[0]
        try: newmean = oldmean + (num - oldmean) / self.count
        except ZeroDivisionError: newmean = num
        vk = vk + (num - oldmean)(num - newmean)
        self.moments[0] = newmean

    def __len__(self):
        return self.count

    def __iadd__(self, other):
        if type(other) is str:
            _addstr(self, other)
            return
        for string in other: _addstr(self, string)

    #def __enter__(self): pass
    def __exit__(self): self._mean = float(self._mean / self.count)

    def _addstr(self, string):
        words = string.split()
        self.count = len(words)
        for w in words: self._mean += len(w)

    def _mean_(self):
        if type(self._mean) is int: __exit__(self)
        return self._mean

    def append(self, other):
        self.count += 1
        self.accumulated += len(other)

    @property
    def mean(self): return self.moments[0]

    @property
    def variance(self): return self.moments[1]

    @property
    def kurtosis(self): return self.moments[2]

class Gen(object):

    __slots__ = ('inner')

    def __init__(self, inner): self.inner = inner
    def __iter__(self): return Iter(self, self.inner)
    def __len__(self): return len(self.inner)

class Iter(object):

    __slots__ = ('generator', 'count', 'inner')

    def __new__(cls, gen, iterable, action=None):
        if isinstance(iterable, cls):
            return iterable
        return super().__new__(cls, gen, iterable)

    def __init__(self, gen, iterable, action=None):
        self.generator = gen
        self.count = 0
        self.actions = [] if action is None else [action]
        self.inner = iterable \
            if hasattr(iterable, '__next__') \
            else iterable.__iter__()

    def __iter__(self): return self

    def __next__(self):
        r = self.inner.__next__()
        for a in self.actions: r = a(r)
        self.count += 1
        return r

    def __len__(self): return self.generator.__len__() - self.count

z_score = st.norm.ppf((1+.95)/2)
z_sqr   = z_score*z_score

def wilson_score(positive, n):
    '''returns lower bound of Wilson score confidence interval for a Bernoulli
    parameter
    resource: http://www.evanmiller.org/how-not-to-sort-by-average-rating.html'''
    assert positive <= n
    if n is 0: return float('NaN')
    p    = positive / n
    zz÷n = z_sqr / n
    return (p + zz÷n/2 - z * sqrt((p * (1 - p) + zz÷n/4) / n)) \
        / (1 + zz÷n)

# trying using closure instead

def stats(gen, moments=2, readers=[]):

    def generator():
