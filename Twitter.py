import re
try:
    from urllib.request import urlopen
except:
    from urllib2 import urlopen

import numpy as np
from twython import Twython
import os
from nltk import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

TRUMP_USERID = 25073877

def scrubText(s):
    chars = {"\n":" ", "&amp;":"and"}
    for c in chars:
        text = s.replace(c, chars[c])
    return text

def removeURLs(s):
    urls = re.findall(r'https://t.co/.{9,10}', s)
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

def getAllTweetsUpToNow(api):
    tweets = api.get_user_timeline(user_id = TRUMP_USERID, count=1)
    oldest = tweets[0]['id'] - 1
    newtweets = tweets
    while len(newtweets) > 0:
        print("Getting tweets before %s"%oldest)
        newtweets = api.get_user_timeline(user_id = TRUMP_USERID, count=200, max_id=oldest)
        tweets.extend(newtweets)
        oldest = tweets[-1]['id'] - 1
        print("%s tweets downloaded so far..."%(len(tweets)))
    return tweets

def getNewTweets(api, latestid):
    print("Getting tweets after %i..."%latestid)
    tweets = []
    since_id = latestid
    newtweets = api.get_user_timeline(user_id = TRUMP_USERID, count = 200, since_id = since_id)
    while len(newtweets) > 0:
        newtweets = [t for t in newtweets if t['id'] > since_id]
        tweets.extend(newtweets)
        if len(tweets) == 0:
            print("No new tweets")
            return []
        print("%s new downloaded so far..."%(len(tweets)))
        IDs = np.array([int(t['id']) for t in tweets])
        since_id = int(np.max(IDs))
        newtweets = api.get_user_timeline(user_id = TRUMP_USERID, count = 200, since_id = since_id)        
    return tweets
    

class TweetObj(object):
    def __init__(self, ID):
        self.ID = ID
        self.oggfile = False
        self.sgm = False
        self.date = ""
        self.text = ""
    
    def __str__(self):
        return "%i, %s, OggFile: %s, SavedGame: %s\n%s"%(self.ID, self.date, self.oggfile, self.sgm, self.text)

def loadAllSavedTweets():
    files = os.listdir('Data')
    tweets = []
    oggs = []
    TweetsDict = {}
    for f in files:
        (ID, ext) = os.path.splitext(f)
        if ext == ".txt":
            ID = int(ID)
            if not ID in TweetsDict:
                TweetsDict[ID] = TweetObj(ID)
                fin = open("Data/"+f)
                lines = fin.readlines()
                TweetsDict[ID].date = lines[0]
                for l in lines[1::]:
                    TweetsDict[ID].text += l
        elif ext == ".ogg":
            ID = int(ID)
            if not ID in TweetsDict:
                TweetsDict[ID] = TweetObj(ID)
            TweetsDict[ID].oggfile = True
        
        elif ext == ".sgm":
            ID = int(ID)
            if not ID in TweetsDict:
                TweetsDict[ID] = TweetObj(ID)
            TweetsDict[ID].sgm = True
    #Remove retweets and tweets with only links
    retweets = []
    for ID in TweetsDict:
        text = TweetsDict[ID].text.lower()
        texturl = removeURLs(text)
        if text[0:3] == "rt ":
            retweets.append(ID)
        elif len(texturl.split()) == 0:
            retweets.append(ID)
    NRetweets = len(retweets)
    for ID in retweets:
        TweetsDict.pop(ID)
    print("%i retweets removed from initial list, %i tweets total loaded"%(NRetweets, len(TweetsDict)))
    return TweetsDict

def saveTweet(tweet):
    ID = tweet['id']
    created_at = tweet['created_at']
    text = tweet['text']
    text = scrubText(text)
    fout = open("Data/%i.txt"%ID, 'w')
    fout.write("%s\n"%created_at)
    fout.write(text)
    fout.close()

def saveNewTweets():
    api = getTwythonObj()
    TweetsDict = loadAllSavedTweets()
    IDs = np.array([TweetsDict[T].ID for T in TweetsDict])
    newtweets = getNewTweets(api, np.max(IDs))
    for t in newtweets:
        print(t['id'])
        saveTweet(t)

#Extract all of the stems and the index ranges of the original words
def processTweet(t):
    text = t.text.lower()
    V = TfidfVectorizer(max_features=len(text))
    texturl = removeURLs(text)
    strs = texturl.split()
    idx = 0
    words = []
    for s in strs:
        try:
            X = V.fit_transform([s])
        except:
            continue
        stem = V.get_feature_names()[0]
        start = text[idx:].find(s) + idx
        end = start + len(s)
        idx = end
        words.append({'stem':stem, 'range':[start, end]})
    return words

if __name__ == '__main__':
    TweetsDict = loadAllSavedTweets()
    for T in sorted(TweetsDict):
        print("----------------------")
        text = TweetsDict[T].text
        words = processTweet(TweetsDict[T])
        for w in words:
            r = w['range']
            print(text[r[0]:r[1]], " (", w['stem'], ")")
