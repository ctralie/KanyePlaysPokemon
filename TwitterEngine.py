import re
try:
    from urllib.request import urlopen
except:
    from urllib2 import urlopen

import numpy as np
import matplotlib.pyplot as plt
from twython import Twython
import os
import shutil
import skimage
from PIL import Image
from PokemonEngine import *

def scrubText(s):
    chars = {"\n":" ", "&amp;":"and"}
    for c in chars:
        text = s.replace(c, chars[c])
    return text

def removeURLs(s):
    urls = re.findall(r'https?://t.co/.{9,10}', s)
    ret = s
    for url in urls:
        ret = ret.replace(url, "")
    return ret

def getTwythonObj():
    fin = open("keys.txt")
    lines = [l.rstrip() for l in fin.readlines()]
    fin.close()    
    [CONSUMER_KEY, CONSUMER_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET] = lines   
    api = Twython(app_key = CONSUMER_KEY, app_secret = CONSUMER_KEY_SECRET, oauth_token = ACCESS_TOKEN, oauth_token_secret = ACCESS_TOKEN_SECRET)
    return api


def contains_commands(text):
    result = False
    words = text.split()
    for i, w in enumerate(words):
        wlower = w.lower()
        if wlower in KEYS:
            result = True
    return result

def makeTweetVideo(sgin, windowID, tweetID, text):
    """
    Given a saved game, load it and apply the words from this
    particular tweet
    """
    time.sleep(1)
    loadGame(sgin, windowID)
    time.sleep(1)
    
    #Step 1: Make all frames
    words = text.split()
    using = np.zeros(len(words))
    ranges = []
    idx = 0
    for i, w in enumerate(words):
        wlower = w.lower()
        ranges.append([])
        if wlower in KEYS:
            keyObj = KEYS[wlower]
            hitKeyAndRecord(windowID, keyObj, "temp%i.gif"%i)
            using[i] = 1
            start = text[idx:].find(w) + idx
            end = start + len(w)
            idx = end
            ranges[i] = [start, end]
            time.sleep(RECORD_TIME)
    saveGame("Data/%i.sgm"%tweetID, windowID)
    
    #Step 2: Add controls and text to all frames
    FrameCount = 0
    FNULL = open(os.devnull, 'w')
    lastFrame = None
    for i in range(len(words)):
        #Output video frames to temporary directory    
        if using[i] == 1:
            subprocess.call(["ffmpeg", "-i", "temp%i.gif"%i, "-r", "%i"%FRAMESPERSEC, "-f", "image2", "Temp/%d.png"], stdout = FNULL, stderr = FNULL)
            os.remove("temp%i.gif"%i)
            
            #Superimpose the text and the gameboy control on all images
            keyObj = KEYS[words[i].lower()]
            (I, r) = makeFrameTemplate("Temp/1.png", keyObj, text, ranges[i])
            H = r[1] - r[0]
            W = r[3] - r[2]
            NFiles = len([f for f in os.listdir("Temp") if f[-3:] == 'png'])
            for k in range(1, NFiles+1):
                frame = skimage.io.imread("Temp/%i.png"%k)
                frame = skimage.transform.resize(frame, (H, W))*255
                I[r[0]:r[1], r[2]:r[3], :] = np.array(frame[:, :, 0:3], dtype=np.uint8)
                I2 = skimage.transform.rescale(I, 0.3, multichannel=True)*255
                I2 = np.array(I2, dtype=np.uint8)
                im = Image.fromarray(I2)
                im.save("Temp/%i.png"%k)
                lastFrame = im
        
            for k in range(NFiles):
                shutil.copyfile("Temp/%i.png"%(k+1), "VideoStaging/%i.png"%(k+FrameCount))
                os.remove("Temp/%i.png"%(k+1))
            FrameCount += NFiles
    if lastFrame:
        lastFrame.save("LastFrame.png")
    print("Saving final video...")
    #Make GIF
    filename = "Data/%i.gif"%tweetID
    if os.path.exists(filename):
        os.remove(filename)
    subprocess.call(["ffmpeg", "-r", "15", "-i", "VideoStaging/%d.png", "-r", "%i"%FRAMESPERSEC, "-fs", "4M", filename], stdout = FNULL, stderr = FNULL)
    #Clean up staging area
    for i in range(FrameCount):
        os.remove("VideoStaging/%i.png"%i)
    print("Finished")

def testMakeTweetVideo():
    launchGame()
    time.sleep(1)
    ID = getWindowID()
    makeTweetVideo("BEGINNING.sgm", ID, 123, "First tweet!  Left up up up up right right right right right up up down down down down down down left left left left down")

def respondToTweets(api, windowID):
    fin = open("LASTSTATUS.txt")
    laststatus = fin.read().strip()
    fin.close()
    statuses = api.search(q="@twitplayspokem", since_id=int(laststatus))['statuses']
    statuses.reverse()
    print("%i new tweets"%len(statuses))
    for s in statuses:
        text = s['text']
        tweetID = s['id']
        laststatus = "%s"%tweetID
        if not contains_commands(text):
            continue
        screen_name = s['user']['screen_name']
        sgm = "Data/%s.sgm"%laststatus
        makeTweetVideo(sgm, windowID, tweetID, text)

        photo = open("Data/%i.gif"%tweetID, 'rb')
        response = api.upload_media(media=photo)
        res = api.update_status(status="@%s"%screen_name, in_reply_to_status_id = tweetID, media_ids=[response['media_id']])
        res = api.retweet(id=res['id_str'])

        photo = open("LastFrame.png", 'rb')
        response = api.upload_media(media=photo)
        res = api.update_status(status="@%s This is the end of your sequence"%screen_name, in_reply_to_status_id = res['id_str'], media_ids=[response['media_id']])
        res = api.retweet(id=res['id_str'])

        
    fout = open("LASTSTATUS.txt", "w")
    fout.write("%s"%laststatus)
    fout.close()

if __name__ == '__main__':
    api = getTwythonObj()
    launchGame()
    time.sleep(1)
    ID = getWindowID()
    while True:
        respondToTweets(api, ID)
        time.sleep(30)