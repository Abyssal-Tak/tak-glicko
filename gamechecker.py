import sqlite3
from collections import Counter
import re

def getGames():
    conn = sqlite3.connect('games_anon.db')
    c = conn.cursor()
    date1 = '1461369600000'
    c.execute('SELECT player_white, player_black, result, notation, date FROM games WHERE date > ' +date1+ ' AND size > 4')
    data = c.fetchall()
    c.close()
    conn.close()
    goodData = []
    notations = []
    badPlayers = {'FriendlyBot', 'Anon'}
    a = 0
    counter = 1
    lastUnix = 0
    players = []

    for d in data:
        if counter == len(data):
            lastUnix = d[4]
        counter += 1
        if d[2] == '0-0':
            pass
        elif len(d[3]) <= 4:
            a += 1
        elif re.match('Guest\d', d[0]) or re.match(r'Guest\d', d[1]):
            pass
        elif d[0] in badPlayers or d[1] in badPlayers:
            pass
        else:
            if d[0] in goodBots:
                bot = d[0]
            elif d[1] in goodBots:
                bot = d[1]
            else:
                continue
            if d[1] == bot and d[2] in whiteWins:
                notations.append(d[3])
            elif d[0] == bot and d[2] not in whiteWins:
                notations.append(d[3])


    cnt = Counter(notations).most_common(25)
    #print(cnt)
    cnt = dict(cnt)
    #print(cnt)
    if __name__ == "__main__":
        print(a)

        for d in data:
            if d[3] in cnt:
                print(d[0], d[1], ':   ',  d[3][10:26])
    else:
        return cnt, lastUnix


goodBots = {'alphabot', 'alphatak_bot', 'TakticianBot', 'TakticianBotDev',
            'ShlktBot', 'AlphaTakBot_5x5', 'TakkerusBot', 'TakticianDev'}

whiteWins = {'1-0', 'F-0', 'R-0'}

WLD = {"1-0": '1-0', "F-0": "1-0", "R-0": "1-0",
       "0-F": '0-1', '0-R': '0-1', '0-1': '0-1', '1/2-1/2': '0.5-0.5', '0-0': '0-0'}

#getGames()


