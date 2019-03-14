import requests 
import json
from google.cloud import bigquery 
from google.api_core.exceptions import NotFound
from config import Config
import time

#4BKD8YNBAM7EATJM
class Stock_Api():

	def __init__(self, base_url, api_key, function):

		self.base_url = base_url
		self.api_key = api_key
		self.function = function
		self.config = Config()
		self.stock_list = list(self.config.company_dict.keys())
		self.new_keys = new_keys = {"01. symbol":'symbol', "02. open":'open', "03. high":'high', "04. low":'low', 
	"05. price":'price', "06. volume":'volume', "07. latest trading day":'latest_trading_day', 
	"08. previous close":'previous_close', "09. change":'change', "10. change percent":'change_percent'}
		self.stock_dict = self.config.company_dict

	def get_data(self):

		
		data_list = []
		for stock in self.stock_list:
		
			url = self.base_url+'function='+self.function+'&symbol='+stock+'&apikey='+self.api_key
			response = requests.get(url)
			if response.ok:
				data = response.json()
				stock_data = data['Global Quote']
				stock_data["10. change percent"] = stock_data["10. change percent"].replace('%','')
				data_list.append(stock_data)
			else:
				response.raise_for_status()
			time.sleep(1)
			print('colllected ', len(data_list), ' stocks' )
			if len(data_list) % 5 != 0:
				pass
			else:
				time.sleep(62)
		return data_list

	def fix_keys(self, data_dict):

		try:
			assert len(data_dict) == len(self.new_keys)
			fixed_data = dict((self.new_keys[key], value) for (key, value) in data_dict.items())
			return fixed_data
		except AssertionError:
			print('please supply dicts of same lengths')

	def add_company_names(self, data_dict):

		for key in self.stock_dict.keys():

			if data_dict['symbol'] == key:
				data_dict['company'] = self.stock_dict[key]
		return data_dict



class Send_to_bq():

	def __init__(self, project):

		self.project = project
		self.client = bigquery.Client(self.project)

	def create_table(self, dataset_id, table_id, schema=None):

		while True:
			dataset_ref = self.client.dataset(dataset_id)
			try:
				dataset = self.client.get_dataset(dataset_ref)
				print('dataset exists')
				break
			except NotFound:
				print('dataset does not exist')
				dataset = bigquery.Dataset(dataset_ref)
				dataset.location = 'EU'
				dataset = self.client.create_dataset(dataset)
				assert dataset.dataset_id == dataset_id
				print('created dataset '+ dataset.dataset_id)
				break
		while True:
			table_ref = dataset_ref.table(table_id)
			try:
				table = self.client.get_table(table_ref)
				print('Table exists')
				break
			except NotFound:
				print('table does not exsist')
				table = bigquery.Table(table_ref, schema)
				table = self.client.create_table(table)
				assert table.table_id == table_id
				print('created table '+ table.table_id)
				break

	def streaming_insert(self,dataset_id, table_id, rows_to_insert):

		table_ref = self.client.dataset(dataset_id).table(table_id)
		errors = self.client.insert_rows_json(table_ref, rows_to_insert)
		if errors:
			for error in errors:
				print(error)
		else:
			print('records inserted')

if __name__ == '__main__':

	#Getting data from the stocks API
	base_url = 'https://www.alphavantage.co/query?'
	api_key = 'SA1NIAP7NKF6IOTM'
	function = 'GLOBAL_QUOTE'

	api = Stock_Api(base_url,api_key,function)

	raw_data = api.get_data()
	

	# Cleaning data for streaming

	ready_to_stream = []
	for stock_data in raw_data:
		x = api.add_company_names(api.fix_keys(stock_data))
		ready_to_stream.append(x)
	print('ready to stream')


	# Streaming data into bq 
	did = 'Stocks'
	tid = 'stocks_data_NASDAQ'
	schema = [ bigquery.SchemaField("symbol", 'STRING', mode='NULLABLE'),
	bigquery.SchemaField("open", 'FLOAT', mode='NULLABLE'), bigquery.SchemaField("high", 'FLOAT', mode='NULLABLE'),
	bigquery.SchemaField("low", 'FLOAT', mode='NULLABLE'), bigquery.SchemaField("price", 'FLOAT', mode='NULLABLE'),
	bigquery.SchemaField("volume", 'FLOAT', mode='NULLABLE'), bigquery.SchemaField("latest_trading_day", 'DATE', mode='NULLABLE'),
	bigquery.SchemaField("previous_close", 'FLOAT', mode='NULLABLE'), bigquery.SchemaField("change", 'FLOAT', mode='NULLABLE'),
	bigquery.SchemaField("change_percent", 'FLOAT', mode='NULLABLE'), bigquery.SchemaField("company", 'STRING', mode='NULLABLE'),
	]
	
	stocks_bq_client = Send_to_bq(project='warm-airline-207713')
	stocks_bq_client.create_table(dataset_id=did , table_id=tid, schema=schema)
	

	stocks_bq_client.streaming_insert(dataset_id=did, table_id=tid, rows_to_insert=ready_to_stream)
	



