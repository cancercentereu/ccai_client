from datetime import datetime
from enum import StrEnum
from typing import Any

from histpat_toolkit.geom import Circle, Ellipse, Point, Polygon, Rectangle, Shape
from histpat_toolkit.types import Tile, TiledMaskPyramidInfo
from pydantic.dataclasses import dataclass

from ccai_client.api import API

from .core_classes import Comment, DiscussionMixin
from .queries import (
    mutation_run_algorithm,
    mutation_update_annotation,
    query_all_algorithms,
    query_all_color_maps,
    query_tiledmask_tiles,
)


@dataclass
class Marker(DiscussionMixin):
    x: float
    y: float
    rotation: float
    width: float
    height: float
    author: str | None
    number: int | None

    def as_rectangle(self, image_width: float) -> Rectangle:
        return Rectangle(self.x, self.y, self.width, self.height, self.rotation).scale(image_width)

    @staticmethod
    def from_graphql(data):
        return Marker(
            x=data["x"],
            y=data["y"],
            rotation=data["rotation"],
            width=data["width"],
            height=data["height"],
            author=data["author"]["name"] if data["author"] else None,
            number=data["number"],
            **DiscussionMixin.parse_graphql(data),
        )


class ShapeType(StrEnum):
    RECT = "rect"
    POLYGON = "polygon"
    CIRCLE = "circle"
    ELLIPSE = ("ellipse",)
    PATH = "path"
    CLOSED_PATH = "closed_path"
    LINE = "line"
    ARROW_LINE = "arrow_line"
    POINT = "point"
    TEXT = "text"


@dataclass
class Annotation(DiscussionMixin):
    id: str
    shape_type: ShapeType
    shape_data: list[float]
    author: str | None
    slide_id: str
    number: int | None
    label: str | None
    is_label_visible: bool | None
    color: str | None
    point_type: str | None
    created_at: datetime

    @staticmethod
    def from_graphql(data):
        return Annotation(
            id=data["id"],
            shape_type=ShapeType(data["shapeType"]),
            shape_data=data["shapeData"],
            author=data["author"]["name"] if data["author"] else None,
            slide_id=data["slideId"],
            number=data["number"],
            label=data["label"],
            is_label_visible=data["isLabelVisible"],
            color=data["color"],
            point_type=data["pointType"],
            created_at=data["createdAt"],
            **DiscussionMixin.parse_graphql(data),
        )

    def change_label_visibility(self, api: API, is_visible: bool) -> None:
        variables = {"id": self.id, "isLabelVisible": is_visible}
        data = api.query_graphql(mutation_update_annotation, variables=variables)
        self.is_label_visible = data["annotation"]["isLabelVisible"]

    def as_shape(self) -> Shape:
        shape_type = self.shape_type
        shape_data = self.shape_data
        match shape_type:
            case ShapeType.RECT:
                return Rectangle(shape_data[0], shape_data[1], shape_data[2], shape_data[3])
            case ShapeType.POLYGON | ShapeType.CLOSED_PATH | ShapeType.PATH:
                return Polygon(points=[Point(x, y) for x, y in zip(shape_data[::2], shape_data[1::2])])
            case ShapeType.CIRCLE:
                return Circle(Point(shape_data[0], shape_data[1]), shape_data[2])
            case ShapeType.ELLIPSE:
                return Ellipse(Point(shape_data[0], shape_data[1]), (shape_data[2], shape_data[3]))
            case _:
                raise ValueError(f"Shape type: {shape_type} not supported")


@dataclass
class Rating:
    score: int
    author: str

    @staticmethod
    def from_graphql(data: dict[str, Any]) -> "Rating":
        return Rating(score=data["score"], author=data["author"]["name"])


@dataclass
class PointCloudStatistic:
    color: str
    key: str
    count: int

    @staticmethod
    def from_graphql(data: dict[str, Any]) -> "PointCloudStatistic":
        return PointCloudStatistic(color=data["color"]["name"], key=data["color"]["value"], count=data["value"])


@dataclass
class PointCloudPoint:
    x: int
    y: int
    color_key: int
    radius: float | None = None
    score: int | None = None

    @staticmethod
    def from_graphql(data: dict[str, Any]) -> "PointCloudPoint":
        return PointCloudPoint(x=data["x"], y=data["y"], color_key=data["v"], radius=data["r"], score=data["s"])


@dataclass
class PointCloud:
    id: str
    statistics: list[PointCloudStatistic]
    points: list[PointCloudPoint]

    @staticmethod
    def from_graphql(data: dict[str, Any]) -> "PointCloud":
        return PointCloud(
            id=data["id"],
            statistics=[PointCloudStatistic.from_graphql(item) for item in data["statistics"]],
            points=[PointCloudPoint.from_graphql(item) for item in data["pointsList"]],
        )


@dataclass
class Algorithm:
    id: str
    name: str

    @staticmethod
    def from_graphql(data: dict[str, Any]) -> "Algorithm":
        return Algorithm(id=data["id"], name=data["name"])

    @staticmethod
    def get_all_algorithms(api: API) -> list["Algorithm"]:
        data = api.query_graphql(query_all_algorithms)
        return [Algorithm.from_graphql(edge["node"]) for edge in data["edges"]]


@dataclass
class RunAlgorithm:
    algorithm: Algorithm
    comments: list[Comment] | None = None
    ratings: list[Rating] | None = None

    @staticmethod
    def from_graphql(data: dict[str, Any]) -> "RunAlgorithm":
        return RunAlgorithm(
            algorithm=Algorithm.from_graphql(data["algorithm"]),
            comments=[Comment.from_graphql(edge["node"]) for edge in data["discussion"]["comments"]["edges"]],
            ratings=[Rating.from_graphql(item) for item in data["ratings"]],
            **DiscussionMixin.parse_graphql(data),
        )

    @staticmethod
    def run(api: API, slide_id: str, algorithm_id: str, roi=None):
        variables = {"slide": slide_id, "algorithm": algorithm_id, "roi": roi if roi else None}
        response = api.query_graphql(mutation_run_algorithm, variables=variables)
        return RunAlgorithm.from_graphql(response["algorithmRun"])


@dataclass
class Color:
    name: str
    key: int
    value: str


@dataclass
class ColorMap:
    id: str
    name: str
    codename: str
    colors: list[Color]

    @staticmethod
    def from_graphql(data):
        return ColorMap(
            id=data["id"],
            name=data["name"],
            codename=data["codename"],
            colors=[Color(**color["node"]) for color in data["colors"]["edges"]],
        )

    @staticmethod
    def get_all_color_maps(api: API) -> list["ColorMap"]:
        data = api.query_graphql(query_all_color_maps)
        return [ColorMap.from_graphql(edge["node"]) for edge in data["edges"]]

    @staticmethod
    def get_by_codename(api: API, codename: str) -> "ColorMap":
        all_maps = ColorMap.get_all_color_maps(api)
        for color_map in all_maps:
            if color_map.codename == codename:
                return color_map
        raise ValueError(f"Color map with codename '{codename}' not found")


@dataclass
class TiledMask:
    id: str
    author: str | None
    algorithm: RunAlgorithm | None
    color_map: ColorMap | None

    @staticmethod
    def from_graphql(data):
        print('data', data)
        return TiledMask(
            id=data["id"],
            author=data["author"]["name"] if data["author"] else None,
            algorithm=(
                RunAlgorithm(
                    algorithm=Algorithm.from_graphql(data["algorithmRun"]["algorithm"]),
                    comments=[
                        Comment.from_graphql(edge["node"])
                        for edge in data["algorithmRun"]["discussion"]["comments"]["edges"]
                    ],
                    ratings=[Rating.from_graphql(item) for item in data["algorithmRun"]["ratings"]],
                )
                if data["algorithmRun"]
                else None
            ),
            color_map=ColorMap.from_graphql(data["colorMap"]) if data["colorMap"] else None,
        )

    def get_pyramid_info(self, api: API):
        data = api.query_graphql(query_tiledmask_tiles, variables={"id": self.id})
        return TiledMaskPyramidInfo(
            tiles=[Tile(x=tile["x"], y=tile["y"], level=tile["level"]) for tile in data["tiles"]],
            scale=data["scale"],
            tiles_url=data["tilesUrl"],
            tile_size=data["tileSize"],
        )
