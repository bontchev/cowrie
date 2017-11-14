# How to send Cowrie output to MySQL database

## Prerequisites

* Working Cowrie installation
* Working MySQL database

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

## mySQL configuration

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

