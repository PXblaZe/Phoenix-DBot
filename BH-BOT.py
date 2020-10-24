import os
import coc
import asyncio
import discord
from discord.ext import commands
client  = coc.login( os.environ['email'], os.environ['pass'], client=coc.EventsClient)

bot = commands.Bot(command_prefix = '>', intents = discord.Intents.all())


''' EVENTS '''

@bot.event
async def on_ready():
    print('Bot is ready...')

    
''' COC EVENTS '''

async def cocev():



    @client.event
    @coc.ClanEvents.member_role(tags=["#229Y8VYP2"])
    async def on_role_updates(old_player, new_player):
        file = open('Data.bh', 'r')
        timap = {}
        for i in file.readlines():
            uid, ptg = i.split()
            guild = bot.get_guild(764594921931276338)
            timap[ptg] = guild.get_member(int(uid))
        file.close()
        
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
        file = open('Data.bh', 'r')
        timap = {}
        for i in file.readlines():
            uid, ptg = i.split()
            guild = bot.get_guild(764594921931276338)
            timap[ptg] = guild.get_member(int(uid))
        file.close()
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
    file = open('Data.bh', 'a+')
    file.write(f'{member.id} {player_tag}\n')
    file.close()
    await bot.get_channel(765497400398708737).send('Successfully Selected.')
       
    
@commands.has_any_role('[Admin]', '[Leader]', '[Co]')
@bot.command(aliases = ['clean', 'erase'])
async def clear(ctx, lines = 1):
    if lines > 0:
        await ctx.channel.purge(limit = lines+1)

@bot.command()
async def ping(ctx):
    await ctx.send('Pong '+ str(round(bot.latency*1000))+'ms')


bot.loop.create_task(cocev())
bot.run(os.environ['Discord_Token'])
