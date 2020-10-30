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

def readlines(file = 'Data.bh'):
    cnts = repo.get_contents(file)
    read = cnts.decoded_content.decode()
    return read.split('\n')[:-1]

def edit(file = 'Data.bh', data = ''):
    cnts = repo.get_contents(file)
    repo.update_file(cnts.path, 'commit', f'{cnts.decoded_content.decode()}{data}', cnts.sha)

def link(server_id = os.environ['BH-serv_id'], file = 'Data.bh', t2m = True):
    mapin = dict()
    server_id = int(server_id)
    cnts = repo.get_contents(file)
    read = cnts.decoded_content.decode()
    guild = bot.get_guild(server_id)
    for i in read.split('\n')[:-1]:
        uid, tg = i.split()
        if t2m:
            mapin[tg] = guild.get_member(int(uid))
        else: mapin[int(uid)] = tg
    return mapin



''' EVENTS '''

@bot.event
async def on_ready():
    print('Bot is ready...')

    
''' COC EVENTS '''

async def cocev():

    @client.event
    @coc.ClanEvents.member_role(tags=["#229Y8VYP2"])
    async def on_role_updates(old_player, new_player):
        timap = link()
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
        timap = link()
        if str(player.tag) in timap:
            r1 = discord.utils.get(timap[player.tag].guild.roles, name = '[Member]')
            r2 = discord.utils.get(timap[player.tag].guild.roles, name = '[WaitingList]')
            await timap[player.tag].add_roles(r1)
            await timap[player.tag].remove_roles(r2)
            await timap[player.tag].edit(nick = f'[Member] {player.name}')

    @client.event
    @coc.ClanEvents.member_name(tags=["#229Y8VYP2"])
    async def foo(old_name, new_name, player):
        ti = link()
        if str(player.tag) in ti:
            cr = ['[Leader]', '[Co]', '[Elder]', '[Member]']
            for dr in ti[player.tag].roles:
                if dr.name in cr:
                    await ti[player.tag].edit(nick = f'{dr.name} {new_name}')
                    break

     

''' COMMANDS '''

@commands.has_any_role('[Admin]', '[Leader]', '[Co]')
@bot.command()
async def select(ctx, discord_member: discord.Member, player_tag):
    role = discord.utils.get(discord_member.guild.roles, name="[WaitingList]")
    r2 = discord.utils.get(discord_member.guild.roles, name="[new]")
    player = await client.get_player(player_tag)
    th = player.town_hall
    await discord_member.edit(nick = f'[TH{th}] {player.name}')
    edit(data = f'{discord_member.id} {player_tag}\n')
    await discord_member.add_roles(role)
    await discord_member.remove_roles(r2)
    await ctx.send('Successfully Selected.')

@select.error
async def foo(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(f'Usage: ` {bot.command_prefix}clan Discord_Menber #Player_Tag `\nError: {error}')
    elif isinstance(error, commands.errors.CommandInvokeError):
        await ctx.send('Invalid Player Tag')
    elif isinstance(error, Exception):
        await ctx.send(f'Error: {error}')

@commands.has_any_role('[Admin]', '[Leader]', '[Co]')
@bot.command(aliases = ['clean', 'erase'])
async def clear(ctx, lines = 1):
    if lines > 0:
        await ctx.channel.purge(limit = lines+1)

@bot.command()
async def clan(ctx, clan_tag):
    cln = await client.get_clan(clan_tag)
    val = ''
    for cm in cln.members:
        if str(cm.role) == 'Leader':
            timap = link()
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
        await ctx.send(f'Usage: ` {bot.command_prefix}clan #clan_tag `\nError: {error}')
    elif isinstance(error, commands.errors.CommandInvokeError):
        await ctx.send('Invalid Clan Tag')
    elif isinstance(error, Exception):
        await ctx.send(f'Error: {error}')
@bot.command()
async def ping(ctx):
    await ctx.send('Pong '+ str(round(bot.latency*1000))+'ms')


bot.loop.create_task(cocev())
bot.run(os.environ['BH-BOT_Token'])
