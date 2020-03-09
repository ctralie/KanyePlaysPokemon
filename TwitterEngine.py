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
import pickle
from PIL import Image
from PokemonEngine import *

START_TEXT = "@twitplayspokem"
MY_ID = 1136035124640919553

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


def contains_commands(tweet, celeb = False):
    result = False
    if not(tweet['user']['id'] == MY_ID):
        text = tweet['text']
        if celeb or text.find(START_TEXT) == 0:
            words = text.split()
            for i, w in enumerate(words):
                wlower = w.lower()
                if wlower in KEYS:
                    result = True
    return result

def makeTweetVideo(sgin, windowID, tweet):
    """
    Given a saved game, load it and apply the words from this
    particular tweet
    """
    text = tweet['text']
    tweetID = tweet['id']
    time.sleep(1)
    loadGame(sgin, windowID)
    time.sleep(1)
    
    #Step 1: Make all frames
    words = text.split()
    using = np.zeros(len(words))
    ranges = []
    idx = len(START_TEXT)
    if tweet['celeb']:
        idx = 0
    for i, w in enumerate(words):
        wlower = w.lower()
        ranges.append([])
        if wlower in KEYS:
            keyObj = KEYS[wlower]
            hitKeyAndRecord(windowID, keyObj, "temp%i.gif"%i)
            using[i] = 1
            if wlower == 'a':
                if text[idx:].find(w + ' '):
                    start = text[idx:].find(w + ' ') + idx
                elif text[idx:].find(' ' + w):
                    start = text[idx:].find(' ' + w) + idx
            else:
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
    makeTweetVideo("BEGINNING.sgm", ID, {'id':123, 'text':"@twitplayspokem do a   Left up up up up right right right right right up up down down down down down down left left left left down", 'celeb':False})

def load_database():
    return pickle.load(open("database.db", "rb"))

def save_database(data):
    pickle.dump(data, open("database.db", "wb"))

def get_celeb_statuses(api, database):
    """
    Load all of the statuses from celebrities
    """
    statuses = []
    for ID in database.keys():
        if not ID == 'laststatus':
            newtweets = api.get_user_timeline(user_id = ID, since_id = database[ID])
            newtweets.reverse()
            for s in newtweets:
                if contains_commands(s, celeb = True):
                    s['celeb'] = True
                    statuses.append(s)
            if len(newtweets) > 0:
                database[ID] = newtweets[0]['id_str']
    return statuses

def reset_celebs(api, database):
    for ID in database.keys():
        if not ID == 'laststatus':
            newtweets = api.get_user_timeline(user_id = ID, count=2)
            database[ID] = newtweets[0]['id_str']
    save_database(database)


def respondToTweets(api):
    database = load_database()
    statuses = api.search(q="@twitplayspokem", since_id=int(database['laststatus']))['statuses']
    statuses = [s for s in statuses if contains_commands(s)]
    statuses.reverse()
    for s in statuses:
        s['celeb'] = False
    statuses =  statuses + get_celeb_statuses(api, database)
    print("%i new tweets"%len(statuses))
    if len(statuses) > 0:
        launchGame()
        time.sleep(1)
        windowID = getWindowID()
        for s in statuses:
            text = s['text']
            tweetID = s['id']
            screen_name = s['user']['screen_name']
            sgm = "Data/%s.sgm"%database['laststatus']
            makeTweetVideo(sgm, windowID, s)

            photo = open("Data/%i.gif"%tweetID, 'rb')
            response = api.upload_media(media=photo)
            res = api.update_status(status="@%s"%screen_name, in_reply_to_status_id = tweetID, media_ids=[response['media_id']])
            res = api.retweet(id=res['id_str'])

            photo = open("LastFrame.png", 'rb')
            response = api.upload_media(media=photo)
            res = api.update_status(status="@%s Here's where you stopped"%screen_name, in_reply_to_status_id = res['id_str'], media_ids=[response['media_id']])
            res = api.retweet(id=res['id_str'])
            database['laststatus'] = "%s"%tweetID

            if s['celeb']:
                time.sleep(30)

            
        save_database(database)
        subprocess.call(["killall", "vba"])

if __name__ == '__main__':
    api = getTwythonObj()
    reset_celebs(api, load_database())
    while True:
        respondToTweets(api)
        time.sleep(30)