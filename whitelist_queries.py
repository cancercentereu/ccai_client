import re
import sys

import requests

import ccai_client.queries

GRAPHQL_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/graphql"

for query in dir(ccai_client.queries):
    query_body = getattr(ccai_client.queries, query)
    if not isinstance(query_body, str):
        continue

    query_search = re.search(r"(query|mutation) +([a-zA-Z0-9_]+)", query_body)
    if not query_search:
        continue
    query_name = query_search.group(2)
    print(f"{query}: {query_name}")
    requests.post(GRAPHQL_URL, json={"query": query_body, "operationName": query_name}, headers={"x-save-query": "1"})
