from PokemonEngine import *
from TwitterEngine import *
import sys
import shutil

def loadStemsDictionary():
    fin = open("stemsdict.txt")
    d = {}
    for l in fin.readlines():
        [stem, key] = (l.rstrip()).split()
        d[stem] = key
    fin.close()
    return d

def saveStemsDictionary(d):
    fout = open("stemsdict.txt", "w")
    for stem in d:
        fout.write("%s %s\n"%(stem, d[stem]))
    fout.close()

def makeTweetVideo(stemsDict, sgin, windowID, tweetID, tweet):
    time.sleep(1)
    loadGame(sgin, windowID)
    time.sleep(1)
    
    text = tweet.text
    words = processTweet(tweet)
    newwords = []
    FrameCount = 0
    for w in words:
        stem = w['stem']
        r = w['range']
        print(text[r[0]:r[1]])
        if not stem in stemsDict:
            newwords.append(stem)
            stemsDict[stem] = getRandomKey()
        keyObj = KEYS[stemsDict[stem]]
        NFiles = hitKeyAndRecord(windowID, keyObj, text, r)
        for i in range(NFiles):
            shutil.copyfile("Temp/%i.png"%(i+1), "VideoStaging/%i.png"%(i+FrameCount))
            os.remove("Temp/%i.png"%(i+1))
        FrameCount += NFiles
    saveGame("Data/%i.sgm"%tweetID, windowID)
    subprocess.call(["avconv", "-r", "30", "-i", "VideoStaging/%d.png", "-b", "30000k", "-r", "30", "Data/%i.ogg"%tweetID])

if __name__ == '__main__':
    #Check for new tweets
    NTweets = saveNewTweets()
    #if NTweets == 0:
    #    sys.exit(0)
    
    #Start up the pokemon emulator
    launchGame()
    time.sleep(1)
    windowID = getWindowID()
    
    #Load in all tweets and the stems dictionary
    TweetsDict = loadAllSavedTweets()
    
    #Load in the stems dictionary, and go through tweets one by one
    #in order of date
    stemsDict = loadStemsDictionary()
    IDs = sorted(TweetsDict)
    for i in range(len(IDs)):
        if not TweetsDict[IDs[i]].oggfile:
            print("Making video for %i..."%IDs[i])
            #If the movie hasn't been made yet, need to make it
            savegame = "BEGINNING.sgm"
            if i > 0:
                if not TweetsDict[IDs[i-1]].sgm:
                    print("Error: Save game doesn't exist for %i"%IDs[i-1])
                    continue
                savegame = "Data/%i.sgm"%IDs[i-1]
            makeTweetVideo(stemsDict, savegame, windowID, IDs[i], TweetsDict[IDs[i]])
            TweetsDict[IDs[i]].oggfile = True
            TweetsDict[IDs[i]].sgm = True
        saveStemsDictionary(stemsDict)
