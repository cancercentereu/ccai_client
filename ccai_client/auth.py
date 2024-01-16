import requests
import time
from urllib.parse import urlparse, parse_qs


def get_magic_link(api_url: str, organization: str):
    response = requests.get(
        api_url + '/auth/cli/get-magic-link', headers={'x-organization': organization})
    response.raise_for_status()
    return response.text


def wait_for_login(api_url: str, pre_auth_session_id: str) -> str | None:
    response = requests.post(api_url + '/auth/cli/wait-for-login', json={
        "preAuthSessionId": pre_auth_session_id
    })
    if response.status_code == 401:
        return
    response.raise_for_status()
    return response.text


def authenticate(api_url: str, organization: str) -> str:
    magic_link = get_magic_link(api_url, organization)
    print('Paste the following link in your browser:\n\n' + magic_link)

    parsed = urlparse(magic_link)
    query = parse_qs(parsed.query)
    pre_auth_session_id: str = query['preAuthSessionId'][0]

    while True:
        time.sleep(1)
        jwt = wait_for_login(api_url, pre_auth_session_id=pre_auth_session_id)
        if jwt:
            return jwt
