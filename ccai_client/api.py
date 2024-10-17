import requests
from ccai_client.auth import authenticate
import json


class API:
    def __init__(self, organization: str | None = None, api_url: str = "https://api.cancercenter.ai"):
        self.api_url = api_url
        self.organization = organization
        self.auth_headers = authenticate(self.api_url, organization)

    def query_graphql(self, query: str, variables: dict | None = None):
        response = requests.post(
            self.api_url + "/graphql",
            json={"query": query, "variables": variables},
            headers=self.auth_headers,
        )

        response.raise_for_status()
        responsein_json = response.json()
        if responsein_json.get('errors'):
            raise Exception('Request failed with errors: ' + json.dumps(responsein_json['errors'], indent=2))

        data = responsein_json["data"]
        return list(data.values())[0]
