#testing
import os
import coc
import asyncio
import discord
import pymysql
from discord.ext import commands


client  = coc.login(os.environ['gmail'], os.environ['COC-API_pass'], client=coc.EventsClient)
bot = commands.Bot(command_prefix = '-', intents = discord.Intents.all())
condb = pymysql.connect(
    host = os.environ['DBhost'],
    user = os.environ['DBuser'],
    password = os.environ['DBpass'],
    db = os.environ['DB'],
    cursorclass=pymysql.cursors.DictCursor
)

ch_tokens = {'-fd': 'feed', '-wel': 'welcome', '-wtg': 'waiting', '-hlp': 'help'}
rl_tokens = {'-l': 'leader', '-c': 'co', '-e': 'elder', '-m': 'member', '-w': 'wrole', '-n': 'new'}


'''DataBase'''

def eject(table: str, pkid: int, mg = ''):
    try:
        with condb.cursor() as cur:
            if table.lower() == 'servers' and mg == '':
                cur.execute(f"delete from servers where guild_id = '{pkid}'")
            elif table.lower() == 'players' and mg != '':
                cur.execute(f"delete from players where member = '{pkid}' and guild_id = '{mg}'")
    except Exception as e: print('EjectError:', e)
    finally: condb.commit()

def append(table: str, data, column = ''):
    try:
        if type(data) in [list, tuple]:
            if column == '' and len(data) in [len(ch_tokens)+len(rl_tokens), 3] :
                val = '('
                for i in data: val += f"'{i}', "
                else: val = val[:-2]+')'
                with condb.cursor() as cur:
                    cur.execute(f"insert into {table.lower()} values{val}")
            elif type(column) in [tuple, list] and len(column) == len(data):
                if (table.lower() == 'servers' and len(column) <= len(ch_tokens)+len(rl_tokens)) or (table.lower() == 'players' and len(column) <= 3):
                    clm = dt = '('
                    for i in range(len(data)):
                        clm += f"{column[i]}, "
                        dt += f"'{data[i]}', "
                    else: 
                        clm = clm[:-2]+')'
                        dt = dt[:-2]+')'
                    with condb.cursor() as cur:
                        cur.execute(f"insert into {table.lower()}{clm} values{dt}")
    except Exception as e: print('AppendError:', e)
    finally:condb.commit()

def update(table: str, column: str, value: str, id: str):
    try:
        if table.lower() == 'servers':
            with condb.cursor() as cur:
                cur.execute(f"UPDATE servers SET {column} = '{value}' WHERE guild_id = '{id}'")
        elif table.lower() == 'players':
            with condb.cursor() as cur:
                cur.execute(f"UPDATE players SET {column} = '{value}' WHERE member = '{id}'")
    except Exception as e: print('UpdateError: ', e)
    finally: condb.commit()

def get(column: str, table: str, pkid: int):
    with condb.cursor() as cur:
        if table.lower() == 'servers':
            cur.execute(f"select {column.lower()} from servers where guild_id = '{pkid}'")
        elif table.lower() == 'players':
            cur.execute(f"select {column.lower()} from players where members = '{pkid}'")
        return (lambda x : int(x) if x.isnumeric() else str(x))(cur.fetchone()[column.lower()])

def links(server_id : int, t2m = True):
    try:
        mapin = dict()
        guild = bot.get_guild(server_id)
        with condb.cursor() as cur:
            cur.execute(f"select player_tag, member from players where guild_id = '{server_id}'")
            ld = cur.fetchall()
            if t2m:
                for tm in ld:
                    mapin[tm['player_tag']] = guild.get_member(int(tm['member']))
            else:
                for it in ld:
                    mapin[int(it['member'])] = it['player_tag']
        return mapin
    except Exception as e: print('LinkError:', e)

def saved_guild(clan_tag = tuple()): 
    try:
        guilds = list()
        with condb.cursor() as cur:
            if clan_tag == ():
                cur.execute("select guild_id from servers")
            elif type(clan_tag) in [tuple, list]:
                tg = '('
                for i in clan_tag: tg += f"'{i}', "
                else: tg = tg[:-2]+')'
                cur.execute(f"select guild_id from servers where clan_tag in {tg}")
            fetch = cur.fetchall()
            for guildid in fetch:
                guilds.append(bot.get_guild(int(guildid['guild_id'])))
        if len(guilds) == 1: return guilds[0]
        else: return guilds 
    except Exception as e: print('SavedGuildError:', e)
        
def saved_clan_tag(guild_id = tuple()):
    try:
        clans = list()
        with condb.cursor() as cur:
            if guild_id == ():
                cur.execute('select clan_tag from servers')
            elif type(guild_id) in [tuple, list]:
                gd = '('
                for i in guild_id: gd += f"'{i}', "
                else: gd = gd[:-2]+')'
                cur.execute(f"select clan_tag from servers where guild_id in {gd}")
            for clantag in cur.fetchall():
                clans.append(clantag['clan_tag'])
        return clans
    except Exception as e: print('SavedClanTag Error:', e)

def clan_roles(roles):
    try:
        rval = tuple()
        if len(roles) == 1 and roles[0] == "*":
            with condb.cursor() as cur:
                cur.execute('select leader, co, elder, member from servers')
                fl = cur.fetchall()
                for dic in fl:
                    if dic['leader']:
                        rval += int(dic['leader'])
                    if dic['co']:
                        rval += int(dic['co'])
                    if dic['elder']:
                        rval += int(dic['elder'])
                    if dic['member']:
                        rval += int(dic['member']),
        elif roles[0] != '*' and len(roles) == 1:
            with condb.cursor() as cur:
                cur.execute(f"select {roles[0]} from servers")
                val = int(cur.fetchone()[roles[0]])
                for guild in bot.guilds:
                    if val in [role.id for role in guild.roles]: 
                        return guild.get_role(val)
        elif len(roles) > 1:
            with condb.cursor() as cur:
                clms = roles[0]
                for i in roles[1:]: clms += f', {i}'
                cur.execute(f"select {clms} from servers")
                fl = cur.fetchall()
                rl = clms.split(', ')
                for dic in fl:
                    for i in rl:
                        if dic[i]:
                            rval += int(dic[i]),
        return rval
    except Exception as e: print('ClanRolesError:', e)


'''SetUp Commands'''

@bot.group()
async def setup(ctx):
    if not ctx.author.guild in saved_guild():
        append(table='servers', column=['guild_id'], data=[ctx.author.guild.id])
@setup.command(aliases = ['edit'])
async def all(ctx, *, arg):
    try:
        tknsl = arg.split()
        for i in range(len(tknsl)):
            if tknsl[i] in ch_tokens:
                update('servers', tokens[tknsl[i]], tknsl[i-1][2:-1], ctx.author.guild.id)
            elif tknsl[i] in rl_tokens:
                update('servers', rl_tokens[tknsl[i]], tknsl[i-1][3:-1], ctx.author.guild.id)
    except Exception as e: print(e)
@setup.command(aliases = ['clan', 'clan_tag'])
async def tag(ctx, tag: str):
    if tag[0] == '#':
        update('servers', 'clan_tag', tag, ctx.guild.id)
    else:
        ctx.send('**Error:** Invalid clan tag, it must be starts with "#"')
@setup.command(aliases = ['ch'])
async def channel(ctx, *, arg):
    try:
        tknsl = arg.split()
        for i in range(len(tknsl)):
            if tknsl[i] in ch_tokens:
                update('servers', ch_tokens[tknsl[i]], tknsl[i-1][2:-1], ctx.author.guild.id)          
    except Exception as e: print(e)
@setup.command(aliases = ['rl'])
async def role(ctx, *, arg):
    try:
        tknsl = arg.split()
        for i in range(len(tknsl)):
            if tknsl[i] in rl_tokens:
                update('servers', rl_tokens[tknsl[i]], tknsl[i-1][3:-1], ctx.author.guild.id)
    except Exception as e: print(e)



'''Discord EVENTS '''

@bot.event
async def on_ready():
    await bot.change_presence( activity = discord.Activity(name = 'BraZZerS', type = discord.ActivityType.watching))
    print('Bot is ready...')

@bot.event
async def on_member_join(new : discord.Member):
    wlcmsg = f'''Hey {new.mention}, Welcome to  :broken_heart: Broken Hearts\** :broken_heart: !
**
We only accept TH10, TH11, TH12 and TH13 !

If you are interested to join our clan do the following:

  1.** Send a screenshot of your in game profile, with your player tag visible.
**2.** Send your player tag in text form. 
**3.** Send a screenshot of your base. It must be in a war base slot.
**4.** Wait for an answer from one of the staff.

*If you need any help ask it in {new.guild.get_channel(get(ch_tokens['-hlp'], 'servers', new.guild.id)).mention} channel.* :slight_smile:'''
    role = discord.utils.get(new.guild.roles, id = get(rl_tokens['-n'], 'servers', new.guild.id))
    await new.add_roles(role)
    await new.guild.get_channel(get(ch_tokens['-wel'], 'servers', new.guild.id)).send(wlcmsg)


''' COC EVENTS '''

async def cocev():

    @client.event
    @coc.ClanEvents.member_role(tags=[tag for tag in saved_clan_tag() if not tag == None])
    async def on_role_updates(old_player, new_player):
        timap = links(saved_guild([new_player.clan.tag]).id)
        if timap and new_player.tag in timap:
            r1 = discord.utils.get(timap[new_player.tag].guild.roles,  id = get())
            r2 = discord.utils.get(timap[new_player.tag].guild.roles, id = int(timap[old_player.tag]))
            if str(old_player.role) == 'Co-Leader':
                r1 = discord.utils.get(timap[new_player.tag].guild.roles,  id = get(ch_tokens['-c'], 'servers', timap[new_player.tag].guild.id))
            else:
                r1 = discord.utils.get(timap[new_player.tag].guild.roles,  id = get(str(old_player.role).lower(), 'servers', timap[new_player.tag].guild.id))

            if str(new_player.role) == 'Co-Leader':
                r1 = discord.utils.get(timap[new_player.tag].guild.roles,  id = get(ch_tokens['-c'], 'servers', timap[new_player.tag].guild.id))
                await timap[new_player.tag].edit(nick = f'[Co] {new_player.name}')
            else:
                r1 = discord.utils.get(timap[new_player.tag].guild.roles,  id = get(str(new_player.role).lower(), 'servers', timap[new_player.tag].guild.id))
                await timap[new_player.tag].edit(nick = f'[{str(new_player.role)}] {new_player.name}')

            await timap[new_player.tag].add_roles(r1)
            await timap[new_player.tag].remove_roles(r2)
    
    @client.event
    @coc.ClanEvents.member_join(tags=[tag for tag in saved_clan_tag() if not tag == None])
    async def foo(player, clan):
        timap = links(saved_guild(clan.tag).id)
        if player.tag in timap:
            for role in timap[player.tag].roles:
                if role.id in [get(i, 'servers',timap[player.tag].id) for i in list(rl_tokens.values())[:4] if not get(i, 'servers',timap[player.tag].id) == None]:
                    if player.name != ' '.join(timap[player.tag].nick.split()[1:]):
                        embed = discord.Embed(
                            title = f"{' '.join(timap[player.tag].nick.split()[1:])} now called {player.name}",
                            description = f'`{timap[player.tag].mention}`',
                            url = player.share_link,
                            color = role.color
                        )
                        embed.set_thumbnail(url = timap[player.tag].avatar_url)
                        await timap[player.tag].edit(nick = f'{timap[player.tag].nick.split()[0]} {player.name}')
                        await timap[player.tag].guild.get_channel(get(ch_tokens['-wel'], 'servers', timap[player.tag].id)).send(embed = embed)
                    break
                elif role.id == get(rl_tokens['-w'], 'servers', timap[player.tag].id):
                    r1 = discord.utils.get(timap[player.tag].guild.roles, id = get(rl_tokens['-m'], 'servers', timap[player.tag].id))
                    r2 = discord.utils.get(timap[player.tag].guild.roles, id = get(rl_tokens['-w'], 'servers', timap[player.tag].id))
                    await timap[player.tag].add_roles(r1)
                    await timap[player.tag].remove_roles(r2)
                    await timap[player.tag].edit(nick = f'[Member] {player.name}')
                    break
            else:
                pass #Future role for guest players joining via discord.
            
    @client.event
    @coc.ClanEvents.member_name(tags=[tag for tag in saved_clan_tag() if not tag == None])
    async def foo(old_player, new_player):
        ti = links(saved_guild(new_player.clan.tag).id)
        if new_player.tag in ti:
            cr = [get(i, 'servers',timap[player.tag].id) for i in list(rl_tokens.values())[:4] if not get(i, 'servers',timap[player.tag].id) == None]
            for dr in ti[new_player.tag].roles:
                if dr.id in cr:
                    if new_player.role == 'Co-Leader':
                        await ti[new_player.tag].edit(nick = f'[Co] {new_player.name}')
                    else:
                        await ti[new_player.tag].edit(nick = f'[{new_player.role}] {new_player.name}')
                    break
     

''' COMMANDS '''

@bot.command(aliases = ['link'])
async def select(ctx, discord_member: discord.Member, player_tag):
    run = False
    for mr in discord_member.roles:
        if mr.id in clan_roles(list(rl_tokens.values())[:3]):
            run = True
            break
    if run:
        player = await client.get_player(player_tag)
        for role in discord_member.roles:
            if role.id == get(rl_tokens['-n'], 'servers', ctx.author.guild.id):
                role = discord.utils.get(discord_member.guild.roles, id=get(rl_tokens['-w'], 'servers', ctx.author.guild.id))
                r2 = discord.utils.get(discord_member.guild.roles, id=get(rl_tokens['-n'], 'servers', ctx.author.guild.id))
                th = player.town_hall
                await discord_member.edit(nick = f'[TH{th}] {player.name}')
                append('players', [discord_member.id, player_tag, ctx.guild.id])
                await discord_member.add_roles(role)
                await discord_member.remove_roles(r2)
                selm = f'''
Hey {discord_member.mention}, **Your base is selected !!!**

**You are now in **waiting list**, if we don't have spot in our clan.

We will dm you a shortlist message if you will be accepted by,

<@&{get(rl_tokens('-l'), 'servers', ctx.author.guild.id)}>, <@&{get(rl_tokens('-c'), 'servers', ctx.author.guild.id)}> or <@&{get(rl_tokens('-e'), 'servers', ctx.author.guild.id)}> of our clan.

Till than checkout our channel make some new friends, we'll select you as

soon as possible if any spot available in our clan.

Feel free to use <#{get(ch_tokens('-hlp'), 'servers', ctx.author.guild.id)}> channel if you have any problem.**

    '''
                await discord_member.guild.get_channel(get(ch_tokens('-wtg'), 'servers', ctx.author.guild.id)).send(selm)
                await ctx.send('**Successfully Selected.**')
                break
        else:
            if discord_member.id in links(discord_member.guild.id, t2m=False): 
                await ctx.send('***This discord member is already linked.***')
            else:
                append(data=f'{discord_member.id} {player_tag}')
                await ctx.send('**Successfully Linked.**')
@select.error
async def foo(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(f'**Usage:** ` {bot.command_prefix}select Discord_Member #Player_Tag `\n**Error:** {error}')
    elif isinstance(error, commands.errors.CommandInvokeError):
        await ctx.send('**Error:** Invalid Player Tag')
    elif isinstance(error, Exception):
        await ctx.send(f'**Error:** {error}')

@bot.command(aliases = ['clean', 'erase'])
async def clear(ctx, lines = 1):
    run = False
    for mr in ctx.author.roles:
        if mr.id in clan_roles(list(rl_tokens.values())[:2]):
            run = True
            break
    if run:
        if lines > 0:
            await ctx.channel.purge(limit = lines+1)
@clear.error
async def foo(ctx, error):
    if isinstance(error, commands.errors.BadArgument):
        await ctx.send(f'**Usage:** ` {bot.command_prefix}clear [no. of lines] `\n**Error:** Invalid Argument! Use a no. not a text.')
    elif isinstance(error, Exception):
        await ctx.send(f'**Error:** {error}')


@bot.command()
async def clan(ctx, clan_tag):
    cln = await client.get_clan(clan_tag)
    val = ''
    for cm in cln.members:
        if str(cm.role) == 'Leader':
            if saved_guild([clan_tag]) != []: timap = links(server_id = saved_guild([clan_tag]).id)
            else: timap = {}
            if cm.tag in timap:
                val = f'{timap[cm.tag].mention} (`{cm.name}`)'
            else:
                val = f'`{cm.name}`'
            break
    det = f':link:**Tag :** `{cln.tag}`\n\n:crossed_swords:**League :** `{cln.war_league}`\n\n:crown:**Leader :** {val}\n\n:arrow_forward:**Link :** [Open Game]({cln.share_link} "{cln.name}")'
    if clan_tag in saved_clan_tag(): 
        nm = ctx.guild.name
        bdg = ctx.guild.icon_url
    else: 
        nm = cln.name
        bdg = cln.badge.url
    if ' ' in str(cln.name):
        coscn = '-'.join(str(cln.name).split())
    else: coscn = nm
    embed = discord.Embed(
        title = nm,
        description = det,
        color = discord.Color.dark_red(),
        url = f'https://www.clashofstats.com/clans/{coscn}-{str(cln.tag)[1:].upper()}/summary'
    )
    embed.set_thumbnail(url = bdg)
    await ctx.send(embed = embed)
@clan.error
async def foo(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(f'**Usage:** `{bot.command_prefix}clan #clan_tag`')
    elif isinstance(error, commands.errors.CommandInvokeError):
        await ctx.send('**Error:** Invalid Clan Tag')
    elif isinstance(error, Exception):
        await ctx.send(f'**Error:** {error}')

@bot.command(aliases = ['remove'])
async def kick(ctx, member : discord.Member, reason = ''):
    run = False
    for mr in member.roles:
        if mr.id in clan_roles(list(rl_tokens.values())[:2]):
            run = True
            break
    if run:
        if member.id in links(server_id = ctx.author.guild.id, t2m=False):
            eject('players', member.id, mg = ctx.author.guild.id)
            await member.kick(reason=reason)
            reason = (lambda reason: 'no reason was given.' if (reason == '') else reason)(reason)
            await ctx.send(f'Successfully kicked `{member.mention}`\n**Reason:** {reason}\n`kicked by {ctx.author}`')
@kick.error
async def foo(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(f'**Usage:** `{bot.command_prefix}kick Discord_Member reason`')
    elif isinstance(error, Exception):
        await ctx.send(f'**Error:** {error}')

@bot.command()
async def accept(ctx, member: discord.Member):
    run = False
    for mr in member.roles:
        if mr.id in clan_roles(list(rl_tokens.values())[:3]):
            run = True
            break
    if run:
        for role in member.roles:
            if role.id == get(rl_tokens['-w'], 'servers', ctx.author.guild.id):
                accE = discord.Embed(
                    title = f'**{ctx.author.guild.name}**',
                    description = f"\nHey {member.mention},\n\n**You are shortlisted to be a member of our Clan !!!**\n\nYou will have invite send from our clan if not\njust ask it with the screenshot of this message\nin {member.guild.get_channel(get(ch_tokens['-hlp'], 'servers', ctx.author.guild.id)).mention} channel of our discord server." ,
                    url = 'https://discord.gg/DZYbQHs7cd'        
                )
                await member.send(embed=accE)
                await ctx.send('**Successfully Accepted.**')
                break
        else:
            await ctx.send(f'**Error:** member {member.mention} is not in [WaitingList]')
@accept.error
async def foo(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(f'**Usage:** `{bot.command_prefix}accept <member of waiting list>`\n**Error:** {error}')
    elif isinstance(error, Exception):
        await ctx.send(f'**Error:** {error}')
    

@bot.command()
async def ping(ctx):
    await ctx.send('Pong '+ str(round(bot.latency*1000))+'ms')


bot.loop.create_task(cocev())
bot.run(os.environ['BH-BOT_Token'])