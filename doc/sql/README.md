# How to Send Cowrie Output to a MySQL Database


## Prerequisites

* Working Cowrie installation
* MySQL Server installation


## Installation

```
$ sudo add-apt-repository ppa:maxmind/ppa
$ sudo apt-get update
$ sudo apt-get install python-mysqldb libmysqlclient-dev geoipupdate
$ sudo su - cowrie
$ cd cowrie
$ source ./cowrie-env/bin/activate
$ easy_install hashlib
$ pip install MySQL-python
$ deactivate
```

Inspect the file `~/cowrie/data/GeoIP.conf` and check that the configuration options `DatabaseDirectory` and `LockFile` point to correct (existing) paths. Then download the latest version of the Maxmind geolocation databases:

```
$ geoipupdate -f ~/cowrie/data/GeoIP.conf
```

To have the database updated automatically (it is updated every second Tuesday
of each month, so download it every second Wednesday), create a crontab job
(`crontab -e`) and enter the following:

```
# Update the geoIP database at midnight on the 2nd Wednesday of each month:
0 0 8-14 * * [ $(/bin/date +\%u) -eq 3 ] && /usr/bin/geoipupdate -f /home/cowrie/cowrie/data/GeoIP.conf
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

Please note that leaving `store_input` set to `true` stores an extensive amount of information (basically, every command executed by every attacker) into one of the MySQL tables (the one named `input`). A year's worth of data can easily cause this table to become hundreds of millions of rows and dozens of gigabytes large and to chocke down your server. Unless you _really_ need to collect this information, it is advisable to set `store_input` to `false`. It is set to `true` by default for compatibility with previous versions of Cowrie, which did not have such a setting and always collected the data.


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
