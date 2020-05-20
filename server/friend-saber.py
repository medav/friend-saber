import json
import discord
import sys

from songlist import SongList
from scorekeeper import ScoreKeeper

client = discord.Client()
cfg_filename = sys.argv[1]

with open(cfg_filename) as f:
    config = json.load(f)

lists = [
    SongList(client, config, sl)
    for sl in config['song-lists']
]

sk = ScoreKeeper(client, config, lists)

@client.event
async def on_ready():
    for l in lists:
        await l.OnReady()

    await sk.OnReady()

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    if sk.ShouldClaim(msg):
        await sk.OnMessage(msg)
        return

    for l in lists:
        if l.ShouldClaim(msg):
            await l.OnMessage(msg)
            break

client.run(config['api-key'])
