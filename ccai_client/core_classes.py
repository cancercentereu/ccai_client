from pydantic.dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class Comment:
    id: str
    text: str
    author: str
    created_at: datetime

    @staticmethod
    def from_graphql(data: dict[str, Any]) -> 'Comment':
        return Comment(
            id=data['id'],
            text=data['text'],
            author=data['author']['name'],
            created_at=data['createdAt']
        )
