import os
import traceback
from typing import Annotated, Any, Union

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema



class MongoDBException(Exception):
    def __init__(self, message, is_warning: bool = False):
        self.uri = os.environ.get("MONGODB_URI")
        self.database_name = os.environ.get("MONGODB_DB_NAME")
        full_message = f"{message}\nDatabase Name: {self.database_name}"
        tb = traceback.format_exc()

        log_message = f"MongoDB {'Warning' if is_warning else 'Error'}: {full_message}\n\nTraceback:\n{tb}"

        if os.getenv('SEND_LOGS_TO_DISCORD') == 'True':
            if is_warning:
                print(log_message)
            else:
                print(log_message)

        super().__init__(full_message)


class ObjectIdPydanticAnnotation:
    @classmethod
    def validate_object_id(cls, v: Any, handler) -> ObjectId:
        if isinstance(v, ObjectId):
            return v

        s = handler(v)
        if ObjectId.is_valid(s):
            return ObjectId(s)
        else:
            raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, _handler) -> core_schema.CoreSchema:
        assert source_type is ObjectId
        return core_schema.no_info_wrap_validator_function(
            cls.validate_object_id,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, handler) -> JsonSchemaValue:
        return handler(core_schema.str_schema())

class MongoModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True
    )
    id: Annotated[ObjectId, ObjectIdPydanticAnnotation] = Field(default_factory=ObjectId, alias='_id',
                                                            title='The unique identifier for the document.')

    @field_serializer('id', when_used='json')
    def serialize_id(self, id: Union[ObjectId, str]) -> str:
        return str(id)

    def __init__(self, /, **data: Any) -> None:
        if '_id' in data and type(data['_id']) is not ObjectId:
            if type(data['_id']) is ObjectId:
                data['_id'] = ObjectId(data['_id'])
            elif type(data['_id']) is str:
                data['_id'] = ObjectId(data['_id'])
            else:
                raise ValueError(f"Invalid ObjectId: {data['_id']}")
        super().__init__(**data)

    def model_dump(self, *args, **kwargs):
        dump = super().model_dump(*args, **kwargs)
        if 'id' in dump:
            dump['_id'] = dump.pop('id')
        return dump
        # dump = super().model_dump(*args, **kwargs)
        # if '_id' in dump:
        #     dump.update({'id': str(dump['_id'])})
        # if 'id' in dump and '_id' in dump:
        #     dump.pop('_id')
        # return dump
