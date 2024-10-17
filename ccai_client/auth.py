import time

import requests
from requests.auth import _basic_auth_str


def create_token(api_url: str, organization: str | None):
    headers = {}
    if organization:
        headers["x-organization"] = organization
    response = requests.post(api_url + "/api/token/create", headers=headers)
    response.raise_for_status()
    result = response.json()
    return result["authorization_url"], result["activation_code"]


def wait_for_login(api_url: str, activation_code: str) -> dict[str, str] | None:
    response = requests.post(api_url + "/api/token/activate", json={"activation_code": activation_code})
    if response.status_code == 401:
        return
    response.raise_for_status()
    result = response.json()
    first_name = result["user"]["first_name"]
    last_name = result["user"]["last_name"]
    organization = result["organization"]["name"]
    auth_token = result["auth_token"]
    print(f"Logged in as {first_name} {last_name} in organization {organization}")
    return {"x-api-token": auth_token}


def authenticate(api_url: str, organization: str | None) -> dict[str, str]:
    magic_link, activation_code = create_token(api_url, organization)
    print("Paste the following link in your browser:\n\n" + magic_link)

    while True:
        time.sleep(1)
        auth = wait_for_login(api_url, activation_code=activation_code)
        if auth:
            return auth
