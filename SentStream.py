import tweepy
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
from textblob import TextBlob 
import re
import json
import sqlite3
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# VALUES FOUND IN TWITTER DEV ACCOUNT: 
# consumer key, consumer secret, access token, access secret.
ckey=""
csecret=""
atoken=""
asecret=""
# handles OAuth twitter authorization
auth = OAuthHandler(ckey, csecret)
auth.set_access_token(atoken, asecret)
api = tweepy.API(auth)

print("What would you like to name your database?")
database = input()

'''
Creates an SQLite databse with the inputted name
'''
conn = sqlite3.connect(database + ".db")
c = conn.cursor()
c.execute('''CREATE TABLE tweets
    (tweetText text,
    user text,
    followers integer,
    date text,
    sentiment, text)''')
conn.commit()
conn.close()

# DB stuff
conn = sqlite3.connect(database + ".db")
c = conn.cursor()
    
# Class for defining a Tweet
class Tweet():

    def clean_tweet(self, tweet): 
            ''' 
            Utility function to clean tweet text by removing links, 
            special characters using simple regex statements. 
            '''
            return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())
        
    # Data on the tweet
    def tweet_sentiment(self, tweet): 
        ''' 
        Utility function to classify sentiment of passed tweet 
        using textblob's sentiment method 
        '''
        analyser = SentimentIntensityAnalyzer()
        score = analyser.polarity_scores(self.clean_tweet(tweet))
        sentscore = analyser.polarity_scores(tweet) 
        return sentscore['compound']
            
    
    def __init__(self, text, user, followers, date, sentiment):
        self.text = text
        self.user = user
        self.followers = followers
        self.date = date
        self.sentiment = self.tweet_sentiment(self.text)
    
        
        

    # Inserting that data into the DB
    def insertTweet(self):

        c.execute("INSERT INTO tweets (tweetText, user, followers, date, sentiment) VALUES (?, ?, ?, ?, ?)",
            (self.text, self.user, self.followers, self.date, self.sentiment))
        conn.commit()
        
#override tweepy.StreamListener to add logic to on_status
class MyStreamListener(tweepy.StreamListener):
    
    def clean_tweet(self, tweet): 
            ''' 
            Utility function to clean tweet text by removing links, 
            special characters using simple regex statements. 
            '''
            return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split()) 
                                     
    
    def get_tweet_sentiment(self, tweet): 
        ''' 
        Utility function to classify sentiment of passed tweet 
        using textblob's sentiment method 
        '''
        # create TextBlob object of passed tweet text 
        analyser = SentimentIntensityAnalyzer()
        score = analyser.polarity_scores(self.clean_tweet(tweet))
        # set sentiment 
        if score['compound'] > 0.05: 
            return '\033[1;35;48m Positive' # weird numbers are for color coding
        elif score['compound'] >= -.05 and score['compound'] >= -.05:
            return '\033[1;36;48m Neutral' 
        else: 
            return '\033[1;30;48m Negative'

    # creates listener that prints each tweet
    def on_data(self, data):
        
               # Error handling because teachers say to do this
        try:

            # Make it JSON
            tweet = json.loads(data)

            # filter out retweets
            if not tweet['retweeted'] and 'RT @' not in tweet['text']:

                # Get user via Tweepy so we can get their number of followers
                user_profile = api.get_user(tweet['user']['screen_name'])

                # assign all data to Tweet object
                tweet_data = Tweet(
                    str(tweet['text']),
                    tweet['user']['screen_name'],
                    user_profile.followers_count,
                    tweet['created_at'],
                    tweet['user']['location'])

                # Insert that data into the DB
                tweet_data.insertTweet()
                print("Added to DB \n")
                
                sent = self.get_tweet_sentiment(tweet_data.text)
                print("\033[0;30;48m This tweet is:" + sent)
                print(tweet_data.text)
                print()#line break
                print()#line break

        # Error handler
        except Exception as e:
            print(e)
            pass

        return True
        
        

        
    
        
myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)

print("Enter keyword to stream:")
keyword = input()


myStream.filter(track=[keyword])
