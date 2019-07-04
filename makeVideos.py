from PokemonEngine import *
from TwitterEngine import *
import subprocess
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
                scipy.misc.imsave("Data/thumb_%i.png"%tweetID, scipy.misc.imresize(frame, 0.1))
            I[r[0]:r[1], r[2]:r[3], :] = frame[:, :, 0:3]
            scipy.misc.imsave("Temp/%i.png"%k, scipy.misc.imresize(I, 0.5))
    
        for k in range(NFiles):
            shutil.copyfile("Temp/%i.png"%(k+1), "VideoStaging/%i.png"%(k+FrameCount))
            os.remove("Temp/%i.png"%(k+1))
        FrameCount += NFiles
    
    print("Saving final video...")
    #Make ogg video
    subprocess.call(["avconv", "-r", "15", "-i", "VideoStaging/%d.png", "-b", "20000k", "-r", "%i"%FRAMESPERSEC, "Data/%i.ogg"%tweetID], stdout = FNULL, stderr = FNULL)
    #Make mp4 video
    subprocess.call(["avconv", "-i",  "Data/%i.ogg"%tweetID, "-c:v", "libx264", "-s", "640x480", "Data/%i.mp4"%tweetID])
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
    stemsDict = loadStemsDictionary()
    
    #Go through tweets one by one in order of date, and make the movies
    #if they haven't been made yet
    newIDsIdx = []
    IDs = sorted(TweetsDict)
    for i in range(len(IDs)):
        print("i = %i, IDs[%i] = %i"%(i, i, IDs[i]))
        if os.path.exists("Data/%i.ogg"%IDs[i]):
            print("Skipping %i..."%IDs[i])
        else:
            #If the movie hasn't been made yet, need to make it
            print("Making video for %i..."%IDs[i])
            newIDsIdx.append(i)
            savegame = "BEGINNING.sgm"
            if i > 0:
                if not os.path.exists("Data/%i.sgm"%IDs[i-1]):
                    print("Error: Save game doesn't exist for %i"%IDs[i-1])
                    continue
                savegame = "Data/%i.sgm"%IDs[i-1]
            print("******Loading saved game ", savegame, "******")
            makeTweetVideo(stemsDict, savegame, windowID, IDs[i], TweetsDict[IDs[i]])
        makeWebPage(IDs, i, TweetsDict[IDs[i]].text, TweetsDict[IDs[i]].date, stemsDict)        
        saveStemsDictionary(stemsDict)
    
    fin = open("statcounter.html")
    statcounter = "".join(fin.readlines())
    fin.close()
    #Make index page
    fout = open("index.html", "w")
    fout.write("<html><head><link rel=\"stylesheet\" type=\"text/css\" href=\"main.css\" /><meta charset=\"UTF-8\"></head><body><h1>Kanye Plays Pokemon</h1>\n\n")
    fout.write("<table width = 600><tr><td><h3><a href = \"https://twitter.com/kanyewest\">Kanye's tweets</a> send commands to the Gameboy classic. Every time a new word comes in, it's randomly assigned to a command, where it stays for the rest of time. Click on a date or thumbnail to see what each tweet does</h3></td></tr></table>\n")
    fout.write(statcounter)
    fout.write("\n\n<h2><a href = index.html>Index</a></h2><h2><a href = Pages/dictionary.html>Dictionary</a></h2>")
    fout.write("<table><tr><td><h3>Date</h3></td><td><h3>Thumbnail</h3></td><td><h3>Tweet</h3></td></tr>")
    IDs.reverse()
    for ID in IDs:
        tweet = TweetsDict[ID]
        fout.write("<tr><td><a href = \"Pages/%i.html\">%s</a></td><td><a href = \"Pages/%i.html\"><img src = \"Data/thumb_%i.png\"></a></td><td>%s</td></tr>\n"%(ID, tweet.date, ID, ID, tweet.text))
    fout.write("</table>")
    fout.write("</body></html>")
    fout.close()
    IDs.reverse()
    
    #Make dictionary page
    fout = open("Pages/dictionary.html", "w")
    fout.write("<html><head><link rel=\"stylesheet\" type=\"text/css\" href=\"main.css\" /><meta charset=\"UTF-8\"></head><body><h1>Kanye Plays Pokemon</h1>")
    fout.write(statcounter)
    fout.write("<h2><a href = index.html>Index</a></h2><h2><a href = dictionary.html>Dictionary</a></h2>")
    fout.write("<table><tr><td><h3>Word</h3></td><td><h3>Gameboy Key</h3></td></tr>")
    for s in sorted(stemsDict):
        fout.write("<tr><td><h3>%s</h3></td><td><img src = \"../ControllerImages/%s.png\"></td></tr>\n"%(s, stemsDict[s]))
    fout.write("</table></body></html>")
    fout.close()
    
    #Close the window
    closeGame(windowID)
    
    #Copy new files to S3
    newList = {}
    newList['index.html'] = ''
    newList['Pages/dictionary.html'] = ''
    for idx in newIDsIdx:
        newList["Data/%i.ogg"%IDs[idx]] = ''
        newList["Data/%i.mp4"%IDs[idx]] = ''
        newList["Pages/%i.html"%IDs[idx]] = ''
        newList["Data/thumb_%i.png"%IDs[idx]] = ''
        if idx > 0:
            newList["Pages/%i.html"%IDs[idx-1]] = ''
    bucket = "www.kanyeplayspokemon.com"
    for s in newList:
        print("Uploading %s"%s)
        subprocess.call(["s3cmd", "put", s, "s3://%s/sPokemon/%s"%(bucket, s)])
