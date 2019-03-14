from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import json
from google.cloud import bigquery 
from datetime import date, datetime



client  = bigquery.Client(project='warm-airline-207713')
dataset_id = 'Stocks'

app = Flask(__name__)
api = Api(app)


class Hello_world(Resource):
	def get(self):
		return 'Hello_world'

class get_top_locations(Resource):
	def get(self, table_id):
		job_config = bigquery.QueryJobConfig()
		dataset_ref = client.dataset(dataset_id)
		table_ref = dataset_ref.table(table_id)
		job_config.destination = table_ref
		job_config.use_legacy_sql = False

		sql = (
		 "SELECT symbol, company, change_percent, price  FROM `warm-airline-207713.Stocks.stocks_data_NASDAQ` where latest_trading_day = date('2019-03-13') order by change_percent desc  LIMIT 5"
		 )

		query_job = client.query(sql,location='EU')


		results = []
		for row in query_job:
				counts = {'symbol':row[0], 'company':row[1], 'change_percent':row[2], 'price':row[3]}
		
				results.append(counts)

		return jsonify(results)





api.add_resource(Hello_world, "/")
api.add_resource(get_top_locations, "/list-top-5/<table_id>")

if __name__ == '__main__':
	app.run(port=5002)