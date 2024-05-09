from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class KMeansRequest(_message.Message):
    __slots__ = ("temp",)
    TEMP_FIELD_NUMBER: _ClassVar[int]
    temp: bool
    def __init__(self, temp: bool = ...) -> None: ...

class KMeansResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class MapRequest(_message.Message):
    __slots__ = ("mapper_id", "start_index", "end_index", "centroids")
    MAPPER_ID_FIELD_NUMBER: _ClassVar[int]
    START_INDEX_FIELD_NUMBER: _ClassVar[int]
    END_INDEX_FIELD_NUMBER: _ClassVar[int]
    CENTROIDS_FIELD_NUMBER: _ClassVar[int]
    mapper_id: int
    start_index: int
    end_index: int
    centroids: _containers.RepeatedCompositeFieldContainer[Centroid]
    def __init__(self, mapper_id: _Optional[int] = ..., start_index: _Optional[int] = ..., end_index: _Optional[int] = ..., centroids: _Optional[_Iterable[_Union[Centroid, _Mapping]]] = ...) -> None: ...

class MapResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class ReduceRequest(_message.Message):
    __slots__ = ("centroid_id",)
    CENTROID_ID_FIELD_NUMBER: _ClassVar[int]
    centroid_id: int
    def __init__(self, centroid_id: _Optional[int] = ...) -> None: ...

class ReduceResponse(_message.Message):
    __slots__ = ("success", "centroid_id", "updated_centroid")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    CENTROID_ID_FIELD_NUMBER: _ClassVar[int]
    UPDATED_CENTROID_FIELD_NUMBER: _ClassVar[int]
    success: bool
    centroid_id: int
    updated_centroid: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, success: bool = ..., centroid_id: _Optional[int] = ..., updated_centroid: _Optional[_Iterable[float]] = ...) -> None: ...

class DataPoint(_message.Message):
    __slots__ = ("x", "y")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ...) -> None: ...

class Centroid(_message.Message):
    __slots__ = ("centroid_id", "value")
    CENTROID_ID_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    centroid_id: int
    value: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, centroid_id: _Optional[int] = ..., value: _Optional[_Iterable[float]] = ...) -> None: ...
