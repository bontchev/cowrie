# How to Send Cowrie Output to a MySQL Database


## Prerequisites

* Working Cowrie installation
* MySQL Server installation


## Installation

```
$ sudo apt-get install python-mysqldb libmysqlclient-dev
$ sudo su - cowrie
$ cd cowrie
$ source ./cowrie-env/bin/activate
$ easy_install hashlib
$ pip install MySQL-python
$ deactivate
$ cd data
$ wget http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz
$ gzip -df GeoLite2-City.mmdb.gz
$ cd ..
```

To have the database updated automatically (it is updated every second Tuesday
of each month, so download it every second Wednesday), create a crontab job
(`crontab -e`) and enter the following:

```
# Update the geoIP database at midnight on the 2nd Wednesday of each month:
0 0 * * 3 [ `/bin/date +\%d` -le 7 ] && cd /home/cowrie/cowrie/data && /usr/bin/wget -q http://geolite.maxmind.com/       download/geoip/database/GeoLite2-City.mmdb.gz && /bin/gzip -df GeoLite2-City.mmdb.gz
```

## MySQL Configuration

First create the database and grant access to the Cowrie user account:
```
$ mysql -p -u root
MySQL> CREATE DATABASE IF NOT EXISTS cowrie;
MySQL> CREATE USER IF NOT EXISTS 'cowrie'@'localhost' IDENTIFIED BY 'PASSWORD HERE' PASSWORD EXPIRE NEVER;
MySQL> GRANT ALTER, ALTER ROUTINE, CREATE, CREATE ROUTINE, CREATE TEMPORARY TABLES, CREATE VIEW, DELETE, DROP, EXECUTE,FILE, INDEX, INSERT, LOCK TABLES, RELOAD, SELECT, SHOW DATABASES, SHOW VIEW, TRIGGER, UPDATE ON cowrie TO 'cowrie'@'localhost';
MySQL> FLUSH PRIVILEGES;
MySQL> exit
```

Next load the database schema:
```
$ cd /home/cowrie/cowrie/
$ mysql -p -u cowrie cowrie
MySQL> source ./doc/sql/mysql.sql;
MySQL> exit
```

## cowrie configuration

* Add the following entries to ~/cowrie/cowrie.cfg

```
[output_mysql]
host = localhost
database = cowrie
username = cowrie
password = PASSWORD HERE
port = 3306
store_input = true
debug = false
```


## Restart Cowrie

```
$ cd ~/cowrie/bin/
$ ./cowrie restart
```


## Verify That the MySQL Output Engine Has Been Loaded

Check the end of the ~/cowrie/log/cowrie.log to make sure that the MySQL output engine has loaded successfully.
```
$ cd ~/cowrie/log/
$ tail cowrie.log
```

Example expected output:
```
2017-11-27T22:19:44-0600 [-] Loaded output engine: jsonlog
2017-11-27T22:19:44-0600 [-] Loaded output engine: mysql
...
2017-11-27T22:19:58-0600 [-] Ready to accept SSH connections

```


## Confirm That Events are Logged to the MySQL Database
Wait patiently for a new login attempt to occur.  Use tail like before to quickly check if any activity has 
been recorded in the cowrie.log file.

Once a login event has occurred, log back into the MySQL database and verify that the event was recorded:

```
$ mysql -u cowrie -p
USE cowrie;
SELECT * FROM auth;
```

Example output:
```
+----+--------------+---------+----------+-------------+---------------------+
| id | session      | success | username | password    | timestamp           |
+----+--------------+---------+----------+-------------+---------------------+
|  1 | a551c0a74e06 |       0 | root     | 12345       | 2017-11-27 23:15:56 |
|  2 | a551c0a74e06 |       0 | root     | seiko2005   | 2017-11-27 23:15:58 |
|  3 | a551c0a74e06 |       0 | root     | anko        | 2017-11-27 23:15:59 |
|  4 | a551c0a74e06 |       0 | root     | 123456      | 2017-11-27 23:16:00 |
|  5 | a551c0a74e06 |       0 | root     | dreambox    | 2017-11-27 23:16:01 |
...
```
