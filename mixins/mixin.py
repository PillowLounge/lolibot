

def split_on(iterable, predicate):
	a = []
	b = []
	for i in iterable:
		if predicate(i): a.append(i)
		else: b.append(i)
	return (a, b)

def trying(callable, args=(), error=Exception):
	try: return callable(*args)
	except error: return

def tryattr(obj, attrname):
	try: return getattr(obj, attrname)
	except AttributeError: return

def trykey(obj, attrname):
	try: return obj[attrname]
	except KeyError: return

def replace(obj, attr=None):
	def decorator(fcn):
		def wrapper(*args, **kwargs):
			if attr is None: attr = fcn.__name__
			setattr(obj, attr, fcn)
			return fcn(*args, **kwargs)
		return wrapper
	return decorator

class mixin(type):
	'''Metaclass of all mixins and the constructor of their subclasses both
	mixins and for normal use'''

	def __new__(cls, name, bases, attrs):
		print('mixin.__new__('+ ', '.join((
			repr(cls), repr(name), repr(bases), repr(attrs)
		)) +')')
		mixins, bases = split_on(bases,
			lambda x: tryattr(x, 'metaclass') == mixin)
		attrs['mixins'] = mixins
		print('mixins:'+ ('' if mixins else ' None'))
		for m in mixins:
			print('\t'+ m)
			trying(m._metanew_, (cls, name, bases, attrs), AttributeError)
		for m in mixins:
			trying(m._metainit_(cls, name, bases, attrs), AttributeError)
		if not bases: attrs['metaclass'] = mixin #TODO: examine

		return type(name, tuple(bases), attrs)


if __name__ == '__main__':
	class Test(metaclass=mixin):
		pass
