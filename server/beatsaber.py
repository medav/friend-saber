

def IsSongRequest(s):
    return s.startswith('!bsr')

def GetSongCode(req):
    return req.split()[1].strip()

def GetSongUrl(song_code):
    return 'https://beatsaver.com/beatmap/{}'.format(song_code)