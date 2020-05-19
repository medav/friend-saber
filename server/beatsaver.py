import requests
from html.parser import HTMLParser
from functools import lru_cache
from datetime import datetime
import json

@lru_cache(maxsize=1024)
def GetSongInfo(score_saber_hash):
    resp = requests.get(
        'https://beatsaver.com/api/maps/by-hash/{}'.format(score_saber_hash),
        headers={
            # We're going all "sneaky beaky" like
            'User-Agent': 'BeatSaverSharp/1.5.3'
        })

    return json.loads(resp.text)
