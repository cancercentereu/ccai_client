from ccai_client.queries import *
from pydantic.dataclasses import dataclass
from dataclasses import asdict
from ccai_client.api import API
from datetime import datetime
import requests
import json
from dicomweb_client.api import DICOMwebClient
import os
from histpat_toolkit.types import SlideProperties
from histpat_toolkit.dzi_file import DZIFile
from histpat_toolkit.image_pyramid.dzi_pyramid import DZIPyramid
from histpat_toolkit.image_pyramid.tiled_mask_pyramid import TiledMaskPyramid
from functools import cached_property
from .patho import TiledMask, Marker
from pydantic import ConfigDict
from .patho import TiledMask, Marker, PointCloud
from typing import Any
from .core_classes import Comment
from tqdm import tqdm


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class File:
    """Class for keeping track of an item in inventory."""
    api: API
    id: str
    name: str
    typename: str
    created_at: datetime
    comments: list[Comment]


    def children(self) -> list["File"]:
        objects = []
        folder_query = self.api.query_graphql(query_folder, variables={
            'id': self.id
        })
        edges = folder_query['childEdges']['edges']
        for edge in edges:
            child = edge['node']['child']
            object = parse_graphql_file(child, self.api)
            objects.append(object)
        return objects

    @staticmethod
    def get(api: API, id: str):
        data = api.query_graphql(query_file, variables={
            'id': id
        })
        return parse_graphql_file(data, api)


@dataclass
class SimpleFileNode(File):
    file_name: str
    download_url: str

    def download(self, path):
        r = requests.get(self.download_url)
        open(path, "wb").write(r.content)
    

@dataclass
class PathologySlideNode(File):
    is_ready: bool
    thumbnail_url: str
    dzi_url: str
    slide_properties: SlideProperties
    point_clouds: list[PointCloud]

    def list_tiled_masks(self):
        data = self.api.query_graphql(query_pathologyslide_masks, variables={
            'id': self.id
        })
        edges = data['tiledMasks']['edges']
        masks = [
            TiledMask.from_graphql(edge['node'])
            for edge in edges
        ]
        return masks
    
    def list_markers(self):
        data = self.api.query_graphql(query_pathologyslide_markers, variables={
            'id': self.id
        })
        edges = data['markers']['edges']
        markers = [
            Marker.from_graphql(edge['node'])
            for edge in edges
        ]
        return markers

    @cached_property
    def dzi_file(self):
        return DZIFile(self.dzi_url, properties=asdict(self.slide_properties))

    def download_original(self, path: str, verbose=True):
        data = self.api.query_graphql(query_pathologyslide_download, variables={
            'id': self.id
        })
        download_url = data['downloadUrl']
        r = requests.get(download_url, stream=True)

        content_disposition = r.headers.get('Content-Disposition')
        if content_disposition and 'filename=' in content_disposition:
            file_name = content_disposition.split('filename=')[1].strip('"')
        else:
            file_name = os.path.split(download_url)[-1]
            file_name = file_name.split('?', 1)[0]

        full_path = os.path.join(path, file_name)
        with open(full_path, "wb") as f:
            total_length = int(r.headers.get('content-length'))
            for chunk in tqdm(r.iter_content(chunk_size=8192), total=total_length/8192, unit='KB', desc=file_name, disable=not verbose):
                f.write(chunk)

        if verbose:
            print("Downloaded file to {}".format(full_path))
        return full_path

    def get_dzi_pyramid(self) -> DZIPyramid:
        return DZIPyramid(self.dzi_file)

    def get_tiled_mask_pyramid(self, mask: TiledMask) -> TiledMaskPyramid:
        return TiledMaskPyramid(self.dzi_file, mask.get_pyramid_info(self.api))


@dataclass
class DicomStudyFile(File):
    access_token: str
    dicomweb_url: str
    study_instance_uid: str

    def download(self, path):
        client = DICOMwebClient(
            url=self.dicomweb_url,
            headers={"Authorization": "Bearer {}".format(self.access_token)})
        study = client.retrieve_study(
            self.study_instance_uid
        )

        new_folder_path = path+self.study_instance_uid
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)
        for image in study:
            image_number = image.imageNumber
            with open(f"{new_folder_path}/1-{image_number:02d}.dcm", 'wb') as outfile:
                image.save_as(outfile)


@dataclass
class Form:
    id: str
    schema_id: str
    schema_name: str
    data: dict


@dataclass
class FormFile(File):
    form: Form


def parse_graphql_file(returnedJSON, api):
    type_name = returnedJSON['__typename']
    match type_name:
        case 'DicomStudyFileNode':
            output = DicomStudyFile(api=api,
                                    id=returnedJSON['id'],
                                    name=returnedJSON['name'],
                                    typename=returnedJSON['__typename'],
                                    created_at=returnedJSON['createdAt'],
                                    access_token=returnedJSON['study']['accessToken'],
                                    dicomweb_url=returnedJSON['study']['dicomwebUrl'],
                                    study_instance_uid=returnedJSON['study']['studyInstanceUid'],
                                    comments=map(lambda edge: Comment.from_graphql(edge['node']), returnedJSON['discussion']['comments']['edges'])
                                    )
        case 'SimpleFileNode':
            output = SimpleFileNode(api=api,
                                    id=returnedJSON['id'],
                                    name=returnedJSON['name'],
                                    typename=returnedJSON['__typename'],
                                    created_at=returnedJSON['createdAt'],
                                    file_name=returnedJSON['fileName'],
                                    download_url=returnedJSON["accessUrl"],
                                    comments=map(lambda edge: Comment.from_graphql(edge['node']), returnedJSON['discussion']['comments']['edges']))
        case 'PathologySlideNode':
            output = PathologySlideNode(api=api,
                                        id=returnedJSON['id'],
                                        name=returnedJSON['name'],
                                        typename=returnedJSON['__typename'],
                                        created_at=returnedJSON['createdAt'],
                                        is_ready=returnedJSON['isReady'],
                                        thumbnail_url=returnedJSON['thumbnailUrl'],
                                        dzi_url=returnedJSON['dziUrl'],
                                        slide_properties=returnedJSON['slideProperties'],
                                        comments=map(lambda edge: Comment.from_graphql(edge['node']), returnedJSON['discussion']['comments']['edges']),
                                        point_clouds=map(
                                            lambda edge: PointCloud.from_graphql(edge['node']),
                                            returnedJSON['pointClouds']['edges']
                                        )
                                        )
        case 'FormFileNode':
            output = FormFile(api=api,
                              id=returnedJSON['id'],
                              name=returnedJSON['name'],
                              typename=returnedJSON['__typename'],
                              created_at=returnedJSON['createdAt'],
                              form=Form(
                                  id=returnedJSON['form']['id'],
                                  schema_id=returnedJSON['form']['schema']['id'],
                                  schema_name=returnedJSON['form']['schema']['name'],
                                  data=returnedJSON['form']['data']
                              ),
                              comments=map(lambda edge: Comment.from_graphql(edge['node']), returnedJSON['discussion']['comments']['edges'])
                              )

        case _:
            output = File(api=api,
                          id=returnedJSON['id'],
                          name=returnedJSON['name'],
                          typename=returnedJSON['__typename'],
                          created_at=returnedJSON['createdAt'],
                          comments=map(lambda edge: Comment.from_graphql(edge['node']), returnedJSON['discussion']['comments']['edges'])
                          )

    return output
