import requests


url = 'http://127.0.0.1:5002/list-data/Donald_Trump_Sentiment'

response = requests.get(url)

if response.ok:
	print(type(response.text))


else:
	response.raise_for_status()