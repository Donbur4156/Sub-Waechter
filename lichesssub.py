import config
import sqlite3
from discord.ext import commands
import discord
import requests
import json
import datetime


token = config.token
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print("I'm online!")


@bot.command()
async def commands(ctx):
    text = "Registriert euch für das Lichess Subscriber Team, indem ihr euer Lichess und Discord Profil verknüpft!"
    embed = discord.Embed(title="**Commands**", color=discord.Color.gold(), description=text)
    text = "Verknüpft das Lichess und Discord Profil mit den Rollen Subscriber und Patreon"
    embed.add_field(name="**!join lichessname**", value=text, inline=False)
    text = "Gibt den Lichessnamen zurück, der mit dem Discord Profil verknüpft ist."
    embed.add_field(name="**!whichname**", value=text, inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def modcommands(ctx):
    text = "Folgende Commands stehen den Moderatoren zur Verfügung:"
    embed = discord.Embed(title="**HELP**", color=discord.Color.gold(), description=text)
    text = "Gibt das Lichess Profil zurück, der mit dem Discord Profil verknüpft ist."
    embed.add_field(name="**!saylichess discordUserID**", value=text, inline=False)
    text = "Gibt das Discord Profil zurück, das mit dem Lichess Profil verknüpft ist."
    embed.add_field(name="**!saydiscord lichessname**", value=text, inline=False)
    text = "Löscht den Datensatz mit dem Lichess Profil."
    embed.add_field(name="**!delete lichessname**", value=text, inline=False)
    text = "Überprüft alle Team Member auf ihren Status."
    embed.add_field(name="**!check**", value=text, inline=False)
    text = "Gibt eine CSV Datei zurück mit allen eingetragenen Usern."
    embed.add_field(name="**!getlist**", value=text, inline=False)
    text = "Gibt das aktuelle Passwort wieder."
    embed.add_field(name="**!getpassword**", value=text, inline=False)
    text = "Ändert das aktuelle Passwort in das neu angegebene."
    embed.add_field(name="**!changepassword**", value=text, inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def join(ctx, arg1):
    discordtag = str(ctx.author)
    discordid = ctx.author.id
    lichessid = str(arg1.lower())
    roles = str(discord.Member.roles.fget(ctx.author))
    user = discord.Member.mention.fget(ctx.author)
    twitch = 0
    patreon = 0
    if config.role1 in roles:
        twitch = 1
    if config.role2 in roles:
        patreon = 1
    if twitch == 0 and patreon == 0:
        text = user + ", du scheinst weder Subscriber oder Patreon zu sein. Melde dich bitte bei einem Moderator!"
        msg = await ctx.send(text)
        await msg.delete(delay=120)
        await send_embed_log(ctx, text, discord.Color.red())
        await ctx.message.delete(delay=120)
        return False
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    sql = "SELECT * FROM lichesssub WHERE discordtag=?"
    cursor.execute(sql, (discordtag,))
    data = cursor.fetchone()
    if data:
        text = user + ", dein Discord Profil ist bereits eingetragen! Wende dich an einen Moderator, " \
                      "wenn du das hinterlegte Lichess Profil ändern möchtest."
        msg = await ctx.send(text)
        await msg.delete(delay=120)
        await send_embed_log(ctx, text, discord.Color.orange())
        await ctx.message.delete(delay=120)
        return False
    sql = "SELECT * FROM lichesssub WHERE lichessid=?"
    cursor.execute(sql, (lichessid,))
    data = cursor.fetchone()
    if data:
        text = user + ", dieses Lichess Profil ist bereits eingetragen!"
        msg = await ctx.send(text)
        await msg.delete(delay=120)
        await send_embed_log(ctx, text, discord.Color.orange())
        await ctx.message.delete(delay=120)
        return False
    cursor.execute("INSERT INTO lichesssub (discordtag, lichessid, twitch, patreon, discordid) VALUES (?, ?, ?, ?, ?)",
                   (discordtag, lichessid, twitch, patreon, discordid))
    connection.commit()
    connection.close()
    text = "Deine Discord Identität wurde erfolgreich mit dem Lichessnamen *" \
           "*" + lichessid + "** verbunden!\nDu kannst dich nun bei unserem Lichess Team " \
           "https://lichess.org/team/" + config.team + " mit dem Passwort **" + config.password + "** bewerben.\n" \
           "Ein Moderator schaltet dich dann für das Team frei!"
    await ctx.author.send(text)
    await send_embed_log(ctx, text, discord.Color.blue())
    await ctx.message.delete(delay=120)


@bot.command()
async def saydiscord(ctx, arg1):
    if not await prove(ctx):
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
            break
    connection.close()
    if current:
        server = bot.get_guild(config.serverid)
        dc_member = server.get_member(user_id=current[4])
        user_current = discord.Member.mention.fget(dc_member)
        text = "Der Lichessname **" + lichessid + "** ist mit dem Discord Profil **" + user_current + "** verbunden."
        if current[2] == 1:
            text = text + "\nDer User ist als **Twitch Subscriber** hinterlegt."
        if current[3] == 1:
            text = text + "\nDer User ist als **Patreon** hinterlegt."
        await send_embed_log(ctx, text, discord.Color.blue())
        await ctx.message.delete(delay=120)
    else:
        text = "Der Lichessname " + lichessid + " ist bisher mit keinem Discord Profil verbunden!"
        await send_embed_log(ctx, text, discord.Color.blue())
        await ctx.message.delete(delay=120)


@bot.command()
async def saylichess(ctx, arg1):
    if not await prove(ctx):
        return False
    discord_id = int(arg1)
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    sql = "SELECT * FROM lichesssub"
    cursor.execute(sql)
    current = False
    for data in cursor:
        if data[4] == discord_id:
            current = data
            break
    connection.close()
    server = bot.get_guild(config.serverid)
    dc_member = server.get_member(user_id=discord_id)
    discord_id = discord.Member.mention.fget(dc_member)
    if current:
        user_current = current[1]
        text = "Der Discord User **" + discord_id + "** ist mit dem Lichess Account **" + user_current + "** verbunden."
        if current[2] == 1:
            text = text + "\nDer User ist als **Twitch Subscriber** hinterlegt."
        if current[3] == 1:
            text = text + "\nDer User ist als **Patreon** hinterlegt."
        await send_embed_log(ctx, text, discord.Color.blue())
    else:
        text = "Der Discord User " + discord_id + " ist bisher mit keinem Lichess Acccount verbunden!"
        await send_embed_log(ctx, text, discord.Color.blue())
    await ctx.message.delete(delay=120)


@bot.command()
async def whichname(ctx):
    user = str(ctx.author)
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    sql = "SELECT lichessid FROM lichesssub WHERE discordtag=?"
    cursor.execute(sql, (user,))
    dataset = cursor.fetchone()
    connection.close()
    if dataset:
        lichessid = dataset[0]
        text = "Deine Discord Identität ist mit dem Lichess Profil **" + str(lichessid) + "** verbunden."
        await ctx.author.send(text)
        await send_embed_log(ctx, text, discord.Color.blue())
        await ctx.message.delete(delay=120)
    else:
        user = discord.Member.mention.fget(ctx.author)
        text = user + ", du bist mit diesem Discord Profil noch nicht eingetragen! Mit dem Befehl" \
                      " `!join lichessname` kannst du dich als Subscriber oder Patreon eintragen."
        msg = await ctx.send(text)
        await msg.delete(delay=120)
        await send_embed_log(ctx, text, discord.Color.orange())


@bot.command()
async def check(ctx):
    if not await prove(ctx):
        return False
    data = getdata(config.team)
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    blacklist = []
    no_list_entry = []
    faultylist = []
    changes = []
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
            no_list_entry.append("Lichess: **" + lichessid + "** (nicht in Datenbank eingetragen!)")
        else:
            try:
                dc_id = dataset[4]
                server = bot.get_guild(config.serverid)
                dc_member = server.get_member(user_id=dc_id)
                user_current = discord.Member.mention.fget(dc_member)
                roles = str(discord.Member.roles.fget(dc_member))
                if config.role1 in roles or config.role2 in roles:
                    if config.role1 in roles and dataset[2] == 0:
                        sql = "UPDATE lichesssub SET twitch = 1 WHERE discordtag=?"
                        cursor.execute(sql, (dataset[0],))
                        connection.commit()
                        text = "Dem User **" + user_current + "** wurde der Twitch Sub hinzugefügt!"
                        changes.append(text)
                    if config.role1 not in roles and dataset[2] == 1:
                        sql = "UPDATE lichesssub SET twitch = 0 WHERE discordtag=?"
                        cursor.execute(sql, (dataset[0],))
                        connection.commit()
                        text = "Dem User **" + user_current + "** wurde der Twitch Sub entfernt!"
                        changes.append(text)
                    if config.role2 in roles and dataset[3] == 0:
                        sql = "UPDATE lichesssub SET patreon = 1 WHERE discordtag=?"
                        cursor.execute(sql, (dataset[0],))
                        connection.commit()
                        text = "Dem User **" + user_current + "** wurde der Patreon Status hinzugefügt!"
                        changes.append(text)
                    if config.role2 not in roles and dataset[3] == 1:
                        sql = "UPDATE lichesssub SET patreon = 0 WHERE discordtag=?"
                        cursor.execute(sql, (dataset[0],))
                        connection.commit()
                        text = "Dem User **" + user_current + "** wurde der Patreon Status entfernt!"
                        changes.append(text)
                else:
                    blacklist.append("Lichess: **" + dataset[1] + "** (aktuell weder Subscriber noch Patreon!)")
            except AttributeError:
                text = "Der User mit dem Discord tag **" + dataset[0] + "** und dem Lichess Profil" \
                       " **" + dataset[1] + "** konnte auf diesem Server nicht gefunden werden!"
                blacklist.append(text)
    connection.close()
    text = ""
    trennzeichen = "\n"
    if no_list_entry:
        no_list_entry = trennzeichen.join(no_list_entry)
        text = "Folgende User sind nicht in der Datenbank eingetragen:\n" + no_list_entry + "\n\n" + text
    if blacklist:
        blacklist = trennzeichen.join(blacklist)
        text = "Folgende User sind kein Sub mehr oder nicht mehr auf dem Server :\n" + blacklist + "\n\n" + text
    if faultylist:
        faultylist = trennzeichen.join(faultylist)
        text = "Folgende User wurden von lichess geflaggt:\n" + faultylist + "\n\n" + text
    if changes:
        changes = trennzeichen.join(changes)
        text = "Folgende Änderungen wurden vorgenommen:\n" + changes + "\n\n" + text
    while len(text) > 0:
        if len(text) > 5000:
            index = 0
            while index < 4800:
                index = text.find("\n", index) + 2
                print("Schleife")
                print(index)
            index -= 1
            text_print = text[:index]
        else:
            index = len(text)
            text_print = text
        await send_embed_log(ctx, text_print, discord.Color.purple())
        text = text[index:]
    await ctx.message.delete(delay=120)


@bot.command()
async def delete(ctx, arg1):
    if not await prove(ctx):
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
        server = bot.get_guild(config.serverid)
        dc_member = server.get_member(user_id=data[4])
        current = discord.Member.mention.fget(dc_member)
        text = "Der Discord User " + current + " wurde aus der Datenbank entfernt!"
    else:
        text = "Dieses Lichess Profil ist mit keiner Discord Identität verknüpft!"
    await send_embed_log(ctx, text, discord.Color.blue())
    connection.close()
    await ctx.message.delete(delay=120)


@bot.command()
async def getlist(ctx):
    if not await prove(ctx):
        return False
    msg = await ctx.send("Dieses Feature ist in der Entwicklung!")
    await msg.delete(delay=120)
    await ctx.message.delete(delay=120)


@bot.command()
async def getpassword(ctx):
    if not await prove(ctx):
        return False
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    sql = "SELECT password FROM config WHERE serverid=?"
    password = cursor.execute(sql, (config.serverid,))
    password = password.fetchone()[0]
    text = "Das aktuelle Passwort für das Lichess Subscriber Team lautet: **" + password + "**"
    await send_embed_log(ctx, text, discord.Color.blue())
    await ctx.message.delete(delay=120)
    connection.close()


@bot.command()
async def changepassword(ctx, arg1):
    if not await prove(ctx):
        return False
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    sql = "SELECT password FROM config WHERE serverid=?"
    password = cursor.execute(sql, (config.serverid,))
    password_old = password.fetchone()[0]
    password_new = arg1
    if password_old != password_new:
        sql = "UPDATE config SET password=? WHERE serverid=?"
        cursor.execute(sql, (password_new, config.serverid,))
        connection.commit()
        text = "Das Passwort für das Lichess Subscriber Team wurde erfolgreich zu **" + password_new + "** geändert!"
        await send_embed_log(ctx, text, discord.Color.green())
    else:
        text = "Das neue Passwort entspricht dem alten Passwort und wurde nicht geändert!"
        await send_embed_log(ctx, text, discord.Color.orange())
    await ctx.message.delete(delay=120)
    connection.close()


@bot.command()
async def ping(ctx):
    await ctx.send("pong")
    pass
    user = ctx.author
    user = discord.Member.mention.fget(user)
    embed = discord.Embed(
        title="Ping Pong",
        description="Ping Pong ist toll \n" + user,
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)
    await ctx.message.delete(delay=60)


def getdata(id_team):
    url = "https://lichess.org/api/team/" + id_team + "/users"
    param = dict()
    resp = requests.get(url=url, params=param)
    list_resp = resp.text.splitlines()
    data = list(map(lambda x: json.loads(x), list_resp))
    return data


async def prove(ctx):
    roles = str(discord.Member.roles.fget(ctx.author))
    if config.mod not in roles:
        user = discord.Member.mention.fget(ctx.author)
        text = user + ", du hast nicht die benötigten Rechte um dies zu tun!"
        msg = await ctx.send(text)
        await msg.delete(delay=120)
        await send_embed_log(ctx, text, discord.Color.red())
        await ctx.message.delete(delay=120)
        return False
    return True


async def send_embed_log(ctx, text, color):
    log_channel = bot.get_channel(config.channelid)
    message = ctx.message.content
    user = discord.Member.mention.fget(ctx.author)
    embed = discord.Embed(
        title="*LOG*", color=color, description=user + ": " + message, timestamp=datetime.datetime.utcnow())
    while len(text) > 0:
        if len(text) > 1000:
            index = 0
            while index < 900:
                index = text.find("\n", index) + 2
                print("Schleife")
                print(index)
            index -= 1
            text_print = text[:index]
        else:
            index = len(text)
            text_print = text
        embed.add_field(name="*RESULT*", value=text_print, inline=False)
        text = text[index:]
    await log_channel.send(embed=embed)


bot.run(token)
