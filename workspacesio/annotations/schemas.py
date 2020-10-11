import datetime
import uuid
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

from workspacesio.schemas import DBBaseModel, WorkspaceDB


class DatasetType(str, Enum):
    VIDEO = "video"
    IMAGE_SEQUENCE = "image_sequence"


class GeoJSONGeometry(BaseModel):
    type: str
    coordinates: Union[List[List[float]], List[List[List[float]]]]


class GeoJSONFeature(BaseModel):
    type: str
    geometry: GeoJSONGeometry
    properties: Dict[str, Union[bool, float, str]]


class GeoJSONFeatureCollection(BaseModel):
    type: str
    features: List[GeoJSONFeature]


class Feature(BaseModel):
    """Feature represents a single detection in a track."""

    frame: int
    bounds: List[float]
    geometry: Optional[GeoJSONFeatureCollection] = None
    head: Optional[Tuple[float, float]] = None
    tail: Optional[Tuple[float, float]] = None
    fishLength: Optional[float] = None
    attributes: Optional[Dict[str, Union[bool, float, str]]] = None
    interpolate: Optional[bool] = False
    keyframe: Optional[bool] = True


###########################################################


class AnnotationDatasetBase(BaseModel):
    workspace_id: uuid.UUID
    source_type: DatasetType
    # filename if source type is video
    media_filename: str
    fps: int = 30
    # prefix inside workspace
    media_prefix: str = ""


class AnnotationDatasetCreate(AnnotationDatasetBase):
    pass


class AnnotationDatasetDB(DBBaseModel, AnnotationDatasetBase):
    workspace: WorkspaceDB


###########################################################


class TrackBase(BaseModel):
    dataset_id: uuid.UUID
    begin: int
    end: int
    track_id: int
    features: List[Feature] = []
    confidencePairs: List[Tuple[str, float]] = []
    attributes: Optional[Dict[str, Union[bool, float, str]]] = None


class TrackCreate(TrackBase):
    pass


class TrackDB(DBBaseModel, TrackBase):
    pass
