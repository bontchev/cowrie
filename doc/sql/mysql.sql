CREATE TABLE IF NOT EXISTS `auth` (
  `id` int(11) NOT NULL auto_increment,
  `session` char(32) NOT NULL,
  `success` tinyint(1) NOT NULL,
  `username` varchar(100) NOT NULL,
  `password` varchar(100) NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `pwd_idx` (`timestamp`, `password`)
) ;

CREATE TABLE IF NOT EXISTS `clients` (
  `id` int(4) NOT NULL auto_increment,
  `version` varchar(80) NOT NULL,
  UNIQUE (`version`),
  PRIMARY KEY (`id`)
) ;

CREATE TABLE IF NOT EXISTS `input` (
  `id` int(11) NOT NULL auto_increment,
  `session` char(32) NOT NULL,
  `timestamp` datetime NOT NULL,
  `realm` varchar(50) default NULL,
  `success` tinyint(1) default NULL,
  `input` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `session` (`session`,`timestamp`,`realm`),
  KEY `input_idx` (`timestamp`, `input`)
) ;

CREATE TABLE IF NOT EXISTS `commands` (
  `id` int(11) NOT NULL auto_increment,
  `input` varchar(3000) CHARACTER SET ascii COLLATE ascii_general_ci NOT NULL,
  `inputhash` varchar(66),
  PRIMARY KEY (`id`),
  UNIQUE (`inputhash`)
) ;

CREATE TABLE IF NOT EXISTS `sensors` (
  `id` int(11) NOT NULL auto_increment,
  `ip` varchar(255) NOT NULL,
  UNIQUE (`ip`),
  PRIMARY KEY  (`id`)
) ;

CREATE TABLE IF NOT EXISTS `sessions` (
  `id` char(32) NOT NULL,
  `starttime` datetime NOT NULL,
  `endtime` datetime default NULL,
  `sensor` int(4) NOT NULL,
  `ip` varchar(15) NOT NULL default '',
  `termsize` varchar(7) default NULL,
  `client` int(4) default NULL,
  `port` int(5) NOT NULL,
  `country_name` varchar(45) default '',
  `country_iso_code` varchar(2) default '',
  `city_name` varchar(128) default '',
  `org` varchar(128) default '',
  `latitude` float,
  `longitude` float,
  `geohash` varchar(30),
  PRIMARY KEY (`id`),
  KEY `starttime` (`starttime`, `sensor`),
  KEY `ip_idx` (`starttime`, `ip`),
  KEY `cname_idx` (`starttime`, `country_name`),
  KEY `ccode_idx` (`starttime`, `country_iso_code`),
  KEY `org_idx` (`starttime`, `org`)
) ;

CREATE TABLE IF NOT EXISTS `ttylog` (
  `id` int(11) NOT NULL auto_increment,
  `session` char(32) NOT NULL,
  `ttylog` varchar(100) NOT NULL,
  `size` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ;

CREATE TABLE IF NOT EXISTS `downloads` (
  `id` int(11) NOT NULL auto_increment,
  `session` CHAR( 32 ) NOT NULL,
  `timestamp` datetime NOT NULL,
  `url` text NOT NULL,
  `outfile` text default NULL,
  `shasum` varchar(64) default NULL,
  PRIMARY KEY (`id`),
  KEY `session` (`session`,`timestamp`),
  KEY (`timestamp`)
) ;

CREATE TABLE IF NOT EXISTS `keyfingerprints` (
  `id` int(11) NOT NULL auto_increment,
  `session` CHAR( 32 ) NOT NULL,
  `username` varchar(100) NOT NULL,
  `fingerprint` varchar(100) NOT NULL,
  UNIQUE (`fingerprint`),
  PRIMARY KEY (`id`)
) ;

CREATE TABLE IF NOT EXISTS `params` (
  `id` int(11) NOT NULL auto_increment,
  `session` CHAR( 32 ) NOT NULL,
  `arch` varchar(32) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `arch_index` (`arch`)
) ;

