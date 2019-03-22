import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import StandardOptions
from apache_beam.options.pipeline_options import SetupOptions
import requests 
import time



options = PipelineOptions()
options.view_as(GoogleCloudOptions).staging_location = 'gs://weblogserver/stage'
options.view_as(GoogleCloudOptions).temp_location = 'gs://weblogserver/temp'
options.view_as(GoogleCloudOptions).project = 'warm-airline-207713'
options.view_as(GoogleCloudOptions).region = 'europe-west1'
options.view_as(GoogleCloudOptions).job_name = 'web-data-enrichment' 
options.view_as(StandardOptions).runner = 'DataflowRunner'
options.view_as(StandardOptions).streaming = False
options.view_as(SetupOptions).save_main_session = True






def parse_web_logs(element):
	ip = element.split('- -')[0].replace(' ','')
	timestamp = element.split('+')[0].replace('[','').split('- -')[1]
	request = element.split('- -')[1].split('"')[1]
	http_code = element.split('- -')[1].split('"')[2].split(' ')[1]
	url = element.split('- -')[1].split('"')[3]
	platform = element.split('- -')[1].split('"')[5].split('(')[1].split(")")[0]	

	return {'ip':ip, 'timestamp':timestamp, 'request':request, 'http_code':http_code, 'url':url, 'platform':platform}


def enrich_logs(element, side_input):

	if int(element['http_code']) in side_input.keys():
		element['http_code_meaning'] = side_input[int(element['http_code'])]
		#yield element
	return element
	
def unpack_generator(element):
	return [x for x in element]


def get_geoip_data(element):
	#element = element[0]
	ip = element['ip']
	url = 'https://tools.keycdn.com/geo.json?host='+ip
	api_call = requests.get(url)
	if api_call.ok:
		data = api_call.json()
		if data['status'] == 'success':
			ip_data = data['data']
			geo_data = ip_data['geo']
			element['host_ip'] = geo_data['ip']
			element['isp'] = geo_data['isp']
			element['country_name'] = geo_data['country_name']
			element['country_code'] = geo_data['country_code']
			element['reigion_name'] = geo_data['region_name']
			element['region_code'] = geo_data['region_code']
			element['city'] = geo_data['city']
			element['continent_name'] = geo_data['continent_name']
			time.sleep(1)
			return element
		else:
			element['host_ip'] = None
			element['isp'] = None
			element['country_name'] = None
			element['country_code'] = None
			element['reigion_name'] = None
			element['region_code'] = None  
			element['city'] = None
			element['continent_name'] = None
			time.sleep(1)
			return element


def fix_empty_data(element):

	for key in element.keys():
		if  element[key] == '':
			element[key] = None
	return element

# need to add functionality to handle when ip is not found my api to get_geoip_data()

query = "SELECT code,_meaning FROM `warm-airline-207713.webserver_raw.http_error_codes`"


schema = 'ip:STRING, host_ip:STRING, country_name:STRING, country_code:STRING, reigion_name:STRING, region_code:STRING, city:STRING, continent_name:STRING, isp:STRING, timestamp:STRING, request:STRING, url:STRING, http_code:STRING, http_code_meaning:STRING, platform:STRING'

def run(argv=None):

	with beam.Pipeline(options=options) as p:

		weblogs = (p | 'read weblogs' >> beam.io.ReadFromText(file_pattern='gs://weblogserver/log_b.txt')
					 | 'parse_web_logs' >> beam.Map(parse_web_logs))


		http_codes = (p | 'read http code table' >> beam.io.Read(beam.io.BigQuerySource(query=query, use_standard_sql=True))
						| 'make KV' >> beam.Map(lambda row : (row['code'], row['_meaning'])))


		enrich_weblogs_with_http = (weblogs | 'enrich http codes' >> beam.Map(enrich_logs,side_input=beam.pvalue.AsDict(http_codes)))
		
											#| 'loop over generator' >> beam.Map(unpack_generator)

		add_ipgeo_data = (enrich_weblogs_with_http | 'enrich ipgeo data' >> beam.Map(get_geoip_data)
												   | 'fix empty data' >> beam.Map(fix_empty_data))
	   
		write_to_bigquery = (add_ipgeo_data | 'fully enriched to big query' >> beam.io.WriteToBigQuery(table='geo_enriched_weblogs', dataset='webserver_raw', project='warm-airline-207713', schema=schema, create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED, write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND))


		write_geo_enriched_logs = ( add_ipgeo_data | 'enriched geo data to gcs' >> beam.io.WriteToText(file_path_prefix='gs://weblogserver/enriched_geo_logs', file_name_suffix='.txt', num_shards=1))
		
		
		write_enriched_logs = ( enrich_weblogs_with_http | 'enriched http to gcs' >> beam.io.WriteToText(file_path_prefix='gs://weblogserver/enriched_http_logs', file_name_suffix='.txt', num_shards=1))


		write_raw_logs = (weblogs | 'raw logs to gcs' >> beam.io.WriteToText(file_path_prefix='gs://weblogserver/logs_raw', file_name_suffix='.txt', num_shards=1))


		write_raw_codes = (http_codes | 'raw HTTP to gcs' >> beam.io.WriteToText(file_path_prefix='gs://weblogserver/http_codes_raw', file_name_suffix='.txt', num_shards=1))


if __name__ == '__main__':
	run()
