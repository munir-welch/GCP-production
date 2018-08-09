import apache_beam as beam

import config
import argparse
import json
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import StandardOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io.gcp.internal.clients import bigquery


options = PipelineOptions()

google_cloud_options = options.view_as(GoogleCloudOptions)
google_cloud_options.project = config.PROJECT_ID
google_cloud_options.staging_location = config.STAGING
google_cloud_options.temp_location = config.TEMP
options.view_as(StandardOptions).runner = 'DataflowRunner'
options.view_as(StandardOptions).streaming = True
options.view_as(SetupOptions)



def compute_sentiment(line):
    import textblob
    from textblob import TextBlob
    templist = line.split('-=-')
    for j, item in enumerate(templist):
        templist[j] = item.replace(',', '')
    tweet = templist[1]
    sent = TextBlob(tweet).sentiment.polarity
    templist.append(str(sent))

    diction = dict(zip(['Username', 'Tweet', 'Time', 'Followers', 'Location', 'Source', 'Sentiment'], templist))

    return diction
        
def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--requirements_file', required=True)
    parser.add_argument('--input_topic',
      help=('Input PubSub topic of the form '
            '"projects/<PROJECT>/topics/<TOPIC>".'),required=True)
    parser.add_argument(
      '--output_table', required=True,
      help=
      ('Output BigQuery table for results specified as: PROJECT:DATASET.TABLE '))
    known_args, pipeline_args=parser.parse_known_args(argv)

    with beam.Pipeline(options=options, argv=pipeline_args) as p:
        # Read the pubsub topic into a PCollection.
        lines = (p | beam.io.ReadStringsFromPubSub(topic=known_args.input_topic)
                   | beam.Map(compute_sentiment)
                   | beam.io.WriteToBigQuery(known_args.output_table,
                    schema='Username:STRING, Tweet:STRING, Time:TIMESTAMP, Followers:INTEGER, Location:STRING, Source:STRING, Sentiment:FLOAT',
                    create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                    write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND))

if __name__ == '__main__':
    run()


