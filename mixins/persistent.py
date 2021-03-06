# Persistent storage

# 2016-06-04 moving away from normal "class Foo():" notation
# and we're making a class factory instead

# conventions:
# MyClass.none returns a null-object
# mixins: Archive / Identify / Persist
# Identifiable objects have:
# .id / .memid / .serverid / .clientid / .localid / .remoteid / .uuid (128b)
# provides integer, string or bytes, unique to what the instance represents
# Archiving objects have:
# .timelast(action) / .history

import shelve
from mixin import mixin, tryattr, trykey, replace
import datetime
import bisect
from dateutil.rrule import rrule, MINUTELY

log_debug = True
validate  = True

################################################################################

class ClassFactory(object):

	def __init__(self, name, doc):
		pass

	def addProperty(self, name, **kwargs):
		self.properties[name] = kwargs

	def addMixin(self, mixin): pass

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
	storage to disc
	INSTANCES: One for every type stored to disc'''

	def __init__(self, cls, ignore=()):
		self.type   = cls
		self.name   = name
		self.slots  = cls.__slots__ #TODO: account for __dict__ use
		#TODO: account for '?' in slot names
		#TODO: use the ignore var
		self.cursor = None
		self.table_name = None
		self.primary = None

	def add(self, field, metadata):
		field_type = trykey(metadata, 'type')
		affinity = \
			' integer' if field_type == int   else \
			' real'    if field_type == float else \
			' text'    if field_type == str   else ''
		self.fields.append((field, affinity))

	def done(self):
		#TODO: resolve reference to a proper sql_create_table
		self.sql_create = sql_create_table(self.name, self.fields)

	def create_updater(self, key):
		sql = sql_insert(self.name +'_'+ key, '??')
		def updater(obj, values):
			#TODO: generate proper update handler on first usage and replace
			# itself with proper handler
			obj._sqlcursor_.execute(sql, values)
		return updater

	def append(self, obj):
		'''synchronize given object to database. If key collides, update'''
		if validate: assert type(obj) is self.type
		self[obj.id] = obj

	def __getitem__(self, _key):
		'''fetch an item from disc with the given id
		RAISES: KeyError if key does not exist'''

		if validate: assert type(self) is Sqlite3_adapter
		sql = Sqlite3_adapter.sql_select(self.table_name, self.primary, '?')
		@replace(self, '__getitem__')
		def getitem(key):
			#TODO: raise TypeError if key is not the right type
			result = self.cursor.execute(sql, (str(key),))
			if not result: raise KeyError
			return self.type(**result)
		return getitem(_key)

	def __setitem__(self, _key, _value):
		'''save or update an item on disc. Key represents the primary key'''

		if validate: assert type(self) is Sqlite3_adapter
		slots = {}
		for s in self.slots: slots[s] = '?'
		sql_upd = Sqlite3_adapter.sql_update(
			self.table_name, slots, self.primary +'=?')
		sql_ins = Sqlite3_adapter.sql_insert(self.table_name, '?'*len(slots))
		@replace(self, '__setitem__')
		def setitem(key, value):
			c = self.cursor
			value = value._state_()
			if log_debug: print(sql_upd, value)
			c.execute(sql_upd, (value, key))
			if c.rowcount <= 0:
				if log_debug: print(sql_ins, value)
				c.execute(sql_ins, (value,))
			c.commit()
		return setitem(_key, _value)

	@staticmethod
	def sql_create_table(table, fields):
		return 'CREATE TABLE {} ({})'.format(table,
			', '.join(key + affinity for key, affinity in fields))

	@staticmethod
	def sql_insert(table, values):
		return 'INSERT INTO {} VALUES ({})'.format(table, ', '.join(values))

	@staticmethod
	def sql_update(table, assign, predicate):
		return 'UPDATE {} SET {} WHERE {}'.format(table,
			', '.join(key +'='+ val for key,val in assign), predicate)

	@staticmethod
	def sql_select(table, key, predicate):
		return 'SELECT * FROM {} WHERE {}'.format(table, key)

################################################################################
# Adapter for shelve

# concerns:
# delegate stored elements to separate files deterministicly
# pick a naming scheme for files
# store and retrieve content

def shelve_adapter(cls):

	def filenamescheme(self):
		#TODO: assert Archiving
		date = self.timelast('created').date()
		return str(date) + filename + '.shelve'

	# callable from both class and instance
	def persistent_resource(self, format='shelve'):
		if issubclass(self.__class__, cls):
			selfid = self.id #TODO: assert Identifiable
		else:
			selfid = self #TODO: assert valid id types

		return filenamescheme(selfid)

	def get(id=None, memid=None, uuid=None):
		if id is None:
			#TODO: pass cls as argument to work with inheritance
			try: return cls.none # does the class provide a null-object?
			except AttributeError: return None

	cls.persistent_resource = persistent_resource
	cls.get = staticmethod(get)

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
	to disk using sqlite3, shelve or any custom framework.
	INSTANCES: None! It is used as a namespace only.
	TODO: create an __init__ for storing data to disk on instantiation
	TODO: create properties that listen for changes to data
	TODO: specify interface standars for adapting storage libraries'''

	default = Sqlite3_adapter

	def _metanew_(cls, name, bases, attrs):
		if validate: Persistent.validate_params(cls, name, bases, attrs)

		adapter = trykey(attrs, 'persistent_storage')
		if validate: adapter = Persistent.validate_adapter(adapter)
		adapter = adapter(name) #instantiation

		if '_properties_' not in attrs:
			attrs['_properties_'] = {}
		for key,val in attrs['_properties_']:
			adapter.add(key, val)
			val['set'].append(adapter.eventlog_setter)
		adapter.done()

	@staticmethod
	def validate_params(cls, name, bases, attrs):
		assert type(cls)   is type
		assert type(name)  is str
		assert type(bases) in (tuple, list)
		assert type(attrs) is dict

	@staticmethod
	def validate_adapter(adapt_cls):
		if adapt_cls is None:
			#TODO: issue notice
			adapt_cls = Persistent.default
		adapt_cls = attrs['persistent_storage']
		assert type(adapt_cls) is type
		assert 'add'  in adapt_cls
		assert 'done' in adapt_cls
		return adapt_cls

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
	'''An instance of this class can be used as a manager where the underlying
	object state is a dynamic context operated on or as one instance per state'''

	# one to many relationships, not-null
	#_source_context_ = {
	#	'author'  : {'type': User,    'tags': ('static',)},
	#	'channel' : {'type': Channel, 'tags': ('static',)}
	#}

	# one to one relationships
	_props_ = {
		'id'      : {'type': int, 'tags': ('static', 'id')},
		'localid' : {'type': int, 'tags': ('static', 'id')},
		'time'    : {'type': int, 'tags': ('static',)},
		'content' : {'type': str, 'tags': ('main',)},
		'history' : {'type': 'history'}
	}

	_properties_ = {
		'id'      : {'type': int,     'tags': ('static', 'id')},
		'channel' : {'type': Channel, 'tags': ('static',)},
		'author'  : {'type': User,    'tags': ('static',)},
		'datetime': {'type': int,     'tags': ('static',)},
		'content' : {'type': str,     'tags': ('main',)},
		'history' : {'type': 'history'}
	}
	persistent_storage = Sqlite3_adapter

	def __cmp__(self, other): return cmp(self.datetime, other.datetime)

	def __set__(self, value):
		if type(value) is str: self.content = value

	def __str__(self): return self.content

def dynamic_property(fcn):
	return property(fcn)

# same thing, using ClassFactory

cf = ClassFactory('Message',
	doc='''An instance of this class can be used as a manager where the underlying
	object state is a dynamic context operated on or as one instance per state''',
	mixins=[Layered, Persistent, Subscribable])
cf.addProperty('id',   int)
cf.addProperty('time', int)
cf.addProperty('content', str) # content or value auto referenced by __str__?
Message = cf.create()


################################################################################

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

if __name__ == '__main__':
	print(dir(Message))
	print(Message.mixins)
	print(Message.default)
