import typing as t

from marshmallow import Schema, fields
from marshmallow.class_registry import get_class


class RelationshipType(fields.String):
    def __init__(
            self, *, related_schema: t.Union[t.Type[Schema], str], many: bool = False, id_field: str = '', **kwargs,
    ):
        self.related_schema = related_schema
        self.many = many
        self.id_field = id_field
        super().__init__(**kwargs)

    def _get_related_schema(self):
        if isinstance(self.related_schema, str):
            return get_class(self.related_schema)
        return self.related_schema

    def get_jsonapi_relationship_schema(self) -> t.Type[Schema]:
        relationship = {
            'id': fields.String(),
            'type': fields.Constant(getattr(self._get_related_schema(), 'type', 'unknown')),
        }

        data = fields.Nested(Schema.from_dict(relationship))
        if self.many:
            data = fields.List(data)
        schema_dict = {
            'data': data,
        }
        schema_cls = Schema.from_dict(schema_dict)

        # wrapping everything in data messes with how the attributes are accessed,
        # so we make data refer to the object being serialized which makes further access to .id successful
        def _get_attribute(schema_self, obj, attr, default):
            if attr == 'data':
                return obj
            return super(schema_self.__class__, schema_self).get_attribute(schema_self, obj, attr, default)
        schema_cls.get_attribute = _get_attribute

        return schema_cls
