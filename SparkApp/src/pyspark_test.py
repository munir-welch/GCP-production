from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession, Row
import requests
import time
import pandas

#-----------------------------------------------------------------------------------------------------------------------------------#
#---------------------------Spark web logs enrichment-------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------------------------------------------------------#


#If running on dataproc need to specify initialisation action to install packages like pandas etc 

# when running on Dataproc cluster leave conf as it is but when running on local cluster use below as conf to pass to SparkSession
#SparkConf().setMaster("spark://FVFY724MHV2H:7077").setAppName("pyspark_test").set("spark.executor.memory", "1g")
conf = (SparkConf().setAppName("pyspark_test"))
#spark session context gives access to new Dataset, DataFrame, SQL API'S as of spark 2.0 
spark=SparkSession.builder.config(conf=conf).getOrCreate()
#Spark context used for dealing with RDD API
sc = spark.sparkContext

#reading text files in RDD
#/Users/munir.welch/Desktop/GCP-production/SparkApp/src/log_b.txt
logData = sc.textFile("gs://weblogserver/log_b.txt").cache()
gcsData = sc.textFile('gs://weblogserver/http_codes_raw-00000-of-00001.txt')


def parse_logs(element):
	ip = element.split('- -')[0].replace(' ','')
	timestamp = element.split('+')[0].replace('[','').split('- -')[1]
	request = element.split('- -')[1].split('"')[1]
	http_code = element.split('- -')[1].split('"')[2].split(' ')[1]
	url = element.split('- -')[1].split('"')[3]
	platform = element.split('- -')[1].split('"')[5].split('(')[1].split(")")[0]	

	return {'ip':ip, 'timestamp':timestamp, 'request':request, 'http_code':http_code, 'url':url, 'platform':platform}

def pars_gcs(element):
	http_code = element.split(',')[0].replace('(', '')
	meaning = element.split(',')[1].replace(')','')
	return {'http_code':http_code, 'meaning':meaning}


def geo_api_call(element):
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
			element['region_name'] = geo_data['region_name']
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
			element['region_name'] = None
			element['region_code'] = None  
			element['city'] = None
			element['continent_name'] = None
			time.sleep(1)
			return element


#parsing log file and preparing for RDD ---> DataFrame transformation by constructing Row object 
parsed_logs = logData.map(parse_logs)            #.map(geo_api_call)
parsed_logs_df = parsed_logs.map(lambda x : Row(ip=x['ip'], timestamp=x['timestamp'], request=x['request'], http_code=x['http_code'], url=x['url'],
 platform=x['platform']))


'''
 , host_ip=x['host_ip'], isp=x['isp'], country_name=x['country_name'], country_code=x['country_name'], region_name=x['region_name'],
 region_code=x['region_code'], city=x['city'], continent_name=x['continent_name']))
'''
parsed_gcsData = gcsData.map(pars_gcs)
gcs_data_df = parsed_gcsData.map(lambda x : Row(http_code=x['http_code'], meaning=str(x['meaning'])))

logsDF = spark.createDataFrame(parsed_logs_df)
gcsDF = spark.createDataFrame(gcs_data_df)

combined = logsDF.join(gcsDF, gcsDF.http_code == logsDF.http_code, how='left_outer').drop(logsDF.http_code)



pandas_combined = combined.toPandas()

print(pandas_combined.dtypes) 

pandas_combined.to_gbq(destination_table='webserver_raw.spark_weblog_test', project_id='warm-airline-207713', if_exists = 'append')



logsDF.show()
gcsDF.show()
combined.show()


