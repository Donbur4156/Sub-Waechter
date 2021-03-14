import config
import sqlite3
from discord.ext import commands
import discord
import requests
import json


token = config.token
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print("I'm online!")


@bot.command()
# @commands.has_any_role(config.role1, config.role2)
async def join(ctx, arg1):
    log_channel_id = config.channelid
    log_channel = bot.get_channel(log_channel_id)
    message = ctx.message.content
    discordtag = str(ctx.author)
    discordid = ctx.author.id
    lichessid = str(arg1.lower())
    roles = str(discord.Member.roles.fget(ctx.author))
    twitch = 0
    patreon = 0
    if config.role1 in roles:
        twitch = 1
    if config.role2 in roles:
        patreon = 1
    if twitch == 0 and patreon == 0:
        text = "Du scheinst weder Subscriber oder Patreon zu sein. Melde dich bitte bei einem Stream-Mod!"
        await ctx.send(text)
        text = "- - - - - - - - - - - - - - - - - -\n" \
               "*LOG* - User: **" + discordtag + "** - Command: `" + message + "`\n*RESULT*:\n" + text
        await log_channel.send(text)
        return False
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    # prüfe auf alte Daten
    sql = "SELECT * FROM lichesssub WHERE discordtag=?"
    cursor.execute(sql, (discordtag,))
    data = cursor.fetchone()
    if data:
        text = "Dein Discord Profil ist bereits eingetragen! Wende dich an einen Stream-Mod, wenn du das " \
               "hinterlegte Lichess Profil ändern möchtest."
        await ctx.send(text)
        text = "- - - - - - - - - - - - - - - - - -\n" \
               "*LOG* - User: **" + discordtag + "** - Command: `" + message + "`\n*RESULT*:\n" + text
        await log_channel.send(text)
        return False
    sql = "SELECT * FROM lichesssub WHERE lichessid=?"
    cursor.execute(sql, (lichessid,))
    data = cursor.fetchone()
    if data:
        text = "Dieses Lichess Profil ist bereits eingetragen!"
        await ctx.send(text)
        text = "- - - - - - - - - - - - - - - - - -\n" \
               "*LOG* - User: **" + discordtag + "** - Command: `" + message + "`\n*RESULT*:\n" + text
        await log_channel.send(text)
        return False
    cursor.execute("INSERT INTO lichesssub (discordtag, lichessid, twitch, patreon, discordid) VALUES (?, ?, ?, ?, ?)",
                   (discordtag, lichessid, twitch, patreon, discordid))
    connection.commit()
    connection.close()
    text = "Deine Discord Identität wurde erfolgreich mit dem Lichessnamen *" \
           "*" + lichessid + "** verbunden!\nDu kannst dich nun bei unserem Lichess Team " \
                             "https://lichess.org/team/tbg-subs mit dem Passwort **TBGSub21** bewerben.\n" \
                             "Ein Moderator schaltet dich dann für das Team frei!"
    await ctx.author.send(text)
    text = "- - - - - - - - - - - - - - - - - -\n" \
           "*LOG* - User: **" + discordtag + "** - Command: `" + message + "`\n*RESULT*:\n" + text
    await log_channel.send(text)


@bot.command()
async def whois(ctx, arg1):
    log_channel_id = config.channelid
    log_channel = bot.get_channel(log_channel_id)
    message = ctx.message.content
    user = str(ctx.author)
    roles = str(discord.Member.roles.fget(ctx.author))
    if config.mod not in roles:
        text = "Du bist nicht berechtigt diese Daten auszulesen!"
        await ctx.send(text)
        text = "- - - - - - - - - - - - - - - - - -\n" \
               "*LOG* - User: **" + user + "** - Command: `" + message + "`\n*RESULT*:\n" + text
        await log_channel.send(text)
        return False
    lichessid = arg1.lower()
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    sql = "SELECT * FROM lichesssub"
    cursor.execute(sql)
    current = False
    for data in cursor:
        if data[1] == lichessid:
            current = data
    if current:
        text = "Der Lichessname **" + lichessid + "** ist mit dem Discord Profil **" + current[0] + "** verbunden."
        if current[2] == 1:
            text = text + "\nDer User ist als **Twitch Subscriber** hinterlegt."
        if current[3] == 1:
            text = text + "\nDer User ist als **Patreon** hinterlegt."
        text = "- - - - - - - - - - - - - - - - - -\n" \
               "*LOG* - User: **" + user + "** - Command: `" + message + "`\n*RESULT*:\n" + text
        await log_channel.send(text)
    else:
        text = "Der Lichessname " + lichessid + " ist bisher mit keinem Discord Profil verbunden!"
        text = "- - - - - - - - - - - - - - - - - -\n" \
               "*LOG* - User: **" + user + "** - Command: `" + message + "`\n*RESULT*:\n" + text
        await log_channel.send(text)
    connection.close()


@bot.command()
async def whichname(ctx):
    log_channel_id = config.channelid
    log_channel = bot.get_channel(log_channel_id)
    message = ctx.message.content
    user = str(ctx.author)
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    sql = "SELECT lichessid FROM lichesssub WHERE discordtag=?"
    cursor.execute(sql, (user,))
    dataset = cursor.fetchone()
    if dataset:
        lichessid = dataset[0]
        text = "Deine Discord Identität ist mit dem Lichess Profil **" + str(lichessid) + "** verbunden."
        await ctx.author.send(text)
        text = "- - - - - - - - - - - - - - - - - -\n" \
               "*LOG* - User: **" + user + "** - Command: `" + message + "`\n*RESULT*:\n" + text
        await log_channel.send(text)
    else:
        text = "Du bist mit diesem Discord Profil noch nicht eingetragen! Mit dem Befehl `!join lichessname`" \
               "kannst du dich als Subscriber oder Patreon eintragen."
        await ctx.send(text)
        text = "- - - - - - - - - - - - - - - - - -\n" \
               "*LOG* - User: **" + user + "** - Command: `" + message + "`\n*RESULT*:\n" + text
        await log_channel.send(text)
    connection.close()

@bot.command()
async def check(ctx):
    log_channel_id = config.channelid
    log_channel = bot.get_channel(log_channel_id)
    message = ctx.message.content
    user = str(ctx.author)
    roles = str(discord.Member.roles.fget(ctx.author))
    if config.mod not in roles:
        text = "Du bist leider nicht berechtigt diese Daten auszulesen!"
        await ctx.send(text)
        text = "- - - - - - - - - - - - - - - - - -\n" \
               "*LOG* - User: **" + user + "** - Command: `" + message + "`\n*RESULT*:\n" + text
        await log_channel.send(text)
        return False
    data = getdata(config.team)
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    blacklist = []
    faultylist = []
    text = "- - - - - - - - - - - - - - - - - -\n" \
           "*LOG* - Ein Datencheck wurde durch den User: **" + user + "** gestartet:"
    await log_channel.send(text)
    for i in data:
        lichessid = i.get("id")
        faulty = i.get("tosViolation")
        if faulty:
            text = "Der User **" + lichessid + "** hat gegen die Lichess Nutzungsbedinungen verstossen!"
            faultylist.append(text)
        sql = "SELECT * FROM lichesssub WHERE lichessid=?"
        cursor.execute(sql, (lichessid,))
        dataset = cursor.fetchone()
        if not dataset:
            text = "Der lichessname **" + lichessid + "** ist nicht in der Datenbank hinterlegt!"
            await log_channel.send(text)
            blacklist.append("Lichess: **" + lichessid + "** (nicht in Datenbank eingetragen!)")
        else:
            dc_id = dataset[4]
            server = bot.get_guild(config.serverid)
            dc_member = server.get_member(user_id=dc_id)
            roles = str(discord.Member.roles.fget(dc_member))
            if config.role1 in roles or config.role2 in roles:
                if config.role1 in roles and dataset[2] == 0:
                    sql = "UPDATE lichesssub SET twitch = 1 WHERE discordtag=?"
                    cursor.execute(sql, (dataset[0],))
                    connection.commit()
                    text = "Dem User **" + dataset[0] + "** wurde der Twitch Sub hinzugefügt!"
                    await log_channel.send(text)
                if config.role1 not in roles and dataset[2] == 1:
                    sql = "UPDATE lichesssub SET twitch = 0 WHERE discordtag=?"
                    cursor.execute(sql, (dataset[0],))
                    connection.commit()
                    text = "Dem User **" + dataset[0] + "** wurde der Twitch Sub entfernt!"
                    await log_channel.send(text)
                if config.role2 in roles and dataset[3] == 0:
                    sql = "UPDATE lichesssub SET patreon = 1 WHERE discordtag=?"
                    cursor.execute(sql, (dataset[0],))
                    connection.commit()
                    text = "Dem User **" + dataset[0] + "** wurde der Patreon Status hinzugefügt!"
                    await log_channel.send(text)
                if config.role2 not in roles and dataset[3] == 1:
                    sql = "UPDATE lichesssub SET patreon = 0 WHERE discordtag=?"
                    cursor.execute(sql, (dataset[0],))
                    connection.commit()
                    text = "Dem User **" + dataset[0] + "** wurde der Patreon Status entfernt!"
                    await log_channel.send(text)
            else:
                text = "Der User **" + dataset[0] + "** ist aktuell weder Subscriber noch Patreon!"
                await log_channel.send(text)
                blacklist.append("Discord: **" + dataset[0] + "**")
    for i in faultylist:
        blacklist.append(i)
    connection.close()
    blacklist.sort(key=str.lower)
    trennzeichen = "\n"
    blacklist = trennzeichen.join(blacklist)
    text = "Folgende User sind kein Sub mehr oder sind nicht in der Datenbank eingetragen:\n" + blacklist
    text = "- - - - - - - - - - - - - - - - - -\n" \
           "*LOG* - User: **" + user + "** - Command: `" + message + "`\n*RESULT*:\n" + text
    await log_channel.send(text)


@bot.command()
async def delete(ctx, arg1):
    log_channel_id = config.channelid
    log_channel = bot.get_channel(log_channel_id)
    message = ctx.message.content
    user = str(ctx.author)
    roles = str(discord.Member.roles.fget(ctx.author))
    if config.mod not in roles:
        text = "du bist nicht berechtigt dies zu tun!"
        await ctx.send(text)
        text = "- - - - - - - - - - - - - - - - - -\n" \
               "*LOG* - User: **" + user + "** - Command: `" + message + "`\n*RESULT*:\n" + text
        await log_channel.send(text)
        return False
    lichess_user = arg1.lower()
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    sql = "SELECT * FROM lichesssub WHERE lichessid=?"
    cursor.execute(sql, (lichess_user,))
    data = cursor.fetchone()
    if data:
        sql = "DELETE FROM lichesssub WHERE lichessid=?"
        cursor.execute(sql, (lichess_user,))
        connection.commit()
        text = "Der User mit dem Discord tag **" + data[0] + "** wurde aus der Datenbank entfernt!"
    else:
        text = "Dieses Lichess Profil ist mit keiner Discord Identität verknüpft!"
    text = "- - - - - - - - - - - - - - - - - -\n" \
           "*LOG* - User: **" + user + "** - Command: `" + message + "`\n*RESULT*:\n" + text
    await log_channel.send(text)
    connection.close()


@bot.command()
async def ping(ctx):
    await ctx.send("pong")


def getdata(id_team):
    url = "https://lichess.org/api/team/" + id_team + "/users"
    param = dict()
    resp = requests.get(url=url, params=param)
    list_resp = resp.text.splitlines()
    data = list(map(lambda x: json.loads(x), list_resp))
    return data


bot.run(token)
