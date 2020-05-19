import discord
import datetime

import scoresaber

class UserData():
    def __init__(self, client, discord_user):
        self.client = client
        self.discord_user = discord_user
        self.steam_uid = None
        self.latest_score_date = None
        self.top_scores = {}
        self.write_log = []

    async def FetchSteamUid(self):
        prof = await self.discord_user.profile()
        for acc in prof.connected_accounts:
            if acc['type'] == 'steam':
                self.steam_uid = acc['id']
                break

    def ClearLog(self):
        self.write_log = []

    def AddScore(self, score):
        if self.latest_score_date is None or \
            score.timestamp > self.latest_score_date:

            self.latest_score_date = score.timestamp

        else:
            # We always expect new scores to be "newer in time"
            return

        if score.bsr_code in self.top_scores:
            if score > self.top_scores[score.bsr_code]:
                self.write_log.append(score)
                self.top_scores[score.bsr_code] = score

        else:
            self.write_log.append(score)
            self.top_scores[score.bsr_code] = score

    async def FullReload(self):
        scores = scoresaber.ReadFullProfile(self.steam_uid)
        for score in scores:
            self.AddScore(score)

        self.ClearLog()

    def Refresh(self):
        scores = scoresaber.ReadLatestPage(self.steam_uid)
        for score in scores:
            self.AddScore(score)

class ScoreKeeper():
    def __init__(self, client, g_config, slists):
        self.client = client
        self.g_config = g_config
        self.slists = slists

    def Debug(self, msg):
        print('ScoreKeeper: {}'.format(msg))

    def ReloadRoles(self):
        self.mod_role = set(discord.utils.get(
            self.channel.guild.roles,
            name='list-mod').members)
        self.Debug('mod_role: {}'.format(self.mod_role))


    async def OnReady(self):
        self.Debug('Starting Score Keeper...')

        self.channel = discord.utils.get(
            self.client.get_all_channels(),
            name=self.g_config['score-channel'])

        self.ReloadRoles()


    def ShouldClaim(self, msg):
        return msg.channel == self.channel

    async def OnMessage(self, msg):
        sender = msg.author
        text = msg.content
