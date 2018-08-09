import tweepy
import config
import os
import time
import sys
import listofcities as ct
from google.cloud import pubsub

'''Creating the client to use with GCS - json key required if running from external application'''
storage_client = storage.Client()
bucket = storage_client.get_bucket(config.BUCKET_NAME)



'''Steam Listener subclassed from the tweepy module class Stream Listener'''
class StreamListener(tweepy.StreamListener):
    def __init__(self, time_limit=60):
        self.start_time = time.time()
        self.limit = time_limit
        super(StreamListener, self).__init__()


    '''Overiding the on_status method see tweepy documentation '''
    def on_status(self, status):

        if status.retweeted:
            return

        text = status.text
        # the text of the tweet
        name = status.user.screen_name
        followers = status.user.followers_count
        # How many followers the user has (status.user.followers_count).
        created = status.created_at
        # When the tweet was sent (status.created_at).
        location = ct.r_city()
        source = ct.r_source()
        #print(type(created), created)

        # here we need to ocnstruct the final line of data and send each line to a csv that will remain in the folder
        line = [name, '-=-', text, '-=-', created, '-=-', followers, '-=-', location, '-=-', source]
        
        '''Publish message to topic convert to sting first'''
        publine = ','.join(map(str, line))
        publish_line = publine.encode('utf-8')

        publisher.publish(topic_path, publish_line)
        print(publish_line)
        
   
        if (time.time() - self.start_time) < self.limit:
            return True
        else:
            return False


    def on_error(self, status_code):
        if status_code == 420:
            # returning False in on_data disconnects the stream
            return False


if __name__ == '__main__':

    '''Create publisher client'''
    publisher = pubsub.PublisherClient()

    '''Set topic path with topic name and Project id'''
    topic_path = publisher.topic_path(config.PROJECT_ID, 'twitter-stream')

    '''Create initial topic'''
    #publisher.create_topic(topic_path)


    auth = tweepy.OAuthHandler(config.TWITTER_APP_KEY, config.TWITTER_APP_SECRET)
    auth.set_access_token(config.TWITTER_KEY, config.TWITTER_SECRET)
    api = tweepy.API(auth)


    stream_listener = StreamListener(time_limit=5)
    stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
    stream.filter(track=config.TRACK_TERMS)


