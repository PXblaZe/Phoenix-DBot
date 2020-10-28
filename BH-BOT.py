import os
import coc
import asyncio
import discord
from github import Github
from discord.ext import commands

client  = coc.login(os.environ['gmail'], os.environ['COC-API_pass'], client=coc.EventsClient)
bot = commands.Bot(command_prefix = '>', intents = discord.Intents.all())

g = Github(os.environ['git_token-BH'])
repo = g.get_user().get_repo('DiscordBot')

def readlines(file = 'Data.bh'):
    cnts = repo.get_contents(file)
    read = cnts.decoded_content.decode()
    return read.split('\n')[:-1]

def edit(file = 'Data.bh', data = ''):
    cnts = repo.get_contents(file)
    repo.update_file(cnts.path, 'commit', f'{cnts.decoded_content.decode()}{data}', cnts.sha)


''' EVENTS '''

@bot.event
async def on_ready():
    print('Bot is ready...')

    
''' COC EVENTS '''

async def cocev():

    @client.event
    @coc.ClanEvents.member_role(tags=["#229Y8VYP2"])
    async def on_role_updates(old_player, new_player):
        timap = {}
        for i in readlines():
            uid, ptg = i.split()
            guild = bot.get_guild(int(os.environ['BH-serv_id']))
            timap[ptg] = guild.get_member(int(uid))
        
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
        timap = {}
        for i in readlines():
            uid, ptg = i.split()
            guild = bot.get_guild(int(os.environ['BH-serv_id']))
            timap[ptg] = guild.get_member(int(uid))
        if str(player.tag) in timap:
            r1 = discord.utils.get(timap[player.tag].guild.roles, name = '[Member]')
            r2 = discord.utils.get(timap[player.tag].guild.roles, name = '[WaitingList]')
            await timap[player.tag].add_roles(r1)
            await timap[player.tag].remove_roles(r2)
            await timap[player.tag].edit(nick = f'[Member] {player.name}')

''' COMMANDS '''

@commands.has_any_role('[Admin]', '[Leader]', '[Co]')
@bot.command()
async def select(ctx, member: discord.Member, player_tag):
    role = discord.utils.get(member.guild.roles, name="[WaitingList]")
    r2 = discord.utils.get(member.guild.roles, name="[new]")
    await member.add_roles(role)
    await member.remove_roles(r2)
    player = await client.get_player(player_tag)
    th = player.town_hall
    await member.edit(nick = f'[TH{th}] {player.name}')
    edit(data = f'{member.id} {player_tag}\n')
    await ctx.send('Successfully Selected.')
    
@commands.has_any_role('[Admin]', '[Leader]', '[Co]')
@bot.command(aliases = ['clean', 'erase'])
async def clear(ctx, lines = 1):
    if lines > 0:
        await ctx.channel.purge(limit = lines+1)

@bot.command()
async def clan(ctx, tag):
    cln = await client.get_clan(tag)
    val = ''
    for cm in cln.members:
        if str(cm.role) == 'Leader':
            timap = {}
            for i in readlines():
                uid, ptg = i.split()
                guild = bot.get_guild(int(os.environ['BH-serv_id']))
                timap[ptg] = guild.get_member(int(uid))
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

@bot.command()
async def ping(ctx):
    await ctx.send('Pong '+ str(round(bot.latency*1000))+'ms')


bot.loop.create_task(cocev())
bot.run(os.environ['BH-BOT_Token'])
