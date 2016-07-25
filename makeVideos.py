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
    
    #Step 1: Make all frames
    for i in range(len(words)):
        stem = words[i]['stem']
        r = words[i]['range']
        print(text[r[0]:r[1]])
        if not stem in stemsDict:
            newwords.append(stem)
            stemsDict[stem] = getRandomKey()
        keyObj = KEYS[stemsDict[stem]]
        hitKeyAndRecord(windowID, keyObj, "temp%i.avi"%i)
    saveGame("Data/%i.sgm"%tweetID, windowID)
    
    #Step 2: Add controls and text to all frames
    FrameCount = 0
    FNULL = open(os.devnull, 'w')
    for i in range(len(words)):
        #Output video frames to temporary directory    
        subprocess.call(["avconv", "-i", "temp%i.avi"%i, "-r", "%i"%FRAMESPERSEC, "-f", "image2", "Temp/%d.png"], stdout = FNULL, stderr = FNULL)
        os.remove("temp%i.avi"%i)
        
        #Superimpose the text and the gameboy control on all images
        stem = words[i]['stem']
        r = words[i]['range']
        keyObj = KEYS[stemsDict[stem]]
        (I, r) = makeFrameTemplate("Temp/1.png", keyObj, text, r)
        H = r[1] - r[0]
        W = r[3] - r[2]
        NFiles = len([f for f in os.listdir("Temp") if f[-3:] == 'png'])
        for k in range(1, NFiles+1):
            frame = scipy.misc.imread("Temp/%i.png"%k)
            frame = scipy.misc.imresize(frame, (H, W))
            I[r[0]:r[1], r[2]:r[3], :] = frame[:, :, 0:3]
            scipy.misc.imsave("Temp/%i.png"%k, scipy.misc.imresize(I, 0.5))
    
        for k in range(NFiles):
            shutil.copyfile("Temp/%i.png"%(k+1), "VideoStaging/%i.png"%(k+FrameCount))
            os.remove("Temp/%i.png"%(k+1))
        FrameCount += NFiles
    
    print("Saving final video...")
    subprocess.call(["avconv", "-r", "15", "-i", "VideoStaging/%d.png", "-b", "20000k", "-r", "%i"%FRAMESPERSEC, "Data/%i.ogg"%tweetID], stdout = FNULL, stderr = FNULL)
    #Clean up staging area
    for i in range(FrameCount):
        os.remove("VideoStaging/%i.png"%i)
    print("Finished")

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
    TweetsDict = loadAllSavedTweets(verbose = True)
    
    #Load in the stems dictionary, and go through tweets one by one
    #in order of date
    stemsDict = loadStemsDictionary()
    IDs = sorted(TweetsDict)
    for i in range(len(IDs)):
        print("i = %i, IDs[%i] = %i"%(i, i, IDs[i]))
        if os.path.exists("Data/%i.ogg"%IDs[i]):
            print("Skipping %i...", IDs[i])
            continue
        else:
            print("Making video for %i..."%IDs[i])
            #If the movie hasn't been made yet, need to make it
            savegame = "BEGINNING.sgm"
            if i > 0:
                if not os.path.exists("Data/%i.sgm"%IDs[i-1]):
                    print("Error: Save game doesn't exist for %i"%IDs[i-1])
                    continue
                savegame = "Data/%i.sgm"%IDs[i-1]
            print("******Loading saved game ", savegame, "******")
            makeTweetVideo(stemsDict, savegame, windowID, IDs[i], TweetsDict[IDs[i]])
        saveStemsDictionary(stemsDict)
