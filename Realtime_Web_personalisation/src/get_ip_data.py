import requests 
from google.cloud import bigquery
from google.api_core.exceptions import NotFound
from faker import Faker
import time 

#---------------------------------------------------------------
#------- a one time streamer class to get IP data from api into BQ table -------

class ip_api_streamer():

	def __init__(self, project, dataset_id, table_id):

		self.endpoint = 'https://tools.keycdn.com/geo.json?host='
		self.project = project
		self.client = bigquery.Client(self.project)
		self.dataset_id = dataset_id
		self.table_id = table_id
		self.schema = [ bigquery.SchemaField("host", 'STRING', mode='NULLABLE'),
	bigquery.SchemaField("host_ip", 'STRING', mode='NULLABLE'),
	bigquery.SchemaField("isp", 'STRING', mode='NULLABLE'), bigquery.SchemaField("country_name", 'STRING', mode='NULLABLE'),
	bigquery.SchemaField("country_code", 'STRING', mode='NULLABLE'), bigquery.SchemaField("reigion_name", 'STRING', mode='NULLABLE'),
	bigquery.SchemaField("region_code", 'STRING', mode='NULLABLE'), bigquery.SchemaField("city", 'STRING', mode='NULLABLE'),
	bigquery.SchemaField("continent_name", 'STRING', mode='NULLABLE')]

		while True:
			self.dataset_ref = self.client.dataset(self.dataset_id)
			try:
				dataset = self.client.get_dataset(self.dataset_ref)
				print('dataset exists')
				break
			except NotFound:
				print('dataset does not exist')
				dataset = bigquery.Dataset(self.dataset_ref)
				dataset.location = 'EU'
				dataset = self.client.create_dataset(dataset)
				assert dataset.dataset_id == self.dataset_id
				print('created dataset '+ dataset.dataset_id)
				break
		while True:
			self.table_ref = self.dataset_ref.table(self.table_id)
			try:
				table = self.client.get_table(self.table_ref)
				print('Table exists')
				break
			except NotFound:
				print('table does not exsist')
				table = bigquery.Table(self.table_ref, self.schema)
				table = self.client.create_table(table)
				assert table.table_id == self.table_id
				print('created table '+ table.table_id)
				break

	def fake_ip_streamer(self):
		
		fake = Faker()
		
		count = 1
		while True:

			if count % 3 != 0:
				ip = fake.ipv4()
				url = self.endpoint+ip
				response = requests.get(url)
				if response.ok:
					data = response.json()
					full_data = {}
					if data['status'] == 'success':
						ip_data = data['data']
						geo_data = ip_data['geo']
						full_data['host'] = geo_data['host']
						full_data['host_ip'] = geo_data['ip']
						full_data['isp'] = geo_data['isp']
						full_data['country_name'] = geo_data['country_name']
						full_data['country_code'] = geo_data['country_code']
						full_data['reigion_name'] = geo_data['region_name']
						full_data['region_code'] = geo_data['region_code']
						full_data['city'] = geo_data['city']
						full_data['continent_name'] = geo_data['continent_name']
						errors = self.client.insert_rows_json(self.table_ref, [full_data])
						if errors:
							for error in errors:
								print(error)
						else:
							print('records inserted')
							count += 1
				else:
					response.raise_for_status()
			else:
				time.sleep(2)
				count += 1
				pass

streamer = ip_api_streamer('warm-airline-207713', 'webserver_raw', 'ip_geo_match')

print(streamer.fake_ip_streamer())




