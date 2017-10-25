# How to send Cowrie output to MySQL database

## Prerequisites

* Working Cowrie installation
* Working MySQL database

## Installation

```
sudo apt-get install python-mysqldb libmysqlclient-dev
su - cowrie
source cowrie/cowrie-env/bin/activate
pip install MySQL-python
```

## mySQL configuration

First create the database and grant access to the Cowrie user account:
```
mysql -u root -p
CREATE DATABASE IF NOT EXISTS cowrie;
CREATE USER IF NOT EXISTS 'cowrie'@'localhost' IDENTIFIED BY 'PASSWORD HERE' PASSWORD EXPIRE NEVER;
GRANT ALTER, ALTER ROUTINE, CREATE, CREATE ROUTINE, CREATE TEMPORARY TABLES, CREATE VIEW, DELETE, DROP, EXECUTE,FILE, INDEX, INSERT, LOCK TABLES, RELOAD, SELECT, SHOW DATABASES, SHOW VIEW, TRIGGER, UPDATE ON cowrie TO 'cowrie'@'localhost';
FLUSH PRIVILEGES;
exit
```

Next load the database schema:
```
cd /home/cowrie/cowrie/
mysql -u cowrie -p
USE cowrie;
source ./doc/sql/mysql.sql;
exit
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

