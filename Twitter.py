import re
try:
    from urllib.request import urlopen
except:
    from urllib2 import urlopen

from twython import Twython
import os
from nltk import word_tokenize

TRUMP_USERID = 25073877

def scrubText(s):
    chars = {"\n":" ", "&amp;":"and"}
    for c in chars:
        text = s.replace(c, chars[c])
    return text

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

if __name__ == '__main__':
    api = getTwythonObj()
#    tweets = getAllTweetsUpToNow(api)
#    for t in tweets:
#        saveTweet(t)
    TweetsDict = loadAllSavedTweets()
    for T in sorted(TweetsDict):
        #print(word_tokenize(TweetsDict[T].text.lower()))
        print (TweetsDict[T].text.lower()).split()
