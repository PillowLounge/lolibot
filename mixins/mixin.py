

def split_on(iterable, predicate):
	a= [], b = []
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

def replace(obj, attr):
	def decorator(fcn):
		def wrapper(*args, **kwargs):
			setattr(obj, attr, fcn)
			return fcn(*args, **kwargs)
		return wrapper
	return decorator

class mixin(type):
	'''Metaclass of all mixins and the constructor of their subclasses both
	mixins and for normal use'''

	def __new__(cls, name, bases, attrs):
		mixins, bases = split_on(bases,
			lambda x: tryattr(x, 'metaclass') == mixin)
		attrs['mixins'] = mixins
		for m in mixins:
			trying(m._metanew_, (cls, name, bases, attrs))
			except AttributeError: pass
		for m in mixins:
			try: m._metainit_(cls, name, bases, attrs)
			except AttributeError: pass
		if not bases: attrs['metaclass'] = mixin #TODO: examine

		return type(name, bases, attrs)
