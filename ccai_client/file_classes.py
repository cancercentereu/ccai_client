import os
from dataclasses import asdict
from datetime import datetime
from functools import cached_property
from pathlib import Path, PurePosixPath
from typing import Literal

import requests
from dicomweb_client.api import DICOMwebClient
from histpat_toolkit.dzi_file import DZIFile
from histpat_toolkit.image_pyramid.dzi_pyramid import DZIPyramid
from histpat_toolkit.image_pyramid.tiled_mask_pyramid import TiledMaskPyramid
from histpat_toolkit.types import SlideProperties
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass
from typing_extensions import deprecated

from ccai_client.api import API

from . import queries
from .core_classes import Comment, Tag, DiscussionMixin
from .patho import Annotation, ColorMap, Marker, PointCloud, ShapeType, TiledMask


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class File(DiscussionMixin):
    """Class for keeping track of an item in inventory."""

    api: API
    id: str
    name: str
    typename: str
    created_at: datetime
    tags: list[Tag]

    @classmethod
    def _parse_common_fields(cls, data: dict, api: API) -> dict:
        return {
            "api": api,
            "id": data["id"],
            "name": data["name"],
            "typename": data["__typename"],
            "created_at": data["createdAt"],
            "tags": [Tag.from_graphql(tag) for tag in data.get("tags", {})],
            **DiscussionMixin.parse_graphql(data),
        }

    @classmethod
    def from_graphql(cls, data: dict, api: API) -> "File":
        common_fields = cls._parse_common_fields(data, api)
        return cls(**common_fields)

    def children(self, search: str | None = None, prefix_search: str | None = None) -> list["File"]:
        objects = []
        folder_query = self.api.query_graphql(
            queries.query_folder, variables={"id": self.id, "search": search, "prefix_search": prefix_search}
        )
        edges = folder_query["children"]["edges"]
        for edge in edges:
            child = edge["node"]
            object = parse_graphql_file(child, self.api)
            objects.append(object)
        return objects

    def search_files(
        self,
        deep: bool = True,
        search: str | None = None,
        prefix_search: str | None = None,
        offset: int = 0,
        limit: int = 100,
        types: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list["File"]:
        variables = {
            "root_file_id": self.id,
            "deep": deep,
            "include_root": False,
            "search": search,
            "search_prefix": prefix_search,
            "offset": offset,
            "limit": limit,
            "type": ",".join(types) if types else None,
            "tagsValue":  ",".join(tags) if tags else None,
        }
        data = self.api.query_graphql(queries.query_deep_search_files, variables=variables)
        edges = data["edges"]
        return [parse_graphql_file(edge["node"], self.api) for edge in edges]

    def rename(self, new_name: str):
        """Rename the current file

        Args:
            new_name (str): new name for the file

        Returns:
            File: updated file object after renaming
        """
        data = self.api.query_graphql(queries.mutation_rename_file, variables={"id": self.id, "name": new_name})
        return parse_graphql_file(data["file"], self.api)

    def delete(self, parent: str):
        """Remove the current file from the given parent folder

        Args:
            parent (str): parent folder ID from which the file will be removed

        Returns:
            File: updated file object
        """
        data = self.api.query_graphql(queries.mutation_delete_file, variables={"id": self.id, "parent": parent})
        return parse_graphql_file(data["file"], self.api)

    def delete_full(self):
        """Completely delete the current file, removing it from all folders

        Returns:
            File: updated file object
        """
        data = self.api.query_graphql(queries.mutation_delete_full_file, variables={"id": self.id})
        return parse_graphql_file(data["file"], self.api)

    def link(self, target):
        """Link the current file to another folder, it will create a copy of the file in the target folder

        Args:
            target (str): target folder ID to link the file to

        Returns:
            File: updated file object
        """
        data = self.api.query_graphql(queries.mutation_link_file, variables={"id": self.id, "target": target})
        return parse_graphql_file(data["file"], self.api)

    def move(self, parent, target):
        """Move the current file from one folder to another

        Args:
            parent (str): source parent folder ID
            target (str): target folder ID where the file should be moved

        Returns:
            File: updated file object
        """
        data = self.api.query_graphql(
            queries.mutation_move_file, variables={"id": self.id, "parent": parent, "target": target}
        )
        return parse_graphql_file(data["file"], self.api)

    def add_subfolder(self, name: str):
        """Add a subfolder to the current folder

        Args:
            name (str): name of the new subfolder

        Returns:
            File: newly created subfolder object
        """
        data = self.api.query_graphql(queries.mutation_add_subfolder, variables={"parent": self.id, "name": name})
        return parse_graphql_file(data["file"], self.api)

    @staticmethod
    def get_root(api: API) -> "File":
        data = api.query_graphql(queries.query_root_file)
        return parse_graphql_file(data["fileRoot"], api)

    @staticmethod
    def get(api: API, id: str):
        data = api.query_graphql(queries.query_file, variables={"id": id})
        return parse_graphql_file(data, api)


@dataclass
class SimpleFileNode(File):
    file_name: str
    download_url: str

    @classmethod
    def from_graphql(cls, data: dict, api: API) -> "SimpleFileNode":
        common_fields = cls._parse_common_fields(data, api)
        return cls(
            **common_fields,
            file_name=data["fileName"],
            download_url=data["accessUrl"],
        )

    def download(self, path):
        r = requests.get(self.download_url)
        open(path, "wb").write(r.content)


@dataclass
class PathologySlideNode(File):
    is_ready: bool
    thumbnail_url: str | None
    dzi_url: str | None
    slide_properties: SlideProperties | None
    point_clouds: list[PointCloud]

    @classmethod
    def from_graphql(cls, data: dict, api: API) -> "PathologySlideNode":
        common_fields = cls._parse_common_fields(data, api)
        return cls(
            **common_fields,
            is_ready=data["isReady"],
            thumbnail_url=data["thumbnailUrl"],
            dzi_url=data["dziUrl"],
            slide_properties=data["slideProperties"],
            point_clouds=[PointCloud.from_graphql(edge["node"]) for edge in data["pointClouds"]["edges"]],
        )

    def list_tiled_masks(self):
        data = self.api.query_graphql(queries.query_pathologyslide_masks, variables={"id": self.id})

        edges = data["tiledMasks"]["edges"]
        masks = [TiledMask.from_graphql(edge["node"]) for edge in edges]
        return masks

    @deprecated("Use list_annotations instead")
    def list_markers(self):
        data = self.api.query_graphql(queries.query_pathologyslide_markers, variables={"id": self.id})
        edges = data["markers"]["edges"]
        markers = [Marker.from_graphql(edge["node"]) for edge in edges]
        return markers

    def list_annotations(self):
        data = self.api.query_graphql(queries.query_pathologyslide_annotations, variables={"id": self.id})
        edges = data["annotations"]["edges"]
        annotations = [Annotation.from_graphql(edge["node"]) for edge in edges]
        return annotations

    def list_annotations_of_shape(self, shape_types: list[ShapeType]):
        data = self.api.query_graphql(queries.query_pathologyslide_annotations, variables={"id": self.id})
        edges = data["annotations"]["edges"]
        annotations = [
            Annotation.from_graphql(edge["node"]) for edge in edges if edge["node"]["shapeType"] in shape_types
        ]
        return annotations

    def create_annotations_from_geojson(self, geojson: str):
        data = self.api.query_graphql(
            queries.mutation_import_annotations_from_geojson, variables={"id": self.id, "geojson": geojson}
        )
        annotations = [Annotation.from_graphql(annotation) for annotation in data["annotations"]]
        return annotations

    @cached_property
    def dzi_file(self):
        return DZIFile(self.dzi_url, properties=asdict(self.slide_properties))

    def download_original(self, path: str):
        data = self.api.query_graphql(queries.query_pathologyslide_download, variables={"id": self.id})
        download_url = data["downloadUrl"]
        r = requests.get(download_url, stream=True)

        try:
            file_name = r.headers["Content-Disposition"].split("filename=")[1][1:-1]
        except Exception:
            file_name = os.path.split(download_url)[-1].split("?")[0]

        full_path = os.path.join(path, file_name)
        with open(full_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        print("Downloaded file to {}".format(full_path))

    def get_dzi_pyramid(self) -> DZIPyramid:
        return DZIPyramid(self.dzi_file)

    def get_tiled_mask_pyramid(self, mask: TiledMask) -> TiledMaskPyramid:
        return TiledMaskPyramid(self.dzi_file, mask.get_pyramid_info(self.api))

    def upload_tiled_mask(
        self,
        file_path: str,
        color_map: str | ColorMap,
        scale: float | None = None,
        tile_size: int | None = None,
        verbose: bool = False,
        mask_type: Literal["COLORS", "KEYS"] = "COLORS",
    ) -> TiledMask:
        """Upload a tiled mask from a file.

        Args:
            file_path: Path to the mask image file
            color_map: Color map object or codename (e.g., 'gleason', 'ki67')
            scale: Optional scale parameter for the mask
            tile_size: Optional tile size for the mask
            verbose: If True, print progress messages

        Returns:
            TiledMask: The created TiledMask object

        Raises:
            ValueError: If file not found
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.is_file():
            raise ValueError(f"File not found: {file_path}")

        file_name = file_path_obj.name

        color_map_codename = color_map.codename if isinstance(color_map, ColorMap) else color_map

        if verbose:
            print(f"Uploading mask file: {file_name}")
            print(f"Using color map codename: {color_map_codename}")

        container_id = upload_files_to_container(
            api=self.api,
            local_files=[file_path],
            relative_files=[file_name],
            verbose=verbose,
        )

        if verbose:
            print("Creating tiled mask in the database...")

        variables = {
            "slide": self.id,
            "colorMapCodename": color_map_codename,
            "uploadsContainer": container_id,
            "maskType": mask_type,
        }
        if scale is not None:
            variables["scale"] = scale
        if tile_size is not None:
            variables["tileSize"] = tile_size

        mask_data = self.api.query_graphql(queries.mutation_tiledmask_create, variables=variables)
        return TiledMask.from_graphql(mask_data["tiledMask"])

    @staticmethod
    def create_from_files(
        api: API,
        sources: str | list[str],
        slide_name: str,
        parent_file_id: str,
        root_dir: str | None = None,
        verbose: bool = False,
    ):
        if isinstance(sources, str):
            sources = [sources]

        local_files = []
        for source in sources:
            source_path = Path(source)
            if source_path.is_dir():
                for file in source_path.rglob("*"):
                    if file.is_file():
                        local_files.append(str(file))
            elif source_path.is_file():
                local_files.append(str(source_path))

        if not root_dir:
            if len(local_files) > 1:
                try:
                    root_dir = os.path.commonpath(local_files)
                except ValueError:
                    raise ValueError(
                        "Cannot determine common root directory for the provided files."
                        " Please specify 'root_dir' explicitly."
                    )
            else:
                root_dir = os.path.dirname(local_files[0]) if local_files else ""

        relative_files = []
        for file in local_files:
            try:
                rel_path = PurePosixPath(file).relative_to(root_dir)
                relative_files.append(str(rel_path))
            except ValueError:
                local_files.remove(file)

        # Upload files to container
        container_id = upload_files_to_container(
            api=api,
            local_files=local_files,
            relative_files=relative_files,
            verbose=verbose,
        )

        if verbose:
            print("Creating slide in the database...")

        slide_data = api.query_graphql(
            queries.mutation_pathology_slide_create,
            variables={
                "container": container_id,
                "parent": parent_file_id,
                "name": slide_name,
            },
        )
        return slide_data["file"]["id"]


@dataclass
class PresignUpload:
    url: str
    method: str
    data: dict
    headers: dict

    @staticmethod
    def from_graphql(graphql_data):
        return PresignUpload(
            url=graphql_data["url"],
            method=graphql_data["method"],
            data=graphql_data["data"],
            headers=graphql_data["headers"],
        )


def upload_files_to_container(
    api: API,
    local_files: list[str],
    relative_files: list[str],
    verbose: bool = False,
) -> str:
    """Upload files to a container and return the container ID.

    Args:
        api: API instance
        local_files: List of local file paths to upload
        relative_files: List of relative file paths (as they should appear in the container)
        verbose: If True, print progress messages

    Returns:
        str: Container ID

    Raises:
        ValueError: If unsupported HTTP method is encountered
    """
    if verbose:
        print("Files to upload:", ", ".join(relative_files))
        print("Sending request to presign upload...")

    data = api.query_graphql(queries.mutation_upload_container, variables={"files": relative_files})
    container_id = data["container"]["id"]
    presign_uploads = [PresignUpload.from_graphql(upload) for upload in data["presignUpload"]["files"]]

    for i, presign in enumerate(presign_uploads):
        with open(local_files[i], "rb") as f:
            if verbose:
                print(f"Uploading file {relative_files[i]}...")
            if presign.method.upper() == "POST":
                response = requests.post(presign.url, data=f, headers=presign.headers)
            elif presign.method.upper() == "PUT":
                response = requests.put(presign.url, data=f, headers=presign.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {presign.method}")
            response.raise_for_status()

    return container_id


@dataclass
class DicomStudyFile(File):
    access_token: str
    dicomweb_url: str
    study_instance_uid: str

    @classmethod
    def from_graphql(cls, data: dict, api: API) -> "DicomStudyFile":
        common_fields = cls._parse_common_fields(data, api)
        return cls(
            **common_fields,
            access_token=data["study"]["accessToken"],
            dicomweb_url=data["study"]["dicomwebUrl"],
            study_instance_uid=data["study"]["studyInstanceUid"],
        )

    def download(self, path):
        client = DICOMwebClient(url=self.dicomweb_url, headers={"Authorization": "Bearer {}".format(self.access_token)})
        study = client.retrieve_study(self.study_instance_uid)

        new_folder_path = path + self.study_instance_uid
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)
        for image in study:
            image_number = image.imageNumber
            with open(f"{new_folder_path}/1-{image_number:02d}.dcm", "wb") as outfile:
                image.save_as(outfile)


@dataclass
class Form:
    id: str
    # schema_id: str
    # schema_name: str
    # data: dict


@dataclass
class FormFile(File):
    form: Form

    @classmethod
    def from_graphql(cls, data: dict, api: API) -> "FormFile":
        common_fields = cls._parse_common_fields(data, api)
        return cls(
            **common_fields,
            form=Form(id=data["form"]["id"]),
            # schema_id=data['form']['schema']['id'],
            # schema_name=data['form']['schema']['name'],
            # data=data['form']['data']
        )


@dataclass
class StudyNode(File):
    assigned_to: list[str]
    status: str

    @classmethod
    def from_graphql(cls, data: dict, api: API) -> "StudyNode":
        common_fields = cls._parse_common_fields(data, api)
        return cls(
            **common_fields,
            assigned_to=[item["entity"]["name"] for item in data["assignedTo"]],
            status=data["status"]["name"],
        )


@dataclass
class StudyListNode(File):
    @classmethod
    def from_graphql(cls, data: dict, api: API) -> "StudyListNode":
        common_fields = cls._parse_common_fields(data, api)
        return cls(**common_fields)

    def add_study(
        self,
        name=None,
        status=None,
        mode=None,
        deadline=None,
    ):
        variables = {
            "parent": self.id,
            "name": name,
            "status": status,
            "mode": mode,
            "deadline": deadline,
        }
        data = self.api.query_graphql(queries.mutation_create_study, variables=variables)
        return parse_graphql_file(data["file"], self.api)


def parse_graphql_file(returnedJSON, api):
    type_name = returnedJSON["__typename"]
    match type_name:
        case "DicomStudyFileNode":
            return DicomStudyFile.from_graphql(returnedJSON, api)
        case "SimpleFileNode":
            return SimpleFileNode.from_graphql(returnedJSON, api)
        case "PathologySlideNode" | "PathologySlideBaseNode":
            return PathologySlideNode.from_graphql(returnedJSON, api)
        case "FormFileNode":
            return FormFile.from_graphql(returnedJSON, api)
        case "StudyNode":
            return StudyNode.from_graphql(returnedJSON, api)
        case "StudyListNode":
            return StudyListNode.from_graphql(returnedJSON, api)
        case _:
            return File.from_graphql(returnedJSON, api)
