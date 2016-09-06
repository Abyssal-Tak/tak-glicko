import math
import sqlite3
import re
import pickle
import datetime

def read_from_db(v):
    """Reads from the database"""
    interval = 604800000 # 7 days
    #interval = 86400000 * 4 # 4 days
    date1 = str(1461369600000 + interval * v)
    date2 = 1461369600000 + interval * (v + 1)
    xyz = date2
    xyz /= 1000
    ti = datetime.date.fromtimestamp(xyz)
    print(ti)
    date2 = str(date2)

    conn = sqlite3.connect('games_anon.db')
    c = conn.cursor()
    if v >= 0:
        c.execute('SELECT player_white, player_black, result FROM games WHERE date > ' +date1+ ' AND date < ' +date2+ ' AND size = 5')


    data = c.fetchall()
    c.close()
    conn.close()
    goodData = []
    badPlayers = {'FriendlyBot', 'Anon'}

    counter = 0
    for d in data:
        if d[2] == '0-0':
            pass
        elif re.match('Guest\d', d[0]) or re.match(r'Guest\d', d[1]):
            pass
        elif d[0] in badPlayers or d[1] in badPlayers:
            pass
        else:
            goodData.append(d)
            '''if d[0] in specialPlayers: #Checking for known alias
                alias = specialPlayers[d[0]]
                if alias not in activePlayers:
                    activePlayers[alias] = [counter]
                else:
                    p1games = activePlayers[alias] + [counter]
                    activePlayers[alias] = p1games '''
            if d[0] not in activePlayers:
                activePlayers[d[0]] = [counter]
            else:
                p1games = activePlayers[d[0]] + [counter]
                activePlayers[d[0]] = p1games

            ''''if d[1] in specialPlayers: #Checking for known alias
                alias = specialPlayers[d[1]]
                if alias not in activePlayers:
                    activePlayers[alias] = [counter]
                else:
                    p1games = activePlayers[alias] + [counter]
                    activePlayers[alias] = p1games '''
            if d[1] not in activePlayers:
                activePlayers[d[1]] = [counter]
            else:
                p2games = activePlayers[d[1]] + [counter]
                activePlayers[d[1]] = p2games

            counter += 1

    return goodData


def reEvalRD():
    """Adjusting RD for activity, less active -> higher RD"""
    c = 48 # for 7 day system
    #c = 36.5  # for 4 day system
    for pl in playerRating:
        t = playerRating[pl][2]
        RD = playerRating[pl][1]
        playerRating[pl][1] = min((math.sqrt(RD ** 2 + c ** 2 * t)), 350)
        if pl in activePlayers:
            playerRating[pl][2] = 1
        else:
            playerRating[pl][2] += 1

def gRD(RD):
    """g(RD) as defined in the Glicko Rating Method"""
    q = 0.0057565
    pi = math.pi
    return 1 / math.sqrt(1 + 3 * q**2 * (RD**2)/(pi**2))

def funcE(playerR, oppR, gRDj):
    """E as defined in the Glicko Rating Method"""
    return 1 / (1 + pow(10, (-1 * gRDj * (playerR - oppR) / 400)))

def convertGames(pg, primaryPlayer):
    """Converts one players games into a usable format for the glickoMain function"""
    games = []
    for g in pg:
        try:
            players = (playerRating[g[0]], playerRating[g[1]])
        except KeyError:
            if g[0] in specialPlayers and g[1] in specialPlayers:
                players = (playerRating[specialPlayers[g[0]]], playerRating[specialPlayers[g[1]]])
            elif g[0] in specialPlayers:
                players = (playerRating[specialPlayers[g[0]]], playerRating[g[1]])
            elif g[1] in specialPlayers:
                players = (playerRating[g[0]], playerRating[specialPlayers[g[1]]])
            else:
                print("Hm?")

        result = WLD[g[2]]
        if result == '0-0':
            print("Dammit")
            continue
        #print(result)
        if g[0] == primaryPlayer:
            pp = 0 # White
            op = 1 # Black
        else:
            op = 0 # White
            pp = 1 # Black
        if result == '1-0':
            if pp == 0:
                result = 1
            else:
                result = 0
        elif result == '0-1':
            if pp == 1:
                result = 1
            else:
                result = 0
        else:
            result = 0.5

        oppgRD = gRD(players[op][1])
        E = funcE(players[pp][0], players[op][0], oppgRD)
        x = (oppgRD, E, result)
        games.append(x)

    return games


def glickoMain(games, primaryPlayer):
    ppStats = playerRating[primaryPlayer]
    q = 0.0057565
    dSquared = 0
    rPrime = 0
    # Where g[0] is gRD, g[1] is funcE, and g[2] is the result of the game
    for g in games:
        dSquared += ((g[0]**2) * g[1] * (1 - g[1]))

    dSquared *= (q**2)
    dSquared = 1 / dSquared

    for g in games:
        rPrime += (g[0] * (g[2] - g[1]))
    num = (1/(ppStats[1]**2) + (1/dSquared))
    rPrime *= (q / num)
    rPrime += ppStats[0]
    #print(rPrime)
    RDPrime = math.sqrt(1/num)
    if RDPrime < 20: # Minimum RD, otherwise player improvement can be buried if they have many games.
        RDPrime = 20
    #print(RDPrime)
    newRating[primaryPlayer] = [rPrime, RDPrime, 1]


outFile = 'out.csv'
activePlayers = {}
playerRating = {}
newRating = {}
pickle_in = open('sqlData.pickle', 'rb')
#playerRating = pickle.load(pickle_in)

#Global Dicts
specialPlayers = {'Turing': 'Turing', 'sectenor': 'Turing',
                  'alphabot': 'alphatak_bot', 'alphatak_bot': 'alphatak_bot',
                  'TakticianBot': 'TakticianBot', 'TakticianBotDev': 'TakticianBot',
                  'SultanPepper': 'SultanPepper', 'KingSultan': 'SultanPepper', 'PrinceSultan': 'SultanPepper',
                  'SultanTheGreat': 'SultanPepper', 'FuhrerSultan': 'SultanPepper', 'MaerSultan': 'SultanPepper',
                  'tarontos': 'Tarontos', 'Tarontos': 'Tarontos', 'Ally': 'Ally', 'Luffy': 'Ally',
                  'Archerion': 'Archerion', 'Archerion2': 'Archerion'}

specialSets = {'Turing': {'Turing', 'sectenor'}, 'alphatak_bot': {'alphatak_bot', 'alphabot'},
                 'TakticianBot': {'TakticianBot', 'TakticianBotDev'}, 'Tarontos': {'tarontos', 'Tarontos'},
               'SultanPepper': {'SultanPepper', 'KingSultan', 'PrinceSultan', 'SultanTheGreat', 'MaerSultan', 'FuhrerSultan'},
               'Ally': {'Ally', 'Luffy'}, 'Archerion': {'Archerion', 'Archerion2'}}

WLD = {"1-0": '1-0', "F-0": "1-0", "R-0": "1-0",
       "0-F": '0-1', '0-R': '0-1', '0-1': '0-1', '1/2-1/2': '0.5-0.5', '0-0': '0-0'}

#someGames = [["Abyss", "Turing", "0-F"], ["Turing","Abyss", "F-0"]]
#someGames = [["ExampleHero", "Example1", "F-0"],["ExampleHero", "Example2", "0-R"],["ExampleHero", "Example3", "0-1"]]
toRead = [0, 1, 2, 3, 4]
for groups in toRead:
    activePlayers = {}
    gData = read_from_db(groups)
    #print(activePlayers)
    for a in activePlayers:
        if a not in playerRating:
            playerRating[a] = [1500, 350, 1]

    reEvalRD()

    #print(len(gData))

    for players in activePlayers:
        someGames = []
        #print(players)
        for pGames in activePlayers[players]:
            #print(pGames)
            try:
                someGames.append(gData[pGames])
            except IndexError:
                print("Error!")
                print(len(gData))
                print(pGames)
        #print(someGames)
        '''
        if players in specialPlayers:
            mainPl = specialPlayers[players]
            aliasSet = specialSets[mainPl]
            newGames = convertGames(someGames, aliasSet)
        '''

        newGames = convertGames(someGames, players)
        glickoMain(newGames, players)



    playerRating = newRating


with open(outFile, 'w') as f:
    f.write('Name, Glicko, Std Dev \n')
    for z in newRating:
        f.write(z + ',' + str(newRating[z][0]) + ',' + str(newRating[z][1]) + '\n')

pickle_out = open('glickoData.pickle', 'wb')
pickle.dump(newRating, pickle_out)
pickle_out.close()

#sor = reversed(sorted(newRating.values()))
'''
apr23 = 1461369600000
theSum = apr23

for zz in range(10):
    theSum += 604800000
    print(theSum)
'''








