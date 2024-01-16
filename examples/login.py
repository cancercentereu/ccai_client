from ccai_client import API
import json

organization = input('Enter organization codename: ')

api = API(organization)

headers = {
  'x-organization': organization,
  'authorization': 'Bearer ' + api.jwt
}

print('Add these headers to your graphql query:')
print(json.dumps(headers, indent=4))