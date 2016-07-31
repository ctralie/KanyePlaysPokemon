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
        print(text[r[0]:r[1]], end = " ")
        if not stem in stemsDict:
            newwords.append(stem)
            stemsDict[stem] = getRandomKey()
        keyObj = KEYS[stemsDict[stem]]
        hitKeyAndRecord(windowID, keyObj, "temp%i.avi"%i)
    saveGame("Data/%i.sgm"%tweetID, windowID)
    print("")
    fout = open("NewWords/%i.txt"%tweetID, "w")
    for i in range(len(newwords)):
        fout.write(newwords[i]+" ")
    fout.close()
    
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
            if i == 0 and k == 1:
                #Make thumbnail image
                scipy.misc.imsave("Data/thumb_%i.png"%tweetID, scipy.misc.imresize(frame, 0.2))
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

def makeWebPage(IDs, idx, date, stemsDict):
    fin = open("NewWords/%i.txt"%IDs[idx])
    lines = fin.readlines()
    newwords = []
    if len(lines) > 0:
        newwords = lines[0].split()
    fin.close()
    
    fin = open("PageTemplate.html")
    lines = fin.readlines()
    fin.close()
    s = "".join(lines)
    
    s = s.replace("DATEGOESHERE", date)
    if idx > 0:
        s = s.replace("PREVGOESHERE", "<h2><a href = \"%i.html\"><--Prev      </a></h2>"%IDs[idx-1])
    else:
        s = s.replace("PREVGOESHERE", " ")
    if idx < len(IDs) - 1:
        s = s.replace("NEXTGOESHERE", "<h2><a href = \"%i.html\">      Next--></a></h2>"%IDs[idx+1])
    else:
        s = s.replace("NEXTGOESHERE", " ")
    s = s.replace("VIDEOGOESHERE", "../Data/%i.ogg"%IDs[idx])
    
    nwstr = ""
    if len(newwords) > 0:
        nwstr = "<h3>New Words</h3>"
        for w in newwords:
            nwstr += "<tr><td><h3>%s</h3></td><td><img src = \"../ControllerImages/%s.png\"></td></tr>"%(w, stemsDict[w])
    s = s.replace("NEWWORDSGOHERE", nwstr)
    
    fout = open("Pages/%i.html"%IDs[idx], "w")
    fout.write(s)
    fout.close()

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
    stemsDict = loadStemsDictionary()
    
    #Go through tweets one by one in order of date, and make the movies
    #if they haven't been made yet
    IDs = sorted(TweetsDict)
    for i in range(len(IDs)):
        print("i = %i, IDs[%i] = %i"%(i, i, IDs[i]))
        if os.path.exists("Data/%i.ogg"%IDs[i]):
            print("Skipping %i..."%IDs[i])
        else:
            #If the movie hasn't been made yet, need to make it
            print("Making video for %i..."%IDs[i])
            savegame = "BEGINNING.sgm"
            if i > 0:
                if not os.path.exists("Data/%i.sgm"%IDs[i-1]):
                    print("Error: Save game doesn't exist for %i"%IDs[i-1])
                    continue
                savegame = "Data/%i.sgm"%IDs[i-1]
            print("******Loading saved game ", savegame, "******")
            makeTweetVideo(stemsDict, savegame, windowID, IDs[i], TweetsDict[IDs[i]])
        makeWebPage(IDs, i, TweetsDict[IDs[i]].date, stemsDict)        
        saveStemsDictionary(stemsDict)
    
    #Make index page
    fout = open("index.html", "w")
    fout.write("<html><head><link rel=\"stylesheet\" type=\"text/css\" href=\"main.css\" /><meta charset=\"UTF-8\"></head><body><h1>Kanye Plays Pokemon</h1><h2><a href = index.html>Index</a></h2><h2><a href = Pages/dictionary.html>Dictionary</a></h2>")
    fout.write("<table><tr><td><h3>Date</h3></td><td><h3>Thumbnail</h3></td><td><h3>Tweet</h3></td></tr>")
    IDs.reverse()
    for ID in IDs:
        tweet = TweetsDict[ID]
        fout.write("<tr><td><a href = \"Pages/%i.html\">%s</a></td><td><a href = \"Pages/%i.html\"><img src = \"Data/thumb_%i.png\"></a></td><td>%s</td></tr>\n"%(ID, tweet.date, ID, ID, tweet.text))
    fout.write("</table>")
    fout.write("</body></html>")
    fout.close()
    
    #Make dictionary page
    fout = open("Pages/dictionary.html", "w")
    fout.write("<html><head><link rel=\"stylesheet\" type=\"text/css\" href=\"main.css\" /><meta charset=\"UTF-8\"></head><body><h1>Kanye Plays Pokemon</h1><h2><a href = index.html>Index</a></h2><h2><a href = dictionary.html>Dictionary</a></h2>")
    fout.write("<table><tr><td><h3>Word</h3></td><td><h3>Gameboy Key</h3></td></tr>")
    for s in sorted(stemsDict):
        fout.write("<tr><td><h3>%s</h3></td><td><img src = \"../ControllerImages/%s.png\"></td></tr>\n"%(s, stemsDict[s]))
    fout.write("</table></body></html>")
    fout.close()
    
#    #Make redirect
#    fout = open("index.html", "w")
#    fout.write("<html><head><meta http-equiv=\"refresh\" content=\"0; url=Pages/%i.html\"></head><body></body></html>"%IDs[0])
#    fout.close()
    
    #Close the window
    closeGame(windowID)
