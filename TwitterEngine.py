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
                im = Image.fromarray(I)
                im.save("Temp/%i.png"%k)
        
            for k in range(NFiles):
                shutil.copyfile("Temp/%i.png"%(k+1), "VideoStaging/%i.png"%(k+FrameCount))
                os.remove("Temp/%i.png"%(k+1))
            FrameCount += NFiles
    
    print("Saving final video...")
    #Make GIF
    subprocess.call(["ffmpeg", "-r", "15", "-i", "VideoStaging/%d.png", "-b", "20000k", "-r", "%i"%FRAMESPERSEC, "Data/%i.gif"%tweetID], stdout = FNULL, stderr = FNULL)
    #Clean up staging area
    for i in range(FrameCount):
        os.remove("VideoStaging/%i.png"%i)
    print("Finished")

if __name__ == '__main__':
    launchGame()
    time.sleep(1)
    ID = getWindowID()
    makeTweetVideo("BEGINNING.sgm", ID, 123, "I want it to go left and then right up down start")

if __name__ == '__main__2':
    api = getTwythonObj()
    photo = open('Left.gif', 'rb')
    response = api.upload_media(media=photo)
    api.update_status(status='Going left!', media_ids=[response['media_id']])