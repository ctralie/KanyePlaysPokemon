import re
try:
    from urllib.request import urlopen
except:
    from urllib2 import urlopen

from twython import Twython

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
    
    t = Twython(app_key = CONSUMER_KEY, app_secret = CONSUMER_KEY_SECRET, oauth_token = ACCESS_TOKEN, oauth_token_secret = ACCESS_TOKEN_SECRET)
    return t

if __name__ == '__main__':
    t = getTwythonObj()
    T = t.get_user_timeline(user_id = TRUMP_USERID, count=20)
    for i in range(len(T)):
        s = T[i]
        print(s['text'])
        print(scrubText(s['text']))
        print(s['id'])
        print(s['created_at'])
        print("\n\n")
