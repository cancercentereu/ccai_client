import json
from pathlib import Path

import requests

from .auth import authenticate
from .queries import query_entity


class API:
    def __init__(
        self,
        organization: str | None = None,
        api_url: str = "https://api.cancercenter.ai",
        save_token_to: str | Path | None = None,
        debug_logs: bool = False,
    ):
        self.api_url = api_url
        self.organization = organization
        self.debug_logs = debug_logs
        if save_token_to:
            auth_headers_loaded = self.try_load_auth_headers(Path(save_token_to))
        else:
            auth_headers_loaded = False

        if not auth_headers_loaded:
            self.auth_headers = authenticate(self.api_url, organization)
            if save_token_to:
                self.save_auth_headers(Path(save_token_to))

    def query_graphql(self, query: str, variables: dict | None = None):
        if self.debug_logs:
            print(f"Query: {query}")
            print(f"Variables: {variables}")

        response = requests.post(
            self.api_url + "/graphql",
            json={"query": query, "variables": variables},
            headers=self.auth_headers,
        )

        if self.debug_logs:
            print(f"Response: {response.text}")

        response.raise_for_status()
        responsein_json = response.json()

        if "errors" in responsein_json:
            error_message = responsein_json["errors"][0]["message"]
            raise Exception("GraphQL query failed: " + error_message)

        data = responsein_json["data"]
        return list(data.values())[0]

    def try_load_auth_headers(self, path: Path):
        if not path.exists():
            return False

        with open(path, "r") as f:
            data = json.load(f)

        key = f"{self.api_url}:{self.organization}"
        if key not in data:
            return False

        self.auth_headers = data[key]
        return self.verify_auth()

    def save_auth_headers(self, path: Path):
        key = f"{self.api_url}:{self.organization}"
        if path.exists():
            with open(path, "r") as f:
                data = json.load(f)
        else:
            data = {}

        data[key] = self.auth_headers
        with open(path, "w") as f:
            json.dump(data, f)

    def verify_auth(self):
        try:
            data = self.query_graphql(query_entity)
            user_name = data["name"]
            organization_name = data["organization"]["name"]
            print(f"Authenticated as {user_name} in organization {organization_name}")
            return True
        except Exception as e:
            print(f"Token expired or invalid")
            return False