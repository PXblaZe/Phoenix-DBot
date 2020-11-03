import os
import coc
import asyncio
import discord
from github import Github
from discord.ext import commands


client  = coc.login(os.environ['gmail'], os.environ['COC-API_pass'], client=coc.EventsClient)
bot = commands.Bot(command_prefix = '-', intents = discord.Intents.all())

g = Github(os.environ['git_token-BH'])
repo = g.get_user().get_repo('DiscordBot')



def append(data: str, file = 'Data.bh', index = -1):
    cnts = repo.get_contents(file)
    lines = cnts.decoded_content.decode().split('\n')
    lines.insert(index, data)
    repo.update_file(cnts.path, f'appended new member data at index {index}', '\n'.join(lines), cnts.sha)

def links(server_id = os.environ['BH-serv_id'], file = 'Data.bh', t2m = True):
    mapin = dict()
    server_id = int(server_id)
    cnts = repo.get_contents(file)
    read = cnts.decoded_content.decode()
    guild = bot.get_guild(server_id)
    for i in read.split('\n')[:-1]:
        uid, tg = i.split()
        if t2m: mapin[tg] = guild.get_member(int(uid))
        else: mapin[int(uid)] = tg
    return mapin


'''Discord EVENTS '''

@bot.event
async def on_ready():
    print('Bot is ready...')

@bot.event
async def on_member_join(new : discord.Member):

    wlcmsg = f'''Hey {new.mention}, Welcome to  :broken_heart: Broken Hearts\** :broken_heart: !
    **
    We only accept <:th10:769275244262588437>TH10, <:th11:769275245152043048>TH11, <:th12:769291986221924412>TH12 and <:th13:769292071692795966>TH13 !

    If you are interested to join our clan do the following:

      1.** Send a screenshot of your in game profile, with your player tag visible.
    **2.** Send your player tag in text form. 
    **3.** Send a screenshot of your base. It must be in a war base slot.
    **4.** Wait for an answer from one of the staff.

   *If you need any help ask it in {new.guild.get_channel(765501711694954518).mention} channel.* :slight_smile:'''
    role = discord.utils.get(new.guild.roles, name = '[new]')
    await new.add_roles(role)
    await new.guild.get_channel(765497400398708737).send(wlcmsg)


''' COC EVENTS '''

async def cocev():

    @client.event
    @coc.ClanEvents.member_role(tags=["#229Y8VYP2"])
    async def on_role_updates(old_player, new_player):
        timap = links()
        if str(new_player.tag) in timap:
            if str(old_player.role) == 'Co-Leader':
                r2 = discord.utils.get(timap[new_player.tag].guild.roles, name = f'[{old_player.role[:2]}]')
            else:
                r2 = discord.utils.get(timap[new_player.tag].guild.roles, name = f'[{old_player.role}]')
            
            if str(new_player.role) == 'Co-Leader':
                r1 = discord.utils.get(timap[new_player.tag].guild.roles, name = f'[{new_player.role[:2]}]')
                await timap[new_player.tag].edit(nick = f'[{new_player.role[:2]}] {new_player.name}')
            else:
                r1 = discord.utils.get(timap[new_player.tag].guild.roles, name = f'[{new_player.role}]')
                await timap[new_player.tag].edit(nick = f'[{new_player.role}] {new_player.name}')
            await timap[new_player.tag].add_roles(r1)
            await timap[new_player.tag].remove_roles(r2)
    
    @client.event
    @coc.ClanEvents.member_join(tags=["#229Y8VYP2"])
    async def foo(player, clan):
        timap = links()
        if str(player.tag) in timap:
            r1 = discord.utils.get(timap[player.tag].guild.roles, name = '[Member]')
            r2 = discord.utils.get(timap[player.tag].guild.roles, name = '[WaitingList]')
            await timap[player.tag].add_roles(r1)
            await timap[player.tag].remove_roles(r2)
            await timap[player.tag].edit(nick = f'[Member] {player.name}')

    @client.event
    @coc.ClanEvents.member_name(tags=["#229Y8VYP2"])
    async def foo(old_name, new_name, player):
        ti = links()
        if str(player.tag) in ti:
            cr = ['[Leader]', '[Co]', '[Elder]', '[Member]']
            for dr in ti[player.tag].roles:
                if dr.name in cr:
                    await ti[player.tag].edit(nick = f'{dr.name} {new_name}')
                    break
     

''' COMMANDS '''

@commands.has_any_role('[Admin]', '[Leader]', '[Co]', '[Elder]')
@bot.command(aliases = ['link'])
async def select(ctx, discord_member: discord.Member, player_tag):
    player = await client.get_player(player_tag)
    for role in discord_member.roles:
        if role.name == '[new]':
            role = discord.utils.get(discord_member.guild.roles, name="[WaitingList]")
            r2 = discord.utils.get(discord_member.guild.roles, name="[new]")
            th = player.town_hall
            await discord_member.edit(nick = f'[TH{th}] {player.name}')
            append(data = f'{discord_member.id} {player_tag}')
            await discord_member.add_roles(role)
            await discord_member.remove_roles(r2)
            selm = f'''
Hey {discord_member.mention}, **Your base is selected !!!**

**You are now in <@&765500587269292032>, if we don't have spot in our clan.

We will dm you a shortlist message if you will be accepted by,

<@&769125392916676608>, <@&769116913234083850> or <@&765480944416981023> of our clan.

Till than checkout our channel make some new friends, we'll select you as

soon as possible if any spot available in our clan.

Feel free to use {discord_member.guild.get_channel(765501711694954518).mention} channel if you have any problem.**

'''
            await discord_member.guild.get_channel(765502125283082270).send(selm)
            await ctx.send('**Successfully Selected.**')
            break
    else:
        if discord_member.id in links(t2m=False): 
            await ctx.send('***This discord member is already linked.***')
        else:
            append(data=f'{discord_member.id} {player_tag}')
            await ctx.send('**Successfully Linked.**')
@select.error
async def foo(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(f'**Usage:** ` {bot.command_prefix}clan Discord_Member #Player_Tag `\n**Error:** {error}')
    elif isinstance(error, commands.errors.CommandInvokeError):
        await ctx.send('**Error:** Invalid Player Tag')
    elif isinstance(error, Exception):
        await ctx.send(f'**Error:** {error}')

@commands.has_any_role('[Admin]', '[Leader]', '[Co]')
@bot.command(aliases = ['clean', 'erase'])
async def clear(ctx, lines = 1):
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
            timap = links()
            if cm.tag in timap:
                val = f'{timap[cm.tag].mention} (`{cm.name}`)'
            else:
                val = f'`{cm.name}`'
            break
    det = f':link:**Tag :** `{cln.tag}`\n\n:crossed_swords:**League :** `{cln.war_league}`\n\n:crown:**Leader :** {val}\n\n:arrow_forward:**Link :** [Open Game]({cln.share_link} "{cln.name}")'
    if str(cln.tag) == '#229Y8VYP2': 
        nm = '💔 BROKEN HEARTS\** 💔'
        bdg = "https://cdn.discordapp.com/icons/764594921931276338/e901edd95e3e9e69d433ca02f70e8759.png?size=128"
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


@commands.has_any_role('[Admin]', '[Leader]', '[Co]')
@bot.command(aliases = ['remove'])
async def kick(ctx, member : discord.Member, reason = ''):
    guild = bot.get_guild(os.environ['BH-serv_id'])
    if member.id in links(t2m=False):
        ct = repo.get_contents('Data.bh')
        lines = ct.decoded_content.decode().split('\n')
        for target in lines:
            if target.startswith(str(member.id)): 
                lines.remove(target)
                repo.update_file(ct.path,f'kicked a member with id {member.id}', '\n'.join(lines), ct.sha)
                break
    await member.kick(reason=reason)
    reason = (lambda reason: 'no reason was given.' if (reason == '') else reason)(reason)
    await ctx.send(f'Successfully kicked {member.mention}\n**Reason:** {reason}\n`kicked by {ctx.author}`')
@kick.error
async def foo(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(f'**Usage:** `{bot.command_prefix}kick Discord_Member reason`')
    elif isinstance(error, Exception):
        await ctx.send(f'**Error:** {error}')

@commands.has_any_role('[Admin]', '[Leader]', '[Co]', '[Elder]')    
@bot.command()
async def accept(ctx, member: discord.Member):
    for role in member.roles:
        if role.name == '[WaitingList]':
            accE = discord.Embed(
                title = '💔 BROKEN HEARTS\** 💔',
                description = f'\nHey {member.mention},\n\n**You are shortlisted to be a member of our Clan !!!**\n\nYou will have invite send from our clan if not\njust ask it with the screenshot of this message\nin {member.guild.get_channel(765501711694954518).mention} channel of our discord server.',
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
