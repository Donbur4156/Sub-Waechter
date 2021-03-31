import config
import sqlite3
from discord.ext import commands
import discord
import requests
import json
import datetime
import lichess.api


token = config.token
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print("I'm online!")


@bot.command()
async def commands(ctx):
    text = "Registriert euch hier für das Lichess Subscriber Team von TBG.\n" \
           "Verknüpft dazu das Profil von Lichess mit Discord.\n" \
           "Nutzt dazu den Befehl !join:"
    embed = discord.Embed(title="**Commands**", color=discord.Color.gold(), description=text)
    text = "Verknüpft das Profil von Lichess mit Discord.\n" \
           "lichessname  **-->**  Dein Lichess Profil Name"
    embed.add_field(name="**!join lichessname**", value=text, inline=False)
    text = "Gibt den Lichessnamen zurück, der mit dem Discord Profil verknüpft ist."
    embed.add_field(name="**!whichname**", value=text, inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def modcommands(ctx):
    text = "Folgende Commands stehen den Moderatoren zur Verfügung:"
    embed = discord.Embed(title="**Mod Commands**", color=discord.Color.gold(), description=text)
    text = "Gibt das Lichess Profil zurück, das mit dem Discord Profil verknüpft ist."
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
    embed.add_field(name="**!changepassword neuesPasswort**", value=text, inline=False)
    text = "Räumt den Kanal tbg-vs-subs auf. Nur dort ausführbar!"
    embed.add_field(name="**!clean**", value=text, inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def join(ctx, arg1):
    discordtag = str(ctx.author)
    discordid = ctx.author.id
    lichessid = str(arg1.lower())
    roles = str(ctx.author.roles)
    user = "<@" + str(ctx.author.id) + ">"
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
    password = await return_password()
    text = "Deine Discord Identität wurde erfolgreich mit dem Lichessnamen *" \
           "*" + lichessid + "** verbunden!\nDu kannst dich nun bei unserem Lichess Team " \
           "https://lichess.org/team/" + config.team + " mit dem Passwort **" + password + "** bewerben.\n" \
           "Ein Moderator schaltet dich dann für das Team frei!"
    await send_embed_log(ctx, text, discord.Color.blue())
    await ctx.message.delete(delay=120)
    await ctx.author.send(text)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandInvokeError):
        user = "<@" + str(ctx.author.id) + ">"
        text = user + ": Möglicherweise erlaubst du keine privaten Nachrichten. Wende dich für weitere Informationen" \
                      "an einen Moderator!"
        msg = await ctx.send(text)
        await msg.delete(delay=120)
        text = text + "\n**Errormessage**: " + str(error)
        await send_embed_log(ctx, text, discord.Color.red())
    else:
        user = "<@" + str(ctx.author.id) + ">"
        text = user + ": Es ist ein unerwarteter Fehler aufgetreten. Wende dich bitte an einen Moderator!"
        msg = await ctx.send(text)
        await msg.delete(delay=120)
        text = text + "\n**Errormessage**: " + str(error)
        await send_embed_log(ctx, text, discord.Color.red())


@bot.command()
async def saydiscord(ctx, arg1):
    if not await authorization(ctx):
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
        user_current = "<@" + str(current[4]) + ">"
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
    if not await authorization(ctx):
        return False
    discord_id = arg1
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    sql = "SELECT * FROM lichesssub"
    cursor.execute(sql)
    current = False
    for data in cursor:
        if data[4] == int(discord_id):
            current = data
            break
    connection.close()
    discord_id = "<@" + str(discord_id) + ">"
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
        await send_embed_log(ctx, text, discord.Color.blue())
        await ctx.message.delete(delay=120)
        await ctx.author.send(text)
    else:
        user_mention = "<@" + str(ctx.author.id) + ">"
        text = user_mention + ", du bist mit diesem Discord Profil noch nicht eingetragen! Mit dem Befehl" \
                              " `!join lichessname` kannst du dich als Subscriber oder Patreon eintragen."
        msg = await ctx.send(text)
        await msg.delete(delay=120)
        await send_embed_log(ctx, text, discord.Color.orange())


@bot.command()
async def check(ctx):
    if not await authorization(ctx):
        return False
    data = getdata(config.team)
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    blacklist = []
    no_list_entry = []
    faulty_list = []
    changes = []
    lost_user = []
    for i in data:
        lichess_id = i.get("id")
        faulty = i.get("tosViolation")
        if faulty:
            text = "Der User **" + lichess_id + "** hat gegen die Lichess Nutzungsbedinungen verstossen!"
            faulty_list.append(text)
        sql = "SELECT * FROM lichesssub WHERE lichessid=?"
        cursor.execute(sql, (lichess_id,))
        dataset = cursor.fetchone()
        if not dataset:
            no_list_entry.append("Lichess: **" + lichess_id + "** (nicht in Datenbank eingetragen!)")
        else:
            try:
                dc_id = dataset[4]
                server = bot.get_guild(config.serverid)
                dc_member = server.get_member(user_id=dc_id)
                user_current = "<@" + str(dataset[4]) + ">"
                roles = str(dc_member.roles)
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
                    sql = "UPDATE lichesssub SET patreon = 0, twitch = 0 WHERE discordtag=?"
                    cursor.execute(sql, (dataset[0],))
                    connection.commit()
                    blacklist.append(user_current + ": **" + dataset[1] + "**")
            except AttributeError:
                text = "Der User mit dem Discord tag **" + dataset[0] + "** und dem Lichess Profil" \
                       " **" + dataset[1] + "** konnte auf diesem Server nicht gefunden werden!"
                lost_user.append(text)
    connection.close()
    text = ""
    delimiter = "\n"
    if no_list_entry:
        no_list_entry = delimiter.join(no_list_entry)
        text = "__**Folgende User sind nicht in der Datenbank eingetragen:**__\n" + no_list_entry + "\n\n" + text
    else:
        text = "__**Alle User sind in der Datenbank eingetragen!**__\n\n" + text
    if lost_user:
        lost_user = delimiter.join(lost_user)
        text = "__**Folgende User konnten nicht auf dem Server gefunden werden:**__\n" + lost_user + "\n\n" + text
    else:
        text = "__**Alle User wurden auf dem Discord Server gefunden!**__\n\n" + text
    if blacklist:
        blacklist = delimiter.join(blacklist)
        text = "__**Folgende User sind nicht mehr als Subscriber/Patreon hinterlegt:**__\n" + blacklist + "\n\n" + text
    else:
        text = "__**Alle User sind als Subscriber oder Patreon hinterlegt!**__\n\n" + text
    if faulty_list:
        faulty_list = delimiter.join(faulty_list)
        text = "__**Folgende User wurden von lichess geflaggt:**__\n" + faulty_list + "\n\n" + text
    else:
        text = "__**Kein User ist von Lichess geflaggt worden!**__\n\n" + text
    if changes:
        changes = delimiter.join(changes)
        text = "__**Folgende Änderungen wurden vorgenommen:**__\n" + changes + "\n\n" + text
    else:
        text = "__**Es mussten keine Änderungen vorgenommen werden!**__\n\n" + text
    while len(text) > 0:
        if len(text) > 5500:
            index = 0
            while index < 5200:
                index = text.find("\n", index) + 2
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
    if not await authorization(ctx):
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
        current = "<@" + str(data[4]) + ">"
        text = "Der Discord User " + current + " wurde aus der Datenbank entfernt!"
    else:
        text = "Dieses Lichess Profil ist mit keiner Discord Identität verknüpft!"
    await send_embed_log(ctx, text, discord.Color.blue())
    connection.close()
    await ctx.message.delete(delay=120)


@bot.command()
async def getlist(ctx):
    if not await authorization(ctx):
        return False
    '''list_team_member = []
    team_member_gen = lichess.api.users_by_team(config.team)
    for i in team_member_gen:
        list_team_member.append(i.get("id")) '''
    list_discord = []
    list_lichess = []
    list_subscription = []
    # list_team_status = []
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    sql = "Select * FROM lichesssub"
    data = cursor.execute(sql)
    for i in data:
        discord_user = "<@" + str(i[4]) + ">\n"
        list_discord.append(discord_user)
        list_lichess.append(i[1] + "\n")
        sub_status = ""
        if i[2] == 1:
            sub_status += "Twitchsub"
        if i[2] == 1 and i[3] == 1:
            sub_status += "/ "
        if i[3] == 1:
            sub_status += "Patreon"
        list_subscription.append(sub_status + "\n")
        '''team_status = "nicht im Team\n"
        if i[1] in list_team_member:
            team_status = "im Team\n"
        list_team_status.append(team_status)'''
    # send log
    log_channel = bot.get_channel(config.channel_log_id)
    message = ctx.message.content
    user_mention = "<@" + str(ctx.author.id) + ">"
    print_count = 0
    while len(list_discord) > 0:
        print_count += 1
        embed = discord.Embed(
            title="*LIST #" + str(print_count) + "*", color=discord.Color.dark_blue(),
            description=user_mention + ": " + message,
            timestamp=datetime.datetime.utcnow())
        u = 0
        gesamt = len(embed)
        while u < 3 and len(list_discord) > 0 and gesamt < 5900:
            u += 1
            list_discord_temp = ""
            list_lichess_temp = ""
            list_subscription_temp = ""
            # list_team_status_temp = ""
            i = 0
            gesamt = len(embed)
            while i < 40 and len(list_discord) > 0 and gesamt < 5900:
                i += 1
                list_discord_temp += list_discord.pop()
                list_lichess_temp += list_lichess.pop()
                list_subscription_temp += list_subscription.pop()
                # list_team_status_temp += list_team_status.pop()
                gesamt = len(embed) + len(list_discord_temp) + len(list_lichess_temp) + len(list_subscription_temp)
            embed.add_field(name="*Discord*", value=list_discord_temp, inline=True)
            embed.add_field(name="*Lichess*", value=list_lichess_temp, inline=True)
            embed.add_field(name="*Subscription*", value=list_subscription_temp, inline=True)
            # embed.add_field(name="*Teammember*", value=list_team_status_temp, inline=True)
        await log_channel.send(embed=embed)
    await ctx.message.delete(delay=120)


@bot.command()
async def getpassword(ctx):
    if not await authorization(ctx):
        return False
    password = await return_password()
    text = "Das aktuelle Passwort für das Lichess Subscriber Team lautet: **" + password + "**"
    await send_embed_log(ctx, text, discord.Color.blue())
    await ctx.message.delete(delay=120)


async def return_password():
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    sql = "SELECT password FROM config WHERE serverid=?"
    password = cursor.execute(sql, (config.serverid,))
    password = password.fetchone()[0]
    connection.close()
    return password


@bot.command()
async def changepassword(ctx, arg1):
    if not await authorization(ctx):
        return False
    password_old = await return_password()
    password_new = arg1
    if password_old != password_new:
        connection = sqlite3.connect(config.database)
        cursor = connection.cursor()
        sql = "UPDATE config SET password=? WHERE serverid=?"
        cursor.execute(sql, (password_new, config.serverid,))
        connection.commit()
        connection.close()
        text = "Das Passwort für das Lichess Subscriber Team wurde erfolgreich zu **" + password_new + "** geändert!"
        await send_embed_log(ctx, text, discord.Color.green())
    else:
        text = "Das neue Passwort entspricht dem alten Passwort und wurde nicht geändert!"
        await send_embed_log(ctx, text, discord.Color.orange())
    await ctx.message.delete(delay=120)


@bot.command()
async def ping(ctx):
    await ctx.send("pong")
    pass
    user = ctx.author
    embed = discord.Embed(
        title="Ping Pong",
        description="Ping Pong ist toll \n" + user,
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)
    await ctx.message.delete(delay=60)


@bot.command()
async def clean(ctx):
    if not await authorization(ctx):
        return False
    if ctx.message.channel.id not in config.channel_clean_available:
        msg = await ctx.send("Dieser Befehl ist hier nicht verfügbar!")
        await msg.delete(delay=60)
        await ctx.message.delete(delay=60)
        return False
    counter = 0
    async for message in ctx.history(limit=200):
        if not message.pinned:
            await message.delete()
            counter += 1
    channel_name = ctx.message.channel.mention
    text = "Es wurden " + str(counter) + " Nachrichten im Channel " + channel_name + " gelöscht!"
    msg = await ctx.send(text)
    await msg.delete(delay=60)
    await send_embed_log(ctx, text, discord.Color.blurple())


def getdata(id_team):
    url = "https://lichess.org/api/team/" + id_team + "/users"
    param = dict()
    resp = requests.get(url=url, params=param)
    list_resp = resp.text.splitlines()
    data = list(map(lambda x: json.loads(x), list_resp))
    return data


async def authorization(ctx):
    roles = str(ctx.author.roles)
    if config.mod not in roles:
        print("false")
        user = "<@" + str(ctx.author.id) + ">"
        text = user + ", du hast nicht die benötigten Rechte um dies zu tun!"
        msg = await ctx.send(text)
        await msg.delete(delay=120)
        await send_embed_log(ctx, text, discord.Color.red())
        await ctx.message.delete(delay=120)
        return False
    return True


async def send_embed_log(ctx, text, color):
    log_channel = bot.get_channel(config.channel_log_id)
    message = ctx.message.content
    user_mention = "<@" + str(ctx.author.id) + ">"
    embed = discord.Embed(
        title="*LOG*", color=color, description=user_mention + ": " + message, timestamp=datetime.datetime.utcnow())
    print_count = 1
    while len(text) > 0:
        if len(text) > 1000:
            index = 0
            while index < 800:
                index = text.find("\n", index) + 2
            index -= 1
            text_print = text[:index]
        else:
            index = len(text)
            text_print = text
        if print_count == 1:
            embed.add_field(name="*RESULT*", value=text_print, inline=False)
            print_count -= 1
        else:
            embed.add_field(name="\u200b", value=text_print, inline=False)
        text = text[index:]
    await log_channel.send(embed=embed)


bot.run(token)
