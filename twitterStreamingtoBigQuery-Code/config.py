
'''Twitter 2 PubSub Configuration'''


#ENTER YOUR GCP PROJECT ID
PROJECT_ID ='warm-airline-207713'

#ENTER YOUR PUBSUB TOPIC NAME e.g 'twitter-stream'
TOPIC_NAME = 'twitter-stream'

#ENTER THE HASHTAG YOU WANT TO TRACK 
TRACK_TERMS = "brexit"

#ENTER HOW LONG YOU WITH TO STREAM FOR IN SECONDS 
STREAM_TIME = 10

#ENTER YOUR TWITTER CREDENTIALS 
TWITTER_APP_KEY = 'KPVEb25geZ1WUxMrJz3flS6je'
TWITTER_APP_SECRET = 'BcjmYWEJmDuU81gwW3Hs64mnzH4I67EzgS0H5FfuIs7VFjkXtH'
TWITTER_KEY = '1014592058215059456-Z1pGlZHdMvx8vsszkDWpsEdTCjfz4o'
TWITTER_SECRET = 'Zsw17mh9OiXDfaf993njgHhGZHxYTHrrD9Ae8fgqEc1mq'



'''Stream-Tweets-Dataflow Configuration'''

#PLEASE ENTER A GCS STAGING LOCATION IN THE FORM gs://<BUCKET_NAME>/staging
STAGING = 'gs://dod-mwja-project1/staging'

#PLEASE ENTER A GCS TEMP LOCATION IN THE FROM gs://<BUCKET_NAME>/temp
TEMP = 'gs://dod-mwja-project1/temp'
