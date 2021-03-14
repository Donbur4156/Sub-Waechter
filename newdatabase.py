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
connection.close()
