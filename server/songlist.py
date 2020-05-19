import discord

class SongList():
    def __init__(self, client, config):
        self.client = client
        self.config = config
        self.approved = {}
        self.pending = {}

    def Debug(self, msg):
        print('SongList ["{}"]: {}'.format(self.config['channel'], msg))

    def ReloadRoles(self):
        self.mod_role = set(discord.utils.get(
            self.channel.guild.roles,
            name='list-mod').members)
        self.Debug('mod_role: {}'.format(self.mod_role))

    def IsListMod(self, user):
        return user in self.mod_role

    async def OnReady(self):
        self.Debug('Starting...')

        self.channel = discord.utils.get(
            self.client.get_all_channels(),
            name=self.config['channel'])

        self.ReloadRoles()

        async for msg in self.channel.history(limit=10000):
            if self.IsListEntry(msg):
                self.approved[SongList.GetSongCode(msg.content)] = msg

        async for msg in self.channel.history(limit=10000):
            if self.IsPendEntry(msg):
                self.pending[SongList.GetSongCode(msg.content)] = msg

    @staticmethod
    def IsSongRequest(s):
        return s.startswith('!bsr')

    @staticmethod
    def GetSongCode(req):
        return req.split()[1].strip()

    @staticmethod
    def GetSongUrl(song_code):
        return 'https://beatsaver.com/beatmap/{}'.format(song_code)

    @staticmethod
    def CreateListEntry(song_code):
        return '!bsr {} {}'.format(song_code, SongList.GetSongUrl(song_code))

    @staticmethod
    def CreatePendEntry(song_code):
        return '!pend {} {}'.format(song_code, SongList.GetSongUrl(song_code))

    def IsListEntry(self, msg):
        return msg.author == self.client.user and \
            SongList.IsSongRequest(msg.content)

    def IsPendEntry(self, msg):
        return msg.author == self.client.user and \
            msg.content.startswith('!pend')

    async def AddSong(self, msg, song_code):
        self.Debug('Adding {} to list'.format(song_code))
        self.approved[song_code] = \
            await self.channel.send(SongList.CreateListEntry(song_code))

    async def PendSong(self, msg, song_code):
        self.Debug('Pending {}'.format(song_code))
        self.pending[song_code] = \
            await self.channel.send(SongList.CreatePendEntry(song_code))

    def ShouldClaim(self, msg):
        return msg.channel == self.channel

    async def OnMessage(self, msg):
        sender = msg.author
        text = msg.content

        if text == '!update_roles':
            self.ReloadRoles()

        elif SongList.IsSongRequest(text):
            song_code = SongList.GetSongCode(text)

            if song_code not in self.approved and song_code not in self.pending:
                if self.IsListMod(sender):
                    await self.AddSong(msg, song_code)
                else:
                    await self.PendSong(msg, song_code)

        elif text.startswith('!approve'):
            song_code = SongList.GetSongCode(text)

            if song_code in self.pending:
                old_text = self.pending[song_code].content
                await self.pending[song_code].edit(
                    content=old_text.replace('!pend', '!bsr'))
                self.approved[song_code] = self.pending[song_code]
                del self.pending[song_code]

        elif text.startswith('!deny'):
            song_code = SongList.GetSongCode(text)

            if song_code in self.pending:
                await self.pending[song_code].delete()
                del self.pending[song_code]

        else:
            self.Debug('Deleting message')

        await msg.delete()