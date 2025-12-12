import json

from ccai_client import API

url = input("Enter API url: ")

api = API(api_url=url)

print("Add these headers to your graphql query:")
print(json.dumps(api.auth_headers, indent=4))
