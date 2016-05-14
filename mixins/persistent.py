# Persistent storage

import sqlite3

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

################################################################################

def metaclassmethod(fcn):
	return classmethod(fcn)

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

def create_table_for(namedtuple):
	return 'CREATE TABLE {} ({})'.format(
		namedtuple.__class__.__name__,
		', '.join(key + typ for key,typ in zip(
			(f for f in namedtuple.__class__._fields),
			(' integer' if val.__class__ == int   else \
			' real'     if val.__class__ == float else \
			' text'     if val.__class__ == str   else ''
			for val in namedtuple)
		))
	)

class Persistent(Serializable):
	'''Allows the object state to be initialized from, stored and synchronized
	to disk using sqlite3, shelve or any custom format
	TODO: create an __init__ for storing data to disk on instantiation
	TODO: create properties that listen for changes to data
	TODO: '''

	default = 'sqlite3'

	def _metanew_(cls, name, bases, attrs):
		if not 'persistent_storage' in attrs:
			import sqlite3
			attrs['persistent_storage'] = sqlite3
		if '_properties_' in attrs:
			for key,val in attrs['_properties_']:
				pass
			sql = create_table_for(namedtuple)

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
	persistent_storage = sqlite3

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
