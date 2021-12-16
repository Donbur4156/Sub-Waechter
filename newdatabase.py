import os
import sqlite3
import config
import sys


if os.path.exists(config.database):
    print("Datei bereits vorhanden")
    sys.exit(0)

connection = sqlite3.connect(config.database)
cursor = connection.cursor()

sql = "CREATE TABLE lichesssub(" \
      "discordtag TEXT," \
      "lichessid TEXT," \
      "twitch INTEGER," \
      "patreon INTEGER," \
      "discordid INTEGER)"
cursor.execute(sql)

sql = "CREATE TABLE config(" \
      "serverid INTEGER," \
      "password TEXT)"
cursor.execute(sql)

sql = "CREATE TABLE usernotes(" \
	"id INTEGER PRIMARY KEY," \
	"date TEXT," \
	"discordid INTEGER," \
	"moddiscordid INTEGER," \
	"note TEXT)"
cursor.execute(sql)


connection.close()
