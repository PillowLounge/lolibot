# Persistent storage

debug = False
validate_params = False
################################################################################

class StructBase(object):
	pass

def struct(name, slots):
	slots = tuple(slots)
	def _init_(self, *args):
		for slot, arg in zip(slots, args): setattr(self, slot, arg)
	return type(name, (StructBase,), {
		'__slots__': slots,
		'__init__' : _init_
	})

def metaclassmethod(fcn):
	return classmethod(fcn)

################################################################################
# Adapter for sqlite3

class Sqlite3_adapter(object):
	'''The interface for creating and manipulating a struct of data for easy
	storage to disc'''

	def __init__(self):
		self.fields = []

	def add(self, field, metadata):
		affinity = if 'type' in metadata (
			' integer' if metadata['type'] == int   else \
			' real'    if metadata['type'] == float else \
			' text'    if metadata['type'] == str   else '') else ''
		self.fields.append((field, affinity))

	def done(self):
		self.sql_create = self.create_table(fields)

	def create_table(name, fields):
		return 'CREATE TABLE {} ({})'.format(name,
			', '.join(key + affinity for key, affinity in fields)
		)

################################################################################

class Layered(metaclass=mixin):
	'''Separates data and access/manipulation. Makes the subclass a taylored
	manager for a POCO like data object storing the state'''

	@metaclassmethod
	def _metanew_(cls, name, bases, attrs):
		if 'persistent_storage' in attrs:
			pass
		if '_properties_' in attrs:
			props = attrs['_properties_']
			for key,val in props.items():
				pass
			Data = struct(name +'Data', props.keys())

################################################################################

class Serializable(metaclass=mixin):
	'''Provides the ability to serialize the object's state'''
	pass

################################################################################
# MIXIN: [Persistent]

class Persistent(Serializable):
	'''Allows the object state to be initialized from, stored and synchronized
	to disk using sqlite3, shelve or any custom framework
	TODO: create an __init__ for storing data to disk on instantiation
	TODO: create properties that listen for changes to data
	TODO: specify interface standars for adapting storage libraries'''

	default = Sqlite3_adapter

	def _metanew_(cls, name, bases, attrs):

		if validate_params:
			assert type(cls) is type
			assert type(name) is str
			assert type(bases) in (tuple, list)
			assert type(attrs) is dict

		if 'persistent_storage' not in attrs:
			attrs['persistent_storage'] = Persistent.default
		adapter = attrs['persistent_storage']()

		if '_properties_' not in attrs:
			attrs['_properties_'] = {}
		for key,val in attrs['_properties_']: adapter.add(key, val)
		adapter.done()

################################################################################

class Subscribable(metaclass=mixin):

	@metaclassmethod
	def _metanew_(cls, name, bases, attrs):

		if '_properties_' in attrs:
			for key,val in attrs['_properties_']:
				pass

	def event(self, fcn): pass

################################################################################

class User(Layered, Persistent, Subscribable, object): pass

class Message(Layered, Persistent, Subscribable, object):

	_properties_ = {
		'id'      : {'type': int,  'tags': ('static', 'unique')},
		'author'  : {'type': User, 'tags': ('static')},
		'datetime': {'type': int,  'tags': ('static')},
		'content' : {'type': str},
		'history' : {'type': Subscribable.history}
	}
	persistent_storage = Sqlite3_adapter

	def __cmp__(self, other): return cmp(self.datetime, other.datetime)

	def __set__(self, value):
		if type(value) is str: self.content = value

	def __str__(self): return self.content

def dynamic_property(fcn):
	return property(fcn)

################################################################################

conn = sqlite3.connect(':memory:')

c = conn.cursor()

def eventlog_for(namedtuple):

	def handler():
		sql = 'INSERT INTO {} VALUES ({})'.format(
			namedtuple.__class__.__name__,
			', '.join(key + typ for key,typ in zip(
				(f for f in namedtuple.__class__._fields),
				(' integer' if val.__class__ == int   else \
				' real'     if val.__class__ == float else \
				' text'     if val.__class__ == str   else ''
				for val in namedtuple)
			))
		)

c.execute(sql)
