import requests
import json
import lichess.api
import config
import sqlite3


def get_teamdata(id_team):
    url = "https://lichess.org/api/team/" + id_team + "/users"
    param = dict()
    resp = requests.get(url=url, params=param)
    list_resp = resp.text.splitlines()
    data = list(map(lambda x: json.loads(x), list_resp))
    return data


def get_teams_of_user(user):
    url = "https://lichess.org/api/team/of/" + user
    param = dict()
    resp = requests.get(url=url, params=param)
    data = resp.json()
    teamlist = []
    for i in data:
        teamlist.append(i["id"])
    return teamlist


def get_users_by_team(team_id):
    teamdata = get_teamdata(team_id)
    userlist = []
    for i in teamdata:
        username = i.get('id')
        userlist.append(username)
    return userlist


def user_in_team(team_id, username):
    if team_id in get_teams_of_user(username):
        return True
    return False


async def send_info_inteam(author):
    text = "Du bist bereits Mitglied des Lichess Subscriber Team von TBG."
    await author.send(text)


async def send_info_join(author):
    password = await return_password()
    text = "Du kannst dich bei unserem Lichess Subscriber Team " \
           "https://lichess.org/team/" + config.team + " mit dem Passwort **" + password + "** bewerben.\n" \
           "Ein Moderator schaltet dich dann für das Team frei!"
    await author.send(text)


async def return_password():
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    sql = "SELECT password FROM config WHERE serverid=?"
    password = cursor.execute(sql, (config.serverid,))
    password = password.fetchone()[0]
    connection.close()
    return password
