import discord
import datetime
import threading
import time

import scoresaber

class UserData():
    def __init__(self, client, score_keeper, discord_user, steam_uid):
        self.client = client
        self.score_keeper = score_keeper
        self.discord_user = discord_user
        self.steam_uid = steam_uid
        self.latest_score_date = None
        self.top_scores = {}
        self.write_log = []

        self.thread = threading.Thread(
            target=UserData.MonitorEntry,
            args=(self,))

        self.thread.start()

    def MonitorEntry(self):
        self.FullReload()

        while True:
            time.sleep(30)

            self.Refresh()

            if len(self.write_log) > 0:
                self.score_keeper.HandleNewScores(self, self.write_log)
                self.ClearLog()

    def Debug(self, msg):
        print('UserData({}): {}'.format(self.discord_user.name, msg))

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

    def FullReload(self):
        self.Debug('Starting FullReload...')
        scores = scoresaber.ReadFullProfile(self.steam_uid)
        for score in scores:
            self.AddScore(score)

        self.ClearLog()

    def Refresh(self):
        self.Debug('Refreshing...')
        scores = scoresaber.ReadLatestPage(self.steam_uid)
        for score in scores:
            self.AddScore(score)

class ScoreKeeper():
    def __init__(self, client, g_config, slists):
        self.client = client
        self.g_config = g_config
        self.slists = slists
        self.player_map = {}

    def Debug(self, msg):
        print('ScoreKeeper: {}'.format(msg))

    async def OnReady(self):
        self.Debug('Starting Score Keeper...')

        self.channel = discord.utils.get(
            self.client.get_all_channels(),
            name=self.g_config['score-channel'])

    def HandleNewScores(self, user_data, new_scores):
        print(user_data)
        print(new_scores)

    def ShouldClaim(self, msg):
        return msg.channel == self.channel

    async def OnMessage(self, msg):
        user = msg.author

        if msg.content.startswith('!join'):
            steam_uid = msg.content.split()[1]

            self.player_map[user] = UserData(
                self.client,
                self,
                user,
                steam_uid)

            await msg.channel.send('Welcome {}!'.format(user.name))
