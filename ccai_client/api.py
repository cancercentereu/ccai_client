from ccai_client.auth import authenticate
import requests
from ccai_client.queries import *
import json


class API:
	def __init__(self, organization: str, api_url: str = 'https://api.cancercenter.ai'):
		self.api_url=api_url
		self.organization=organization
		jwt = authenticate(self.api_url, organization)
		self.jwt=jwt

	def query_graphql(self, query: str, variables: dict | None = None):
		response = requests.post(self.api_url + '/graphql', json={ "query": query,"variables":variables}, headers={
			'authorization': 'Bearer ' + self.jwt,
			'x-organization': self.organization
		})
		
		response.raise_for_status()
		responsein_json=response.json()
		# TODO: check responsein_json['errors']

		data = responsein_json['data']
		return list(data.values())[0]
		