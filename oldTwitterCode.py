def getRidOfDisallowedChars(s):
    chars = ["@", "#", "\n"]
    text = ""+s
    for c in chars:
        text = text.replace("@", "")
        text = text.replace("#", "")
        text = text.replace("\n", "")
    return text

if __name__ == '__main__':
    api = _get_api()
    #print(api.VerifyCredentials())
    #https://gist.github.com/yanofsky/5436496
    tweets = api.GetUserTimeline(user_id = TRUMP_USERID, count=200)
    oldest = tweets[-1].id - 1
    newtweets = tweets
    while len(newtweets) > 0:
        print("Getting tweets before %s"%oldest)
        newtweets = api.GetUserTimeline(user_id = TRUMP_USERID, count=200, max_id=oldest)
        tweets.extend(newtweets)
        oldest = tweets[-1].id - 1
        print("%s tweets downloaded so far..."%(len(tweets)))
    print("Writing tweets to file...")
    fout = open("tweets.txt", "w")
    for t in tweets:
        text = ''.join([i if ord(i) < 128 else ' ' for i in t.text]) #Get rid of non-ascii characters
        text = getRidOfDisallowedChars(text)
        text = text.translate("ascii")
        text = re.sub("https://t.co/..........", " ", text)
        print(text)
        fout.write("%i\n%s\n%s\n"%(t.id, text, t.created_at))
    fout.close()
    fout = open("most_recent_id.txt", "w")
    fout.write("%i"%tweets[0].id)
    fout.close()
