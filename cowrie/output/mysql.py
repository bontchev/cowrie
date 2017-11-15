
"""
MySQL output connector. Writes audit logs to MySQL database
"""

from __future__ import division, absolute_import

import MySQLdb

import geoip2.database
import Geohash
import hashlib

from twisted.internet import defer
from twisted.enterprise import adbapi
from twisted.python import log

import cowrie.core.output

class ReconnectingConnectionPool(adbapi.ConnectionPool):
    """
    Reconnecting adbapi connection pool for MySQL.

    This class improves on the solution posted at
    http://www.gelens.org/2008/09/12/reinitializing-twisted-connectionpool/
    by checking exceptions by error code and only disconnecting the current
    connection instead of all of them.

    Also see:
    http://twistedmatrix.com/pipermail/twisted-python/2009-July/020007.html
    """
    def _runInteraction(self, interaction, *args, **kw):
        try:
            return adbapi.ConnectionPool._runInteraction(
                self, interaction, *args, **kw)
        except MySQLdb.OperationalError as e:
            if e[0] not in (2003, 2006, 2013):
                raise log.msg("RCP: got error %s, retrying operation" %(e,))
            conn = self.connections.get(self.threadID())
            self.disconnect(conn)
            # Try the interaction again
            return adbapi.ConnectionPool._runInteraction(
                self, interaction, *args, **kw)



class Output(cowrie.core.output.Output):
    """
    docstring here
    """
    debug = False
    db = None
    reader = None
    store_input = True

    def __init__(self, cfg):
        self.cfg = cfg
        self.geoipdb = '{}/GeoLite2-City.mmdb'.format(cfg.get('honeypot', 'data_path'))
        cowrie.core.output.Output.__init__(self, cfg)


    def start(self):
        """
        docstring here
        """
        try:
            self.reader = geoip2.database.Reader(self.geoipdb)
        except Exception as e:
            log.msg("could not open GeoIP database file " + self.geoipdb + ".")
        if self.cfg.has_option('output_mysql', 'debug'):
            self.debug = self.cfg.getboolean('output_mysql', 'debug')
        if self.cfg.has_option('output_mysql', 'store_input'):
            self.store_input = self.cfg.getboolean('output_mysql', 'store_input')

        if self.cfg.has_option('output_mysql', 'port'):
            port = int(self.cfg.get('output_mysql', 'port'))
        else:
            port = 3306
        try:
            self.db = ReconnectingConnectionPool('MySQLdb',
                host = self.cfg.get('output_mysql', 'host'),
                db = self.cfg.get('output_mysql', 'database'),
                user = self.cfg.get('output_mysql', 'username'),
                passwd = self.cfg.get('output_mysql', 'password'),
                port = port,
                cp_min = 1,
                cp_max = 1)
        except MySQLdb.Error as e:
            log.msg("output_mysql: Error %d: %s" % (e.args[0], e.args[1]))


    def stop(self):
        """
        docstring here
        """
        if self.reader is not None:
            self.reader.close()
        self.db.close()


    def sqlerror(self, error):
        """
        docstring here
        """
        log.err('output_mysql: MySQL Error: {}'.format(error.value))


    def simpleQuery(self, sql, args):
        """
        Just run a deferred sql query, only care about errors
        """
        if self.debug:
            log.msg("output_mysql: MySQL query: {} {}".format(sql, repr(args)))
        d = self.db.runQuery(sql, args)
        d.addErrback(self.sqlerror)


    @defer.inlineCallbacks
    def write(self, entry):
        """
        docstring here
        """

        if entry["eventid"] == 'cowrie.session.connect':
            r = yield self.db.runQuery(
                "SELECT `id` FROM `sensors` WHERE `ip` = %s", (self.sensor,))
            if r:
                sensorid = r[0][0]
            else:
                yield self.db.runQuery(
                    'INSERT INTO `sensors` (`ip`) VALUES (%s) ' +
                    'ON DUPLICATE KEY UPDATE `ip` = %s', (self.sensor, self.sensor,))
                r = yield self.db.runQuery('SELECT LAST_INSERT_ID()')
                sensorid = int(r[0][0])
            try:
                response = self.reader.city(entry["src_ip"])
                city = response.city.name
                if city is None:
                    city = ''
                country = response.country.name
                if country is None:
                    country = ''
                country_code = response.country.iso_code
                latitude = response.location.latitude
                longitude = response.location.longitude
            except:
                city = ''
                country = ''
                country_code = ''
                latitude = 0
                longitude = 0
            self.simpleQuery(
                'INSERT INTO `sessions` (`id`, `starttime`, `sensor`, `ip`, ' +
                '`port`, `country_name`, `country_iso_code`, `city_name`, `latitude`, ' +
                '`longitude`, `geohash`)' +
                ' VALUES (%s, FROM_UNIXTIME(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (entry["session"], entry["time"], sensorid, entry["src_ip"], entry["dst_port"],
                country.encode('utf8'), country_code, city.encode('utf8'),
                str(latitude), str(longitude), Geohash.encode(latitude, longitude)))
        elif entry["eventid"] == 'cowrie.login.success':
            self.simpleQuery('INSERT INTO `auth` (`session`, `success`' + \
                ', `username`, `password`, `timestamp`)' + \
                ' VALUES (%s, %s, %s, %s, FROM_UNIXTIME(%s))',
                (entry["session"], 1, entry['username'], entry['password'],
                entry["time"]))

        elif entry["eventid"] == 'cowrie.login.failed':
            self.simpleQuery('INSERT INTO `auth` (`session`, `success`' + \
                ', `username`, `password`, `timestamp`)' + \
                ' VALUES (%s, %s, %s, %s, FROM_UNIXTIME(%s))',
                (entry["session"], 0, entry['username'], entry['password'],
                entry["time"]))

        elif entry["eventid"] == 'cowrie.command.success':
            if self.store_input:
                shasum = hashlib.sha256(entry["input"]).hexdigest()
                r = yield self.db.runQuery(
                    'SELECT `id` FROM `commands` WHERE `inputhash` = %s', (shasum,))
                if r:
                    commandid = r[0][0]
                else:
                    yield self.db.runQuery(
                        'INSERT INTO `commands` (`input`, `inputhash`) VALUES (%s, %s) ' +
                        'ON DUPLICATE KEY UPDATE `inputhash` = %s', (entry["input"], shasum, shasum,))
                    r = yield self.db.runQuery('SELECT LAST_INSERT_ID()')
                    commandid = int(r[0][0])
                self.simpleQuery('INSERT INTO `input`' + \
                    ' (`session`, `timestamp`, `success`, `input`)' + \
                    ' VALUES (%s, FROM_UNIXTIME(%s), %s , %s)',
                    (entry["session"], entry["time"], 1, commandid))

        elif entry["eventid"] == 'cowrie.command.failed':
            if self.store_input:
                shasum = hashlib.sha256(entry["input"]).hexdigest()
                r = yield self.db.runQuery(
                    'SELECT `id` FROM `commands` WHERE `inputhash` = %s', (shasum,))
                if r:
                    commandid = r[0][0]
                else:
                    yield self.db.runQuery(
                        'INSERT INTO `commands` (`input`, `inputhash`) VALUES (%s, %s) ' +
                        'ON DUPLICATE KEY UPDATE `inputhash` = %s', (entry["input"], shasum, shasum,))
                    r = yield self.db.runQuery('SELECT LAST_INSERT_ID()')
                    commandid = int(r[0][0])
                self.simpleQuery('INSERT INTO `input`' + \
                    ' (`session`, `timestamp`, `success`, `input`)' + \
                    ' VALUES (%s, FROM_UNIXTIME(%s), %s , %s)',
                    (entry["session"], entry["time"], 0, commandid))

        elif entry["eventid"] == 'cowrie.session.file_download':
            self.simpleQuery('INSERT INTO `downloads`' + \
                ' (`session`, `timestamp`, `url`, `outfile`, `shasum`)' + \
                ' VALUES (%s, FROM_UNIXTIME(%s), %s, %s, %s)',
                (entry["session"], entry["time"],
                entry['url'], entry['outfile'], entry['shasum']))

        elif entry["eventid"] == 'cowrie.session.file_upload':
            self.simpleQuery('INSERT INTO `downloads`' + \
                ' (`session`, `timestamp`, `url`, `outfile`, `shasum`)' + \
                ' VALUES (%s, FROM_UNIXTIME(%s), %s, %s, %s)',
                (entry["session"], entry["time"],
                '', entry['outfile'], entry['shasum']))

        elif entry["eventid"] == 'cowrie.session.input':
            if self.store_input:
                shasum = hashlib.sha256(entry["input"]).hexdigest()
                r = yield self.db.runQuery(
                    'SELECT `id` FROM `commands` WHERE `inputhash` = %s', (shasum,))
                if r:
                    commandid = r[0][0]
                else:
                    yield self.db.runQuery(
                        'INSERT INTO `commands` (`input`, `inputhash`) VALUES (%s, %s) ' +
                        'ON DUPLICATE KEY UPDATE `inputhash` = %s', (entry["input"], shasum, shasum,))
                    r = yield self.db.runQuery('SELECT LAST_INSERT_ID()')
                    commandid = int(r[0][0])
                self.simpleQuery('INSERT INTO `input`' + \
                    ' (`session`, `timestamp`, `realm`, `input`)' + \
                    ' VALUES (%s, FROM_UNIXTIME(%s), %s , %s)',
                    (entry["session"], entry["time"],
                    entry["realm"], commandid))

        elif entry["eventid"] == 'cowrie.client.version':
            #self.simpleQuery('LOCK TABLES `clients` WRITE', '')
            r = yield self.db.runQuery(
                'SELECT `id` FROM `clients` WHERE `version` = %s', \
                (entry['version'],))
            if r:
                id = int(r[0][0])
            else:
                yield self.db.runQuery(
                    'INSERT INTO `clients` (`version`) VALUES (%s) ' +
                    'ON DUPLICATE KEY UPDATE `version`= %s', (entry['version'], \
                    entry['version'],))
                r = yield self.db.runQuery('SELECT LAST_INSERT_ID()')
                id = int(r[0][0])
            #self.simpleQuery('UNLOCK TABLES', '')
            self.simpleQuery(
                'UPDATE `sessions` SET `client` = %s WHERE `id` = %s',
                (id, entry["session"]))

        elif entry["eventid"] == 'cowrie.client.size':
            self.simpleQuery(
                'UPDATE `sessions` SET `termsize` = %s WHERE `id` = %s',
                ('%sx%s' % (entry['width'], entry['height']),
                    entry["session"]))

        elif entry["eventid"] == 'cowrie.session.closed':
            self.simpleQuery(
                'UPDATE `sessions` SET `endtime` = FROM_UNIXTIME(%s)' + \
                ' WHERE `id` = %s', (entry["time"], entry["session"]))

        elif entry["eventid"] == 'cowrie.log.closed':
            self.simpleQuery(
                'INSERT INTO `ttylog` (`session`, `ttylog`, `size`) VALUES (%s, %s, %s)',
                (entry["session"], entry["ttylog"], entry["size"]))

        elif entry["eventid"] == 'cowrie.client.fingerprint':
            self.simpleQuery(
                'INSERT INTO `keyfingerprints` (`session`, `username`, `fingerprint`) VALUES (%s, %s, %s) ' +
                'ON DUPLICATE KEY UPDATE `fingerprint` = %s',
                (entry["session"], entry["username"], entry["fingerprint"], entry["fingerprint"]))

