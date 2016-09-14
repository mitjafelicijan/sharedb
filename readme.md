# sqlite-xmlrpc - network accessible sql database


## Overview

sqlite-xmlrpc is intended to be used as a network enabled caching database. SQL 
language supported gives user extendability necessary to perform higher 
functions like full-text search and pattern matching.

sqlite-xmlrpc uses XMLRPC to communicate with other processes and completely 
isolated from main client applications. Only couple of method are 
available publicly to clients.

With standard configuration sqlite-xmlrpc has disabled remote connections but 
this can be changed by editing config file.

Because sqlite-xmlrpc runs completely in memory you will loose data when 
server is restarted. So that is why data persistence was integrated 
into service. If schema is data persistent then every n-minutes this 
scheme will be written/backed-up to disk. This functionality is 
configurable in config file.


## Installation

sqlite-xmlrpc heavily relies on Sqlite3 so in order to install you must first
install sqlite3 package from repository.

```
  $ sudo apt install sqlite3
```

Then download Debian package can install (currently supports only amd64).

```
  $ wget http://mitjafelicijan.github.io/dist/sharedb_1.0-0.deb
  $ sudo dpkg -i sharedb_1.0-0.deb
```

After installation is complete new systemd service is exposed to 
operating system. To start sqlite-xmlrpc start service via systemd.

```
  $ sudo service sharedb start
  $ sudo service sharedb status
  $ sudo service sharedb stop
```



## Schema definition

When server is started configuration file (config.json) is read and
schemas are created based on a definition.

Every schema has columns or attributes. This extends functionality
of classic Key/Value datastores. This is the reason it is called
wide-column datastore.

You can use multiple schemas with one server.

If schema is persisten (persistance: true) then contents of schema 
is periodically written to disk and loaded on server start.




## Available schema datatypes

  - integer (signed integer)
  - real (floating point value)
  - text (utf-8 text string)
  - blob (data, stored exactly as it was input)

  * Dates are represented as Unix timestamp integer value.
  * Booleans are represented as [0, 1] integer value.
  * Blobs can be used to store hex values etc.




## Server configuration

Server configuration is located in /opt/sharedb/config.json.

```
  persistent_timeout: 3600
    interval on which memory data is 
    written to disk to ensure data
    persistance (in seconds)

  persistent: false
    if this attribute is set to true than
    this schema will be backed up
    if set to false schema will reinitilize
    empty on server restart

  host: 127.0.0.1
    to enable remote connections change ip
    to 0.0.0.0
```



## Response status codes

For every request there is a response with field status. Status
codes are compliant on RFC 7231 standard.
https://tools.ietf.org/html/rfc7231

Status used by server:

```
  200 ... Ok
  400 ... Bad Request (query malformed)
```


## Search patterns and best practices

ShareDB uses in-memory style database with virtual tables so you can 
use "match" technique for full-text.

* Like statement is also supported but is significantly slower than match.
* The Like operator does a pattern matching comparison.

Example of "like" query:

```
  select * from cities where name like 'oregon' limit 1;
  -- matches oregon word

  select * from cities where name like '%rego%' limit 1;
  -- matches every string with "rego" substring regardless of position
```

Example of "match" query (very fast and non cpu intensive):

```
  select * from cities where name match 'oregon' limit 1;
  -- matches exctact oregon word in sentance

  select * from cities where name match 'oreg*' limit 1;
  -- matches prefix of "oreg" word in sentance
```
