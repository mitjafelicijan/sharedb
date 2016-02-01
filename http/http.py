#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import bottle
import xmlrpclib

try:
	sharedb = xmlrpclib.ServerProxy('http://localhost:51234')
except Exception, e:
	print '>> fatal error:', e
	sys.exit(1)

# default route
@bottle.route('/')
def index():

	query = ''
	results = []
	se = '0.000000 seconds'

	if 'query' in dict(bottle.request.query):
		query = str(bottle.request.query['query'])
		print query
		if query != '':
			st = time.time()
			for item in sharedb.query(query)['data']:
				results.append(item)
			se = '%.6f seconds' % (time.time() - st)
	return bottle.template('default',
		schemas = sharedb.get_available_schemas(),
		info = sharedb.info(),
		query = query,
		results = results if results else [],
		keys = results[0].keys() if len(results) > 0 else [],
		se = se
	)


# run simple web server
bottle.debug(True)
bottle.run(host='0.0.0.0', port=8000, reloader=True)
