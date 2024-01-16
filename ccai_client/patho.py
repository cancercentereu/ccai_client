from pydantic.dataclasses import dataclass
from ccai_client.api import API
from .queries import query_tiledmask_tiles
from histpat_toolkit.types import Tile, ColorMap, TiledMaskPyramidInfo
from histpat_toolkit.geom import Rectangle
from .core_classes import Comment
from typing import Any

@dataclass
class Marker:
    x: float
    y: float
    rotation: float
    width: float
    height: float
    author: str | None
    number: int | None
    comments: list[Comment]

    def as_rectangle(self, image_width: float) -> Rectangle:
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        return Rectangle.with_center(cx, cy, self.width, self.height, -self.rotation).scale(image_width)
    
    @staticmethod
    def from_graphql(data):
        return Marker(
            x=data['x'],
            y=data['y'],
            rotation=data['rotation'],
            width=data['width'],
            height=data['height'],
            author=data['author']['name'] if data['author'] else None,
            number=data['number'],
            comments=map(lambda edge: Comment.from_graphql(edge['node']), data['discussion']['comments']['edges'])
        )


@dataclass
class Rating:
    score: int
    author: str

    @staticmethod
    def from_graphql(data: dict[str, Any]) -> 'Rating':
        return Rating(
            score=data['score'],
            author=data['author']['name']
        )


@dataclass
class PointCloudStatistic:
    color: str
    key: str
    count: int
    
    @staticmethod
    def from_graphql(data: dict[str, Any]) -> 'PointCloudStatistic':
        return PointCloudStatistic(
            color=data['color']['name'],
            key=data['color']['value'],
            count=data['value']
        )


@dataclass
class PointCloudPoint:
    x: int
    y: int
    color_key: int
    
    @staticmethod
    def from_graphql(data: dict[str, Any]) -> 'PointCloudPoint':
        return PointCloudPoint(
            x=data['x'],
            y=data['y'],
            color_key=data['value']
        )


@dataclass
class PointCloud:
    id: str
    statistics: list[PointCloudStatistic]
    points: list[PointCloudPoint]
    
    @staticmethod
    def from_graphql(data: dict[str, Any]) -> 'PointCloud':
        return PointCloud(
            id=data['id'],
            statistics=list(map(
                PointCloudStatistic.from_graphql,
                data['statistics']
            )),
            points=map(
                lambda edge: PointCloudPoint.from_graphql(edge['node']),
                data['points']['edges']
            )
        )

@dataclass
class Algorithm:
    name: str
    comments: list[Comment]
    ratings: list[Rating]


@dataclass
class TiledMask:
    id: str
    author: str | None
    algorithm: Algorithm | None
    color_map: ColorMap | None

    @staticmethod
    def from_graphql(data):
        return TiledMask(
            id=data['id'],
            author=data['author']['name'] if data['author'] else None,
            algorithm=(
                Algorithm(
                    name=data['algorithmRun']['algorithm']['name'],
                    comments=(
                        map(lambda edge: Comment.from_graphql(edge['node']),
                            data['algorithmRun']['discussion']['comments']['edges'])
                    ),
                    ratings=(
                        map(Rating.from_graphql,
                            data['algorithmRun']['ratings'])
                    )
                )
                if data['algorithmRun']
                else None
            ),
            color_map=ColorMap.from_graphql(
                data['colorMap']) if data['colorMap'] else None
        )

    def get_pyramid_info(self, api: API):
        data = api.query_graphql(query_tiledmask_tiles, variables={
            'id': self.id
        })
        return TiledMaskPyramidInfo(
            tiles=[Tile(x=tile['x'], y=tile['y'], level=tile['level'])
                   for tile in data['tiles']],
            scale=data['scale'],
            tiles_url=data['tilesUrl'],
            tile_size=data['tileSize']
        )
