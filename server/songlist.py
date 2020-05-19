import json
import discord
import sys

from utils import *
from beatsaber import *

client = discord.Client()
cfg_filename = sys.argv[1]

with open(cfg_filename) as f:
    config = json.load(f)

def CreateListEntry(song_code):
    return '!bsr {} {}'.format(song_code, GetSongUrl(song_code))

def IsListEntry(msg):
    return msg.author == client.user and IsSongRequest(msg.content)

def CreatePendEntry(song_code):
    return '!pend {} {}'.format(song_code, GetSongUrl(song_code))

def IsPendEntry(msg):
    return msg.author == client.user and msg.content.startswith('!pend')

async def AddSong(msg, song_code):
    global channel
    global approved

    print('Adding {} to list'.format(song_code))

    await msg.delete()
    approved[song_code] = await channel.send(CreateListEntry(song_code))

async def PendSong(msg, song_code):
    global channel
    global approved

    print('Pending {}'.format(song_code))

    await msg.delete()
    pending[song_code] = await channel.send(CreatePendEntry(song_code))

def IsListMod(user):
    return user in mod_role

@client.event
async def on_ready():
    global channel
    global mod_role
    global approved
    global pending

    print('We have logged in as {0.user}'.format(client))

    channel = discord.utils.get(
        client.get_all_channels(),
        name=config['channel'])

    mod_role = set(discord.utils.get(
        channel.guild.roles,
        name='list-mod').members)

    print('Mods: {}'.format(mod_role))

    approved = {}
    pending = {}

    async for msg in channel.history(limit=10000):
        if IsListEntry(msg):
            approved[GetSongCode(msg.content)] = msg

    async for msg in channel.history(limit=10000):
        if IsPendEntry(msg):
            pending[GetSongCode(msg.content)] = msg

    print('Built song cache! Here is what I found:')
    for song_code in approved:
        print('In List: {}'.format(song_code))

    for song_code in pending:
        print('Pending: {}'.format(song_code))

@client.event
async def on_message(msg):
    global channel
    global mod_role
    global approved
    global pending

    sender = msg.author
    if sender == client.user:
        return

    if msg.channel != channel:
        return

    text = msg.content

    if text == '!update_roles':
        mod_role = set(discord.utils.get(
            channel.guild.roles,
            name='list-mod').members)

        print('mod_role:', mod_role)
        await msg.delete()

    elif IsSongRequest(text):
        song_code = GetSongCode(text)

        if song_code in approved or song_code in pending:
            await msg.delete()

        else:
            if IsListMod(sender):
                await AddSong(msg, song_code)
            else:
                await PendSong(msg, song_code)

    elif text.startswith('!approve'):
        await msg.delete()
        song_code = GetSongCode(text)

        if song_code in pending:
            old_text = pending[song_code].content
            await pending[song_code].edit(content=old_text.replace('!pend', '!bsr'))
            approved[song_code] = pending[song_code]
            del pending[song_code]

    else:
        print('Deleting message')
        await msg.delete()

client.run(config['api-key'])

