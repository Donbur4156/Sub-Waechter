import config
import sqlite3
from discord.ext import commands
from discord.ext.commands import MemberConverter, RoleConverter
import discord
import datetime
import csv
import os
import lichess.api
import operator
import functions.function as f


token = config.token
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print("I'm online!")


@bot.command()
async def commands(ctx):
    text = "Registriert euch hier für das Lichess Subscriber Team von TBG.\n" \
           "Verknüpft dazu euer Lichess Profil mit eurem Discord Profil.\n" \
           "Nutzt dazu den Befehl !join:"
    embed = discord.Embed(title="**Commands**", color=discord.Color.gold(), description=text)
    text = "Verknüpft das Profil von Lichess mit deinem Discord Profil."
    embed.add_field(name="**!join {dein lichessname}**", value=text, inline=False)
    text = "Gibt den Lichessnamen zurück, der mit deinem Discord Profil verknüpft ist."
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
    text = "Räumt den Kanal auf. Nur in folgenden Kanälen verfügbar:\n#tbg-vs-sub\n#lichess-sub-team\n#control"
    embed.add_field(name="**!clean**", value=text, inline=False)
    text = "Gibt das Ergebnis mehrerer Swiss Turniere als CSV zurück.\n" \
           "Als Argumente die IDs der Turniere anfügen."
    embed.add_field(name="**!swiss ID1 ID2 ID3 ...**", value=text, inline=False)
    text = "Fügt einen Bot-Account als Platzhalter in die Datenbank ein."
    embed.add_field(name="**!joinbot lichessname**", value=text, inline=False)
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
    data_discord = cursor.fetchone()
    if data_discord:  # Discord Profil eingetragen
        lichess_id = data_discord[1]
        text = user + ", dein Discord Profil ist bereits eingetragen! Wende dich an einen Moderator, " \
                      "wenn du das hinterlegte Lichess Profil (**" + lichess_id + "**) ändern möchtest."
        await ctx.author.send(text)
        await ctx.message.delete(delay=120)
        if f.user_in_team(config.team, lichessid):
            in_team = await f.send_info_inteam(ctx.author)
            log_text = text + "\n\n" + in_team
            await send_embed_log(ctx, log_text, discord.Color.green())
        else:
            in_team = await f.send_info_join(ctx.author)
            log_text = text + "\n\n" + in_team
            await send_embed_log(ctx, log_text, discord.Color.orange())
        return False
    sql = "SELECT * FROM lichesssub WHERE lichessid=?"
    cursor.execute(sql, (lichessid,))
    data_lichess = cursor.fetchone()
    if data_lichess:  # Lichess eingetragen aber nicht dieser Discord User
        text = user + ", du versuchst ein Lichess Profil einzutragen, welches bereits eingetragen ist!" \
                      "Wende dich an einen Moderator, wenn du das hinterlegte Discord Profil ändern möchtest."
        await ctx.author.send(text)
        await send_embed_log(ctx, text, discord.Color.orange())
        await ctx.message.delete(delay=120)
        return False
    cursor.execute("INSERT INTO lichesssub (discordtag, lichessid, twitch, patreon, discordid) VALUES (?, ?, ?, ?, ?)",
                   (discordtag, lichessid, twitch, patreon, discordid))
    connection.commit()
    connection.close()
    text = "Deine Discord Identität wurde erfolgreich mit dem Lichessnamen *" \
           "*" + lichessid + "** verbunden!"
    await ctx.message.delete(delay=120)
    await ctx.author.send(text)
    team_info = await f.send_info_join(ctx.author)
    log_text = text + "\n\n" + team_info
    await send_embed_log(ctx, log_text, discord.Color.blue())


@join.error
async def join_handler(ctx, error):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        text = await get_mention(ctx, ctx.author.id) + \
               "Der Befehl !join benötigt zusätzlich deinen Lichessnamen!\n" \
               "!join lichessname"
        msg = await ctx.send(text)
        await msg.delete(delay=18000)
        await ctx.message.delete(delay=18000)


@bot.command()
async def joinbot(ctx, arg1):
    if not await authorization(ctx):
        return False
    discordtag = "Bot"
    discordid = 1234
    lichessid = str(arg1.lower())
    user = "<@" + str(ctx.author.id) + ">"
    twitch = 1
    patreon = 1
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    sql = "SELECT * FROM lichesssub WHERE lichessid=?"
    cursor.execute(sql, (lichessid,))
    data_lichess = cursor.fetchone()
    if data_lichess:  # Lichess eingetragen aber nicht dieser Discord User
        text = user + ", du versuchst ein Lichess Profil einzutragen, welches bereits eingetragen ist!"
        await ctx.author.send(text)
        await send_embed_log(ctx, text, discord.Color.orange())
        await ctx.message.delete(delay=120)
        return False
    cursor.execute("INSERT INTO lichesssub (discordtag, lichessid, twitch, patreon, discordid) VALUES (?, ?, ?, ?, ?)",
                   (discordtag, lichessid, twitch, patreon, discordid))
    connection.commit()
    connection.close()
    text = "Dem Platzhalter für Bots wurde der Lichessname **" + lichessid + "** hinzugefügt!"
    await send_embed_log(ctx, text, discord.Color.blue())
    await ctx.message.delete(delay=120)
    await ctx.author.send(text)


@joinbot.error
async def joinbot_handler(ctx, error):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        text = await get_mention(ctx, ctx.author.id) + \
               "Der Befehl !joinbot benötigt zusätzlich den Lichessnamen des Bots!\n" \
               "!joinbot lichessname"
        msg = await ctx.send(text)
        await msg.delete(delay=18000)
        await ctx.message.delete(delay=18000)


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
        if current[0] == "Bot":
            text = "Der lichessname **" + lichessid + "** ist als Bot Account hinterlegt."
        else:
            user_current = "<@" + str(current[4]) + ">"
            text = "Der Lichessname **" + lichessid + "** ist mit dem Discord Profil **" \
                   + user_current + "** verbunden."
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
    discord_id = await get_mention(ctx, discord_id)
    #    discord_id = "<@" + str(discord_id) + ">"
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


async def check_user():
    # auf Rolle prüfen
    # auf Lichess prüfen
    pass


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
        user_mention = await get_mention(ctx, ctx.author.id)
        text = user_mention + ", du bist mit diesem Discord Profil noch nicht eingetragen! Mit dem Befehl" \
                              " `!join lichessname` kannst du dich als Subscriber oder Patreon eintragen."
        msg = await ctx.send(text)
        await msg.delete(delay=120)
        await send_embed_log(ctx, text, discord.Color.orange())


@bot.command()
async def check(ctx):
    if not await authorization(ctx):
        return False
    data = f.get_teamdata(config.team)
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    blacklist = []
    no_list_entry = []
    faulty_list = []
    changes = []
    lost_user = []
    for i in data:
        lichess_id = i.get("id")
        if i.get("tosViolation"):
            text = "Der User **" + lichess_id + "** hat gegen die Lichess Nutzungsbedinungen verstossen!"
            faulty_list.append(text)
        sql = "SELECT * FROM lichesssub WHERE lichessid=?"
        cursor.execute(sql, (lichess_id,))
        dataset = cursor.fetchone()
        if not dataset:
            no_list_entry.append("Lichess: **" + lichess_id + "** (nicht in Datenbank eingetragen!)")
        elif dataset[0] != "Bot":
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
async def getlist(ctx):
    if not await authorization(ctx):
        return False
    list_team_member = []
    team_member_gen = lichess.api.users_by_team(config.team)
    for i in team_member_gen:
        list_team_member.append(i.get("id"))
    list_discord_tag = []
    list_discord_id = []
    list_lichess = []
    list_twitch_status = []
    list_patreon_status = []
    list_team_status = []
    connection = sqlite3.connect(config.database)
    cursor = connection.cursor()
    sql = "Select * FROM lichesssub"
    data = cursor.execute(sql)
    for i in data:
        list_discord_id.append(i[4])
        list_discord_tag.append(i[0])
        list_lichess.append(i[1])
        twitch = False
        if i[2] == 1:
            twitch = True
        list_twitch_status.append(twitch)
        patreon = False
        if i[3] == 1:
            patreon = True
        list_patreon_status.append(patreon)
        team_status = False
        if i[1] in list_team_member:
            team_status = True
        list_team_status.append(team_status)
    filename = 'subscriber_list.csv'
    if os.path.isfile(filename):
        os.remove(filename)
    columns = ["Discordtag", "DiscordID", "LichessID", "Twitch", "Patreon", "Teamstatus"]
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        for x in range(0, len(list_discord_id)):
            discord_tag = list_discord_tag[x]
            discord_id = list_discord_id[x]
            lichess_id = list_lichess[x]
            twitch = list_twitch_status[x]
            patreon = list_patreon_status[x]
            team_member = list_team_status[x]
            writer.writerow([discord_tag, discord_id, lichess_id, twitch, patreon, team_member])
    await send_embed_log(ctx, "Export CSV to Discord", discord.Color.dark_blue())
    file_export = discord.File(filename)
    log_channel = bot.get_channel(config.channel_log_id)
    await log_channel.send(file=file_export)
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
async def getpassword(ctx):
    if not await authorization(ctx):
        return False
    password = await f.return_password()
    text = "Das aktuelle Passwort für das Lichess Subscriber Team lautet: **" + password + "**"
    await send_embed_log(ctx, text, discord.Color.blue())
    await ctx.message.delete(delay=120)


@bot.command()
async def changepassword(ctx, arg1):
    if not await authorization(ctx):
        return False
    password_old = await f.return_password()
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
async def swiss(ctx, *args):
    if not await authorization(ctx):
        return False
    result = []
    dict_score = {}
    dict_tie = {}
    userlist = []
    error_list = []
    for arg in args:
        unique_swiss = f.get_swiss(arg)
        if unique_swiss:
            for row in unique_swiss:
                if row[0] in userlist:
                    dict_score[row[0]] += row[1]
                    dict_tie[row[0]] += row[2]
                else:
                    item = {row[0]: row[1]}
                    dict_score.update(item)
                    item = {row[0]: row[2]}
                    dict_tie.update(item)
                    userlist.append(row[0])
        else:
            error_list.append(arg)
    for i in range(len(userlist)):
        username = userlist[i]
        result_line = [i, username, dict_score[username], dict_tie[username]]
        result.append(result_line)
    result_sorted = sorted(result, key=operator.itemgetter(2, 3), reverse=True)
    for i in range(len(result_sorted)):
        result_sorted[i][0] = i + 1
    print(error_list)
    filename = 'swiss.csv'
    if os.path.isfile(filename):
        os.remove(filename)
    columns = ["Rank", "Username", "Score", "TieBreak"]
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(columns)
        for x in range(len(result_sorted)):
            rank = result_sorted[x][0]
            username = result_sorted[x][1]
            score = str(result_sorted[x][2]).replace('.', ',')
            tiebreak = str(result_sorted[x][3]).replace('.', ',')
            writer.writerow([rank, username, score, tiebreak])
    text = "Export CSV to Discord"
    if error_list:
        text += "\nFolgende IDs konnten nicht geladen werden:"
        for i in error_list:
            text += "\n" + i
    await send_embed_log(ctx, text, discord.Color.dark_blue())
    file_export = discord.File(filename)
    log_channel = bot.get_channel(config.channel_log_id)
    await log_channel.send(file=file_export)
    if os.path.isfile(filename):
        os.remove(filename)
    await ctx.message.delete(delay=120)


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
    messages = ""
    async for message in ctx.history(limit=10):
        if not message.pinned:
            message_time = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            messages = "\n" + str(await get_mention(ctx, message.author.id)) + " (" + str(message_time) + "):\n" \
                       + str(message.content) + messages
            await message.delete()
            counter += 1
    channel_name = ctx.message.channel.mention
    text = "Es wurden " + str(counter) + " Nachrichten im Channel " + channel_name + " gelöscht!"
    msg = await ctx.send(text)
    await msg.delete(delay=60)
    text += "\n**Gelöschte Nachrichten:**" + messages
    await send_embed_log(ctx, text, discord.Color.blurple())


async def authorization(ctx):
    roles = str(ctx.author.roles)
    if config.mod not in roles:
        user = "<@" + str(ctx.author.id) + ">"
        text = user + ", du hast nicht die benötigten Rechte um dies zu tun!"
        msg = await ctx.send(text)
        await msg.delete(delay=120)
        await send_embed_log(ctx, text, discord.Color.red())
        await ctx.message.delete(delay=120)
        return False
    return True


async def ping_unique_mods(ctx):
    log_channel = bot.get_channel(config.channel_log_id)
    for mod in config.log_mods_to_ping:
        member = await get_mention(ctx, mod)
        mention = await log_channel.send(member)
        await mention.delete()
    for role in config.log_mod_role_to_ping:
        role = await get_role_mention(ctx, role)
        mention = await log_channel.send(role)
        await mention.delete()


async def get_mention(ctx, member):
    converter = MemberConverter()
    member = await converter.convert(ctx, str(member))
    return member.mention


async def get_role_mention(ctx, role):
    converter = RoleConverter()
    role_mention = await converter.convert(ctx, str(role))
    return role_mention.mention


# Creates a logger and works with it.
def print_log(text):
    now = datetime.datetime.now()
    now = now.strftime("%Y-%m-%d %H:%M:%S")
    print(str(now) + ": " + str(text))


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


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        user = "<@" + str(ctx.author.id) + ">"
        text = "Der User " + user + " hat dem Befehl zu wenig Argumente übergeben!\n**Errormessage**: " + str(error)
        await send_embed_log(ctx, text, discord.Color.red())
        print_log(text)
    elif isinstance(error, discord.ext.commands.CommandInvokeError):
        user = "<@" + str(ctx.author.id) + ">"
        text = user + ": Möglicherweise erlaubst du keine privaten Nachrichten. Wende dich für weitere Informationen" \
                      "an einen Moderator!"
        msg = await ctx.send(text)
        await msg.delete(delay=120)
        text = text + "\n**Errormessage**: " + str(error)
        await send_embed_log(ctx, text, discord.Color.red())
        print_log(text)
    else:
        user = "<@" + str(ctx.author.id) + ">"
        text = user + ": Es ist ein unerwarteter Fehler aufgetreten. Wende dich bitte an einen Moderator!"
        msg = await ctx.send(text)
        await msg.delete(delay=120)
        text = text + "\n**Errormessage**: " + str(error)
        await send_embed_log(ctx, text, discord.Color.red())
        print_log(text)
    await ping_unique_mods(ctx)


bot.run(token)
