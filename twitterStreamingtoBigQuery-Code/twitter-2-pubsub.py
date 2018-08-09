import tweepy
# for connection to google biqQ later pip install --upgrade google-cloud-bigquery
# https://cloud.google.com/bigquery/docs/reference/libraries#client-libraries-install-python
import json
import csv
import config
import os
import time
import sys
import listofcities as ct

from google.cloud import bigquery, storage
from faker import Faker as fk
'''Creating the client to use with GCS - json key required if running from external application'''

storage_client = storage.Client()
#.from_service_account_json(json_credentials_path=config.STORAGE_KEY_PATH,project=config.PROJECT_ID)
bucket = storage_client.get_bucket(config.BUCKET_NAME)
import config
from google.cloud import pubsub
import os
import json
import datetime

'''Steam Listener sublcassed from the tweepy module class Stream Listener'''
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
        '''Publiah message to topic convert to sting first'''
        publine = ','.join(map(str, line))
        publish_line = publine.encode('utf-8')

        publisher.publish(topic_path, publish_line)
        print(publish_line)
        '''Try json method to hold data'''
        #deal with datatime for json object
        def datetime_handler(x):
            if isinstance(x, datetime.datetime):
                return x.isoformat()
            raise TypeError("Unknown type")

        #jlin = {'Username' : name, 'Tweet' : text, 'Time' : created, 'Followers':followers, 'Location': location, 'Source':source}
        #json_input = json.dumps(jlin,default=datetime_handler)
        #publisher.publish(topic_path, str.encode(str(json_input),'utf-8'))
        #print(str.encode(str(json_input),'utf-8'))

       # with open(config.CSV_NAME, 'a') as f:
        #    line_writer = csv.writer(f)
         #   line_writer.writerow(line)
        # returning false if the time limit runs out thus stopping the stream safely
        if (time.time() - self.start_time) < self.limit:
            return True
        else:
            return False


    def on_error(self, status_code):
        if status_code == 420:
            # returning False in on_data disconnects the stream
            return False

'''Mehtod to send csv file to GCS'''
def send_to_GCS(csv):
    blob = bucket.blob(csv)
    blob.upload_from_filename('C://Users/709231/PycharmProjects/DataMigrationProjectGCP/'+csv)
print('File {} uploaded to {}.'.format(csv,config.BUCKET_NAME))

if __name__ == '__main__':
   # os.environ[
        #"GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/709231/PycharmProjects/DataMigrationProjectGCP/pubsub-with-storage.json"

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

    #df = read_csv(config.CSV_NAME)
    #df.columns = config.COLUMN_NAMES
    #df.to_csv(config.CSV_NAME,index=False)
    #send_to_GCS(config.CSV_NAME)
    #os.system('gsutil cp' +config.CSV_NAME+' gs://'+config.BUCKET_NAME+'/Source/')

