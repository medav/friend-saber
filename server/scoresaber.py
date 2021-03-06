import requests
from html.parser import HTMLParser
from functools import lru_cache
from datetime import datetime
import json

import beatsaver

class Score():
    def __init__(self, bsr_code, timestamp, score, acc):
        self.bsr_code = bsr_code
        self.timestamp = timestamp
        self.score = score
        self.acc = acc

    @staticmethod
    def Cmp(s1, s2):
        if s1 is None:
            assert s2 is None
            return 0

        else:
            return s1 - s2

    def __eq__(self, other):
        assert self.bsr_code == other.bsr_code
        return self.timestamp == other.timestamp

    def __ge__(self, other):
        assert self.bsr_code == other.bsr_code
        return self.timestamp > other.timestamp and \
            Score.Cmp(self.score, other.score) >= 0 and \
            Score.Cmp(self.acc, other.acc) >= 0

    def __le__(self, other):
        assert self.bsr_code == other.bsr_code
        return other > self

class LeaderboardParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.record = False
        self.hex_code = None

    def handle_starttag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        if data == 'ID: ':
            self.record = True
            return

        if self.record:
            self.hex_code = data
            self.record = False

@lru_cache()
def ResolveHexCode(song_id):
    parser = LeaderboardParser()
    resp = requests.get('https://scoresaber.com/leaderboard/{}'.format(song_id))
    parser.feed(resp.text)
    return parser.hex_code

@lru_cache()
def ConvertToBsr(beat_saver_hash):
    try:
        song_info = beatsaver.GetSongInfo(beat_saver_hash)
        return song_info['key']
    except json.decoder.JSONDecodeError:
        return beat_saver_hash


class ScoreSaberParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.record = False
        self.song_scores = []

    def RecordSongScore(self):
        if self.cur_song_id is None:
            return

        self.song_scores.append(Score(
            ConvertToBsr(ResolveHexCode(self.cur_song_id)),
            datetime.strptime(self.cur_song_time, '%Y-%m-%d %H:%M:%S %Z'),
            self.cur_score,
            self.cur_acc
        ))

    @staticmethod
    def IsRankingSongsTable(attrs):
        for (key, value) in attrs:
            if key == 'class' and value == 'ranking songs':
                return True

        return False

    @staticmethod
    def IsSongTime(attrs):
        for (key, value) in attrs:
            if key == 'class' and value == 'songBottom time':
                return True

        return False

    @staticmethod
    def GetSongTime(attrs):
        for (key, value) in attrs:
            if key == 'title':
                return value

        raise KeyError('Title not found!')

    @staticmethod
    def GetHref(attrs):
        for (key, value) in attrs:
            if key == 'href':
                return value

        raise KeyError('Href not found!')

    def handle_starttag(self, tag, attrs):
        if tag == 'table' and ScoreSaberParser.IsRankingSongsTable(attrs):
            self.record = True
            self.cur_song_id = None
            self.cur_song_time = None
            self.cur_score = None
            self.cur_acc = None

        if tag == 'a' and self.record:
            link = ScoreSaberParser.GetHref(attrs)
            self.cur_song_id = link.split('/')[-1]

        if tag == 'span' and self.record and ScoreSaberParser.IsSongTime(attrs):
            self.cur_song_time = ScoreSaberParser.GetSongTime(attrs)

    def handle_endtag(self, tag):
        if tag == 'tr':
            self.RecordSongScore()
            self.cur_song_id = None
            self.cur_song_time = None
            self.cur_score = None
            self.cur_acc = None

        if tag == 'table':
            self.record = False

    def handle_data(self, data):
        if self.record:
            data = data.strip()
            if len(data) == 0:
                return

            if data.startswith('score'):
                self.cur_score = float(data.split(':')[1].replace(',', ''))

            elif data.startswith('accuracy'):
                self.cur_acc = float(data.split(':')[1].replace('%', ''))

def GetPage(profile_uid, pid):
    return requests.get(
        'https://scoresaber.com/u/{}&page={}&sort=2'.format(profile_uid, pid))

def ReadFullProfile(profile_uid):
    print('Reading full profile for {}'.format(profile_uid))
    parser = ScoreSaberParser()
    i = 1

    while True:
        print('Scanning page {}'.format(i))
        last_num_records = len(parser.song_scores)
        resp = GetPage(profile_uid, i)
        parser.feed(resp.text)

        if last_num_records == len(parser.song_scores):
            break

        i += 1

    return parser.song_scores

def ReadLatestPage(profile_uid):
    parser = ScoreSaberParser()
    resp = GetPage(profile_uid, 1)
    parser.feed(resp.text)
    return parser.song_scores

def ReadPage(profile_uid, pid):
    parser = ScoreSaberParser()
    resp = GetPage(profile_uid, pid)
    parser.feed(resp.text)
    return parser.song_scores
