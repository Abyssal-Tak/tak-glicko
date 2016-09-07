import math
import sqlite3
import re
import pickle
import datetime

def read_from_db(v, includeBots=True,size=-1):
    """Reads from the database"""
    interval = 604800000 # 7 days
    # interval = 86400000 * 4 # 4 days
    date1 = str(1461369600000 + interval * v)
    date2 = 1461369600000 + interval * (v + 1)
    endUnix = date2
    endUnix /= 1000
    ti = datetime.date.fromtimestamp(endUnix)
    print(ti)
    date2 = str(date2)

    conn = sqlite3.connect('games_anon.db')
    c = conn.cursor()
    if size > 0:
        size = str(size)
        c.execute('SELECT player_white, player_black, result, notation FROM games WHERE date > ' +date1+ ' AND date < ' +date2+ ' AND size = '+size+'')
    else:
        c.execute('SELECT player_white, player_black, result, notation FROM games WHERE date > ' + date1 + ' AND date < ' + date2 + ' AND size > 4')


    data = c.fetchall()
    c.close()
    conn.close()
    goodData = []
    badPlayers = {'FriendlyBot', 'Anon'}


    counter = 0
    for d in data:
        if not includeBots:
            if d[0] in bots or d[1] in bots:
                continue
        if d[2] == '0-0':
            pass
        elif re.match('Guest\d', d[0]) or re.match(r'Guest\d', d[1]):
            pass
        elif len(d[3]) <= 4: #If len == 4 white aborted after black played flat 1.
            pass
        elif d[0] in badPlayers or d[1] in badPlayers:
            pass
        else:
            goodData.append(d[0:3]) #Not the game notation

            if d[0] not in activePlayers:
                activePlayers[d[0]] = [counter]
            else:
                p1games = activePlayers[d[0]] + [counter]
                activePlayers[d[0]] = p1games

            if d[1] not in activePlayers:
                activePlayers[d[1]] = [counter]
            else:
                p2games = activePlayers[d[1]] + [counter]
                activePlayers[d[1]] = p2games

            counter += 1

    return goodData


def reEvalRD():
    """Adjusting RD for activity, less active -> higher RD"""
    c = 46.5 # for 7 day system
    #c = 36.5  # for 4 day system
    for pl in playerRating:
        t = playerRating[pl][2]
        RD = playerRating[pl][1]
        playerRating[pl][1] = min((math.sqrt(RD ** 2 + c ** 2 * t)), 350)
        if pl in specialPlayers:
            playerRating[pl][2] += 1
            primary = specialPlayers[pl]
            for al in specialSets[primary]:
                if al in activePlayers:
                    playerRating[pl][2] = 1
        else:
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


def convertGames(pg, primaryPlayer, aliases=False):
    """Converts one players games into a usable format for the glickoMain function"""
    games = []
    for g in pg:
        twoPlayers = (playerRating[g[0]], playerRating[g[1]])

        if not aliases:
            if g[0] == primaryPlayer:
                pp = 0  # White
                op = 1  # Black
            else:
                op = 0  # White
                pp = 1  # Black
        else:
            if g[0] in specialSets[primaryPlayer]:
                pp = 0
                op = 1
            else:
                op = 0
                pp = 1

        result = WLD[g[2]]
        if result == '0-0':
            print("SQL-related bug")
            continue
        #print(result)

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

        oppgRD = gRD(twoPlayers[op][1])
        E = funcE(twoPlayers[pp][0], twoPlayers[op][0], oppgRD)
        x = (oppgRD, E, result)
        games.append(x)

    return games


def glickoMain(games, primaryPlayer):
    ppStats = playerRating[primaryPlayer]
    q = 0.0057565
    dSquared = 0
    rPrime = 0
    numOfGames = len(games) + ppStats[3]
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

    newRating[primaryPlayer] = [rPrime, RDPrime, 1, numOfGames]

# Begin "Main Function" proper...

fullList = True
outFile = 'out.csv'
activePlayers = {}
playerRating = {}
newRating = {}
try:
    pickle_in = open('sqlData.pickle', 'rb')
except FileNotFoundError:
    pass
#playerRating = pickle.load(pickle_in)

# Global Dicts
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

bots = {'alphabot', 'alphatak_bot', 'TakticianBot', 'TakticianBotDev', 'ShlktBot', 'cutak_bot', 'takkybot',
        'AlphaTakBot_5x5', 'TakkerusBot', 'BeginnerBot', 'TakticianDev'}

#someGames = [["Abyss", "Turing", "0-F"], ["Turing","Abyss", "F-0"]]
#someGames = [["ExampleHero", "Example1", "F-0"],["ExampleHero", "Example2", "0-R"],["ExampleHero", "Example3", "0-1"]]
toRead = []
if fullList: # All data
    tt = 1472924361 # The timestamp of the last game in the current database (Sep 3)
    ttt = -1
    working = 1461369600 #April 23rd
    while working < tt:
        ttt += 1
        working += (86400 * 7)
    toRead = list(range(ttt))
else:
    toRead = [0, 1, 2, 3, 4]
    #toRead = [0]



for groups in toRead:
    activePlayers = {}
    gData = read_from_db(groups, includeBots=False,size=-1)
    for a in activePlayers:
        if a not in playerRating:
            if a not in specialPlayers:
                playerRating[a] = [1500, 350, 1, 0]
            else:
                mainAccount = specialPlayers[a]
                for aliases in specialSets[mainAccount]:
                    if aliases in playerRating:
                        playerRating[a] = playerRating[aliases]
                        break
                else: # If the break wasn't hit, i.e. if there was no existing alias found in the rankings dict.
                    playerRating[a] = [1500, 350, 1, 0]



    reEvalRD()

    for players in activePlayers:
        someGames = []
        #print(players)
        if players in specialPlayers:
            if players == specialPlayers[players]: # Main account
                for alts in specialSets[players]:
                    if alts in activePlayers: # If this alias played any games in the period
                        for pGames in activePlayers[alts]:
                            someGames.append(gData[pGames])
                newGames = convertGames(someGames, players, aliases=True)
                glickoMain(newGames, players)
        else:
            for pGames in activePlayers[players]:
                #print(pGames)
                someGames.append(gData[pGames])


            newGames = convertGames(someGames, players)
            glickoMain(newGames, players)



    playerRating = newRating

    for specP in specialPlayers: # For all aliases
        mainAccount = specialPlayers[specP]
        if mainAccount in newRating: # If the main account exists
            newRating[specP] = newRating[mainAccount] # All aliases have the same rating


for specP in specialPlayers: # Removing all the duplicate alias accounts before outputting to file
    mainAccount = specialPlayers[specP]
    if specP != mainAccount:
        if specP in newRating:
            del newRating[specP]

with open(outFile, 'w') as f:
    f.write('Name, Glicko, Std Dev, Games \n')
    for z in newRating:
        gamesPlayed = int(newRating[z][3])
        if gamesPlayed >= 10:
            f.write(z + ',' + str(newRating[z][0]) + ',' + str(newRating[z][1]) + ',' + str(newRating[z][3]) + '\n')

pickle_out = open('glickoData.pickle', 'wb')
pickle.dump(newRating, pickle_out)
pickle_out.close()


