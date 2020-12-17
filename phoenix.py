#create help command for setup.
#create help command for prefix.
#testing COC events.
import os
import coc
import discord
import pymysql
from discord.ext import commands

condb = pymysql.connect(
    host = os.environ['DBhost'],
    user = os.environ['DBuser'],
    password = os.environ['DBpass'],
    db = os.environ['DB'],
    cursorclass=pymysql.cursors.DictCursor
)

async def get_prefix(bot, message):
    with condb.cursor() as cur:
        cur.execute("select guild_id, prefix from prefixes")
        fetch = cur.fetchall()
    for fd in fetch:
        if fd['guild_id'] == str(message.guild.id): return fd['prefix']
    else: return '-'

client  = coc.login(os.environ['gmail'], os.environ['COC-API_pass'], client=coc.EventsClient)
bot = commands.Bot(command_prefix = get_prefix, help_command = None, intents = discord.Intents.all())

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

def append(table: str, data: list, column = ''):
    try:
        if type(data) in [list, tuple]:
            if column == '' and len(data) in [len(ch_tokens)+len(rl_tokens), 3, 2] :
                val = '('
                for i in data: val += f"'{i}', "
                else: val = val[:-2]+')'
                with condb.cursor() as cur:
                    cur.execute(f"insert into {table.lower()} values{val}")
            elif type(column) in [tuple, list] and len(column) == len(data):
                if (table.lower() == 'servers' and len(column) <= len(ch_tokens)+len(rl_tokens)) or (table.lower() == 'players' and len(column) <= 3) or (table.lower() == 'prefixes' and len(column) <= 2):
                    clm = dt = '('
                    for i in range(len(data)):
                        clm += f"{column[i]}, "
                        dt += f"'{data[i]}', "
                    else: 
                        clm = clm[:-2]+')'
                        dt = dt[:-2]+')'
                    with condb.cursor() as cur:
                        cur.execute(f"insert into {table.lower()}{clm} values{dt}")
    except pymysql.err.IntegrityError as e: flag = False
    except Exception as e: 
        flag = False
        print('AppendError:', e)
    else: flag = True
    finally:
        condb.commit()
        return flag

def update(table: str, column: str, value: str, id: str):
    try:
        if table.lower() in ['servers', 'prefixes']:
            with condb.cursor() as cur:
                cur.execute(f"UPDATE {table.lower()} SET {column} = '{value}' WHERE guild_id = '{id}'")
        elif table.lower() == 'players':
            with condb.cursor() as cur:
                cur.execute(f"UPDATE players SET {column} = '{value}' WHERE member = '{id}'")
    except Exception as e: 
        flag = False
        print('UpdateError: ', e)
    else: flag = True
    finally: 
        condb.commit()
        return flag

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
            fetch = cur.fetchall()
            for clantag in fetch:
                clans.append(clantag['clan_tag'])
        if len(clans) == 1: return clans[0]
        else: return clans
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
@commands.has_permissions(administrator=True)
async def setup(ctx):
    if not ctx.author.guild in saved_guild():
        append(table='servers', column=['guild_id'], data=[ctx.author.guild.id])

@setup.command(aliases = ['ch'])
@commands.has_permissions(administrator=True)
async def channel(ctx, *, arg):
    tknsl = arg.split()
    it = list()
    if not len(tknsl)%2 and tknsl:
        tknsl = dict([j for j in [tuple([tknsl[i+1], tknsl[i][2:-1]]) if tknsl[i+1] in ch_tokens else it.append(tknsl[i+1]) for i in range(0,len(tknsl),2)] if j])
    else: tknsl = {}
    for tkn in tknsl:
        if ctx.guild.get_channel(int(tknsl[tkn])):
            update('servers', ch_tokens[tkn], tknsl[tkn], ctx.author.guild.id)
    else: 
        if tknsl: 
            await ctx.send('**Updated Channel(s):**\n'+'\n'.join([ch_tokens[i].capitalize()+' --> <#'+tknsl[i]+'>' for i in tknsl]))
        else:
            if arg: await ctx.send('**Error:** Invalid Input. !!!')
        if it: await ctx.send(f'**Invalid token(s):** {", ".join(it)}')
@channel.error
async def foo(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.invoke(bot.get_command('help', ['setup',]))
    elif isinstance(error, commands.errors.CommandInvokeError):
        await ctx.send('**Error:** Invalid Channel(s).')

@setup.command(aliases = ['rl'])
@commands.has_permissions(administrator=True)
async def role(ctx, *, arg):
    tknsl = arg.split()
    it = list()
    if not len(tknsl)%2 and tknsl:
        tknsl = dict([j for j in [tuple([tknsl[i+1], tknsl[i][3:-1]]) if tknsl[i+1] in rl_tokens else it.append(tknsl[i+1]) for i in range(0,len(tknsl),2)] if j])
    else: tknsl = {}
    for tkn in tknsl:
        if ctx.guild.get_role(int(tknsl[tkn])):
            update('servers', rl_tokens[tkn], tknsl[tkn], ctx.author.guild.id)
    else: 
        if tknsl: 
            await ctx.send('**Updated Role(s): **\n'+'\n'.join([rl_tokens[i].capitalize()+' --> <@&'+tknsl[i]+'>' for i in tknsl]))
        else:
            await ctx.send('**Error:** Invalid Input. !!!')
        if it: await ctx.send(f'**Invalid token(s):** {", ".join(it)}')
@role.error
async def foo(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.invoke(bot.get_command('help setup role'))
    elif isinstance(error, commands.errors.CommandInvokeError):
        await ctx.send('**Error:** Invalid role(s).')

@setup.command(aliases = ['clan', 'clan_tag'])
@commands.has_permissions(administrator=True)
async def tag(ctx, tag: str):
    if tag[0] == '#':
        if await client.get_clan(tag) and not tag in saved_clan_tag():
            update('servers', 'clan_tag', tag, ctx.guild.id)
            await ctx.send('**Done**')
        else:
            await ctx.send('**Clan tag is Invalid or Already used by a Server.**')
    else:
        await ctx.send('**Error:** Clan tag must be starts with "#"')
@tag.error
async def foo(ctx, error):
    if isinstance(error, commands.errors.CommandInvokeError):
        await ctx.send('**Error:** Invaild clan tag !!!')
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send('**Error:** Clan tag not found.')

@setup.command(aliases = ['edit'])
@commands.has_permissions(administrator=True)
async def all(ctx, *, arg):
    tknsl, rl, ch, it = arg.split(), tuple(), tuple(), tuple()
    for i in range(len(tknsl)):
        if tknsl[i] in ch_tokens: ch += tknsl[i-1], tknsl[i],
        elif tknsl[i] in rl_tokens: rl += tknsl[i-1], tknsl[i],
        elif i%2: it += tknsl[i],
    if ch and not len(ch)%2: await ctx.invoke(bot.get_command('setup ch'), arg = ' '.join(ch))
    if rl and not len(rl)%2: await ctx.invoke(bot.get_command('setup rl'), arg = ' '.join(rl))
    if it: await ctx.send(f'**Invalid token(s):** {", ".join(it)}')
@all.error
async def foo(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.invoke(bot.get_command('help setup all'))
    elif isinstance(error, commands.errors.CommandInvokeError):
        await ctx.send('**Error:** Either role(s) or channel(s) is Invalid.')

'''Discord EVENTS '''

@bot.event
async def on_ready():
    await bot.change_presence( activity = discord.Activity(name = 'BraZZerS', type = discord.ActivityType.watching))
    print('Bot is ready...')

@bot.event    
async def on_message(message: discord.Message):
    cntl = message.content.split()
    if len(cntl) in [2, 3] and cntl[0][2:-1] == str(bot.user.id) and (cntl[1].lower() in ['prefix', 'set', 'set_prefix', 'setprefix']):
        if len(cntl) == 2: cntl.append('')
        if append('prefixes', [message.guild.id, cntl[2]]): 
            await message.channel.send(f'Prefix changed to `{(lambda para: None if not para else para)(cntl[2])}`')
        else: 
            update('prefixes', 'prefix', cntl[2], message.guild.id)
            await message.channel.send(f'Prefix changed to `{(lambda para: None if not para else para)(cntl[2])}`')
    else: await bot.process_commands(message)     

@bot.event
async def on_member_join(new : discord.Member):
    wlcmsg = f'''Hey {new.mention}, WelCome to **{new.guild.name}** !
**
We only accept <:th10:769275244262588437>TH10, <:th11:769275245152043048>TH11, <:th12:769291986221924412>TH12 and <:th13:769292071692795966>TH13 !

If you are interested to join our clan do the following:

1.** Send a screenshot of your in game profile, with your player tag visible.
**2.** Send your player tag in text form. 
**3.** Send a screenshot of your base. It must be in a war base slot.
**4.** Wait for an answer from one of the staff.

*If you need any help ask it in <#{get(ch_tokens['-hlp'], 'servers', new.guild.id)}> channel.* :slight_smile:'''
    role = discord.utils.get(new.guild.roles, id = get(rl_tokens['-n'], 'servers', new.guild.id))
    await new.add_roles(role)
    await new.guild.get_channel(get(ch_tokens['-wel'], 'servers', new.guild.id)).send(wlcmsg)


''' COC EVENTS '''

async def cocev():
    @client.event
    @coc.ClanEvents.member_role(tags=[tag for tag in saved_clan_tag() if not tag == None])
    async def on_role_updates(old_player, new_player):
        if saved_guild([new_player.clan.tag]):
            timap = links(saved_guild([new_player.clan.tag]).id)
        else: return
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
        if saved_guild([clan.tag]):
            timap = links(saved_guild([clan.tag]).id)
        else: return
        if player.tag in timap:
            for role in timap[player.tag].roles:
                if role.id in [get(i, 'servers',timap[player.tag].id) for i in list(rl_tokens.values())[:4] if not get(i, 'servers',timap[player.tag].id) == None]:
                    if player.name != ' '.join(timap[player.tag].nick.split()[1:]):
                        embed = discord.Embed(
                            title = f"{' '.join(timap[player.tag].nick.split()[1:])} now called {player.name}",
                            description = f'`{timap[player.tag].name}#{timap[player.tag].discriminator}`',
                            url = player.share_link,
                            color = timap[player.tag].color
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
        if saved_guild([new_player.clan.tag]):
            ti = links(saved_guild([new_player.clan.tag]).id)
        else: return
        if new_player.tag in ti:
            cr = [get(i, 'servers',timap[player.tag].id) for i in list(rl_tokens.values())[:4] if not get(i, 'servers',timap[player.tag].id) == None]
            for dr in ti[new_player.tag].roles:
                if dr.id in cr:
                    if new_player.role == 'Co-Leader':
                        await ti[new_player.tag].edit(nick = f'[Co] {new_player.name}')
                    else:
                        await ti[new_player.tag].edit(nick = f'[{new_player.role}] {new_player.name}')
                    break


''' HELP COMMAND '''

@bot.command()
async def help(ctx: commands.Context, *, command = None):
    cmd_names = [command.name for command in bot.commands]
    help_embed = discord.Embed(
        title = '**HELP COMMAND**' if command == None else command.upper() if bot.get_command(command.lower()) in bot.commands else 'COMMAND NOT FOUND !!!',
        color = ctx.author.color
    )
    if not command:
        help_embed.add_field(
            name="**List of supported commands:**",
            value='```\n'+f'1. <mention_bot>prefix [new_prefix]\n'+"\n".join([f'{i+2}. {ctx.prefix + x.name} {x.signature}' for i, x in enumerate(bot.commands)])+'\n```',
            inline=False
        )
        help_embed.add_field(
            name="Details",
            value=f"Type `{ctx.prefix}help [command name]` for more details about each command.",
            inline=False
        )
    elif bot.get_command(command.lower()) in bot.commands:
        cmd = bot.get_command(command.lower())
        if command.lower() == 'setup':
            ct = '''
abc
                 '''
            help_embed.add_field(
                name=f'**{ctx.prefix}<channel|ch> **',
                value=ct,
            )
            ch = 'abc'
            help_embed.add_field(
                name='**Channels**',
                value=ch,
            )
            rl = 'abc'
            help_embed.add_field(
                name='**Roles**',
                value=rl,
            )
            usg = '''
abc
                  '''
            help_embed.add_field(
                name='**Usage**',
                value=usg,
                inline=False
            )
        else:
            help_embed.add_field(
                name='Usage:',
                value='`'+str(cmd.help)+'`',
                inline=False
            )
            cn = lambda x: f'<{x.name}>' if not len(x.aliases) else f'<{x.name+"|"+"|".join(x.aliases)}>'
            help_embed.add_field(
                name='Syntex:',
                value=f'`{ctx.prefix+cn(cmd)} {cmd.signature}`',
                inline=False
            )
    help_embed.set_thumbnail(url = bot.user.avatar_url)
    help_embed.set_footer(text=f"{ctx.author.name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar_url)
    await ctx.send(embed = help_embed) 


''' COMMANDS '''

@bot.command(aliases = ['link'])
async def select(ctx, discord_member: discord.Member, player_tag):
    run = False
    for mr in ctx.author.roles:
        if mr.id in clan_roles(list(rl_tokens.values())[:3]):
            run = True
            break
    if run:
        player = await client.get_player(player_tag)
        for role in discord_member.roles:
            if role.id == get(rl_tokens['-n'], 'servers', ctx.guild.id):
                role = discord.utils.get(discord_member.guild.roles, id=get(rl_tokens['-w'], 'servers', ctx.guild.id))
                r2 = discord.utils.get(discord_member.guild.roles, id=get(rl_tokens['-n'], 'servers', ctx.guild.id))
                th = player.town_hall
                await discord_member.edit(nick = f'[TH{th}] {player.name}')
                append('players', [discord_member.id, player_tag, ctx.guild.id])
                await discord_member.add_roles(role)
                await discord_member.remove_roles(r2)
                selm = f'''
Hey {discord_member.mention}, **Your base is selected !!!

You are now in waiting list, if we don't have spot in our clan.

We will dm you a shortlist message if you will be accepted by,

<@&{get(rl_tokens['-l'], 'servers', ctx.guild.id)}>, <@&{get(rl_tokens['-c'], 'servers', ctx.guild.id)}> or <@&{get(rl_tokens['-e'], 'servers', ctx.guild.id)}> of our clan.

Till than checkout our channel make some new friends, we'll select you 
as soon as possible if any spot available in our clan.

Feel free to use <#{get(ch_tokens['-hlp'], 'servers', ctx.guild.id)}> channel if you have any problem.**
'''
                await discord_member.guild.get_channel(get(ch_tokens['-wtg'], 'servers', ctx.guild.id)).send(selm)
                await ctx.send('**Successfully Selected.**')
                break
        else:
            if discord_member.id in links(discord_member.guild.id, t2m=False): 
                await ctx.send(f'{discord_member.display_name} ***is already linked.***')
            else:
                append('players', [discord_member.id, player_tag,ctx.guild.id])
                await ctx.send('**Successfully Linked.**')
@select.error
async def foo(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(f'**Usage:** ` {ctx.prefix}select Discord_Member #Player_Tag `\n**Error:** {error}')
    elif isinstance(error, commands.errors.CommandInvokeError):
        await ctx.send('**Error:** Invalid Player Tag')
    elif isinstance(error, Exception):
        await ctx.send(f'**Error:** {error}')

@bot.command(aliases = ['clean', 'erase'])
async def clear(ctx, lines = None):
    if not lines: lines = 1 
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
        await ctx.send(f'**Usage:** ` {ctx.prefix}clear [no. of lines] `\n**Error:** Invalid Argument! Use a no. not a text.')
    elif isinstance(error, Exception):
        await ctx.send(f'**Error:** {error}')


@bot.command(help = 'Shows clan details and provide ClashOfStats and clan url of the clan_tag.')
async def clan(ctx, clan_tag):
    cln = await client.get_clan(clan_tag)
    val = ''
    for cm in cln.members:
        if str(cm.role) == 'Leader':
            if saved_guild([clan_tag]) != []: timap = links(saved_guild([clan_tag]).id)
            else: timap = {}
            if cm.tag in timap and ctx.guild == saved_guild([clan_tag]):
                val = f'{timap[cm.tag].mention} (`{cm.name}`)'
            else:
                val = f'`{cm.name}`'
            break
    det = f':link:**Tag :** `{cln.tag}`\n\n:crossed_swords:**League :** `{cln.war_league}`\n\n:crown:**Leader :** {val}\n\n:arrow_forward:**Link :** [Open Game]({cln.share_link} "{cln.name}")'
    if clan_tag in saved_clan_tag() and ctx.guild == saved_guild([clan_tag]): 
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
        await ctx.send(f'**Usage:** `{ctx.prefix}clan #clan_tag`')
    elif isinstance(error, commands.errors.CommandInvokeError):
        await ctx.send('**Error:** Invalid Clan Tag')
    elif isinstance(error, Exception):
        await ctx.send(f'**Error:** {error}')

@bot.command(aliases = ['remove'], help = 'Used to kick a member from server and erase his/her data.')
async def kick(ctx, member : discord.Member, *, reason = ''):
    run = False
    for mr in ctx.author.roles:
        if mr.id in clan_roles(list(rl_tokens.values())[:2]):
            run = True
            break
    if run:
        if member.id in links(server_id = ctx.author.guild.id, t2m=False):
            eject('players', member.id, mg = ctx.author.guild.id)
            await member.kick(reason=reason)
            reason = (lambda reason: 'no reason was given.' if (reason == '') else reason)(reason)
            await ctx.send(f'Successfully kicked {member.display_name}\n**Reason:** {reason}\nkicked by {ctx.author.mention}')
@kick.error
async def foo(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(f'**Usage:** `{ctx.prefix}kick Discord_Member reason`')
    elif isinstance(error, Exception):
        await ctx.send(f'**Error:** {error}')

@bot.command(help = 'Used to DM a member that he/she is accepted in the clan.')
async def accept(ctx, member: discord.Member):
    run = False
    for mr in ctx.author.roles:
        if mr.id in clan_roles(list(rl_tokens.values())[:3]):
            run = True
            break
    if run:
        for role in member.roles:
            if role.id == get(rl_tokens['-w'], 'servers', ctx.author.guild.id):
                clan = await client.get_clan(saved_clan_tag([ctx.guild.id]))
                accE = discord.Embed(
                    title = f'**{ctx.guild.name}**',
                    description = f"\nHey {member.mention},\n\n**You are shortlisted to be a member of our Clan !!!**\n\nYou will have invite send from our clan if not\njust ask it with the screenshot of this message\nin {member.guild.get_channel(get(ch_tokens['-hlp'], 'servers', ctx.author.guild.id)).mention} channel of our discord server." ,
                    url = clan.share_link      
                )
                await member.send(embed=accE)
                await ctx.send('**Successfully Accepted.**')
                break
        else:
            await ctx.send(f'**Error:** member {member.mention} is not in Waiting List')
@accept.error
async def foo(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(f'**Usage:** `{ctx.prefix}accept <member of waiting list>`\n**Error:** {error}')
    elif isinstance(error, Exception):
        await ctx.send(f'**Error:** {error}')
    

@bot.command(help = "Shows the ping/latency of the bot in miliseconds.")
async def ping(ctx):
    await ctx.send('Pong '+ str(round(bot.latency*1000))+'ms')

@bot.command(help = 'Invoke a given command by bot.')
async def invoke(ctx, *,text = ''):
    tokens = text.split()
    await ctx.invoke(bot.get_command(tokens[0]), *tokens[1:])

if __name__ == '__main__':
    try:
        bot.loop.create_task(cocev())
        bot.run(os.environ['BH-BOT_Token'])
    except coc.errors.GatewayError as e: print('MainError:', e)
