from datetime import datetime
from typing import Any

from pydantic.dataclasses import dataclass

from ccai_client.api import API
from ccai_client.queries import mutation_comment_create


@dataclass
class Comment:
    id: str
    text: str
    author: str
    created_at: datetime

    @staticmethod
    def from_graphql(data: dict[str, Any]) -> "Comment":
        return Comment(id=data["id"], text=data["text"], author=data["author"]["name"], created_at=data["createdAt"])


@dataclass
class Tag:
    id: str
    value: str

    @staticmethod
    def from_graphql(data: dict[str, Any]) -> "Tag":
        return Tag(id=data["id"], value=data["value"])


@dataclass
class DiscussionMixin:
    discussion_id: str
    comments: list[Comment]

    @staticmethod
    def parse_graphql(data: dict[str, Any]):
        return {
            "discussion_id": data["discussion"]["id"],
            "comments": [Comment.from_graphql(edge["node"]) for edge in data["discussion"]["comments"]["edges"]],
        }

    def add_comment(self, text: str, api: API):
        variables = {"discussion": self.discussion_id, "text": text}
        data = api.query_graphql(mutation_comment_create, variables=variables)
        self.comments.append(Comment.from_graphql(data["comment"]))
