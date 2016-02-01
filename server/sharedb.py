#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import signal
import time
import json
import sqlite3
import threading

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from StringIO import StringIO

# restrict to a particular path
class RequestHandler(SimpleXMLRPCRequestHandler):
	rpc_paths = ('/RPC2',)

# database handling
class SharedDB:

	db_optimizations = [
		'pragma temp_store=memory;',
		'pragma journal_mode=memory;',
		'pragma foreign_keys=on;',
		'pragma synchronous=off;',
		'pragma default_cache_size=10000;',
		'pragma jlocking_mode=exclusive;'
	]

	absolute_path = os.path.dirname(os.path.realpath(__file__))

	def __init__(self, config):

		signal.signal(signal.SIGINT, self._signal_handler)

		self._config = config
		self._db = sqlite3.connect(':memory:', check_same_thread=False)
		self._db.text_factory = str
		self._db.row_factory = self._dict_factory
		self._cursor = self._db.cursor()
		self._started = int(time.time())

		# initializing schemas
		self._initialize_schemas()

		# optimization tweaks
		# todo: check if this optimizations corrupt data
		for optmization in self.db_optimizations:
			self._cursor.execute(optmization)

		# initializing persistent backup worker
		self.persistent_timer = threading.Timer(int(self._config['persistent_timeout']), self._copy_to_persistent)
		self.persistent_timer.start()

		print '>>', self._current_datetime(), '>> starting sharedb server on', config['host'] + ':' + str(config['port'])

	# restores or freshly initializes schemas
	def _initialize_schemas(self):
		print '>> initializing schemas'

		persistant_file = os.path.isfile(self.absolute_path + '/persistent/persistent.db')
		for schema in self._config['schemas']:

			attributes = []
			for attr in schema['attributes']:
				attributes.append(' '.join(attr))

			if int(schema['persistent']) and persistant_file:
				# copies data from persisten database
				self._cursor.execute('attach database "' + self.absolute_path + '/persistent/persistent.db" as persistent;')
				self._cursor.execute('create virtual table ' + schema['name'] + ' using fts4 (' + ','.join(attributes) + ');')
				self._cursor.execute('insert into ' + schema['name'] + ' select * from persistent.' + schema['name'] + ';')
				self._cursor.execute('detach database persistent;')
			else:
				# creates new empty virtual table
				self._cursor.execute('create virtual table ' + schema['name'] + ' using fts4 (' + ','.join(attributes) + ');')

		self._db.commit()
		print '>>', self._current_datetime(), '>> persistent database restored to memory'

	# associative result addressing from query
	def _dict_factory(self, cursor, row):
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		return d

	def _current_datetime(self):
		return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())

	def _signal_handler(self, signal, frame):
		self.persistent_timer.cancel()
		print 'exiting ...'
		sys.exit(0)

	# copies in-memory schemas to local file / persistent storage
	def _copy_to_persistent(self):
		persistent_schemas = []
		for schema in self._config['schemas']:
			if int(schema['persistent']):
				persistent_schemas.append(schema)

		if len(persistent_schemas) > 0:
			if os.path.isfile(self.absolute_path + '/persistent/persistent.db'):
				os.rename(self.absolute_path + '/persistent/persistent.db', self.absolute_path + '/persistent/persistent.db.bak')
			self._cursor.execute('attach database "' + self.absolute_path + '/persistent/persistent.db" as persistent;')

			for schema in persistent_schemas:
				attributes = []
				for attr in schema['attributes']:
					attributes.append(' '.join(attr))

				# fixme: bad cpu usage / performance when exporting
				self._cursor.execute('create virtual table persistent.' + schema['name'] + ' using fts4 (' + ','.join(attributes) + ');')
				self._cursor.execute('insert into persistent.' + schema['name'] + ' select * from ' + schema['name'] + ';')

			self._cursor.execute('detach database persistent;')
			self._db.commit()

			print '>>', self._current_datetime(), '>> memory database stored locally'

		# reinitialize persistent backup worker
		self.persistent_timer = threading.Timer(int(self._config['persistent_timeout']), self._copy_to_persistent)
		self.persistent_timer.start()

	# returns basic server info
	def info(self):
		m, s = divmod((int(time.time()) - self._started), 60)
		h, m = divmod(m, 60)
		return {
			'status': 200,
			'version': self._config['version'],
			'uptime': '%d:%02d:%02d' % (h, m, s)
		}

	# returns available schemas
	def get_available_schemas(self):
		try:
			self._cursor.execute('select name from sqlite_master where type="table";')
			return {
				'status': 200,
				'data': self._cursor.fetchall()
			}
		except sqlite3.OperationalError, e:
			return { 'status': 400 }

	# sql query and returns associative array
	def query(self, query_string):
		try:
			self._cursor.execute(query_string)
			self._db.commit()
			return {
				'status': 200,
				'data': self._cursor.fetchall()
			}
		except sqlite3.OperationalError, e:
			return { 'status': 400 }


if __name__ == '__main__':

	try:
		with open(os.path.dirname(os.path.realpath(__file__)) + '/config.json') as config_file:
			config = json.load(config_file)
			server = SimpleXMLRPCServer(
				(config['host'], int(config['port'])),
				requestHandler = RequestHandler,
				logRequests = int(config['logging'])
			)
			server.register_introspection_functions()
			server.register_instance(SharedDB(config))
			server.serve_forever()

	except Exception, e:
		print '>>', time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()), '>> fatal error:', e

