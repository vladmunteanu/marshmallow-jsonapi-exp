import typing as t

from marshmallow import Schema, SchemaOpts, fields
from marshmallow.class_registry import get_class

if t.TYPE_CHECKING:
    from mjapi.schemas import JSONAPISchema


class RelationshipType(fields.String):
    def __init__(
            self, *, related_schema: t.Union[t.Type['JSONAPISchema'], str],
            many: bool = False, id_field: str = '', **kwargs,
    ):
        self.related_schema = related_schema
        self.many = many
        self.id_field = id_field
        super().__init__(**kwargs)

    def _get_related_schema(self) -> 'JSONAPISchema':
        if isinstance(self.related_schema, str):
            return get_class(self.related_schema)
        return self.related_schema

    def get_jsonapi_relationship_schema(self, relationship_name: str) -> t.Type[Schema]:
        related_schema_cls = self._get_related_schema()
        relationship = {
            'id': fields.String(),
            'type': fields.Constant(getattr(related_schema_cls, 'type', 'unknown')),
        }

        data_field = fields.Nested(Schema.from_dict(relationship))
        if self.many:
            data_field = fields.List(data_field)

        class RelationshipSchema(Schema):
            data = data_field

            class Meta(SchemaOpts):
                register = False

            def get_attribute(schema_self, obj, attr, default):
                """ Overwrite to handle included data. """
                # serializing
                if relationship_name in schema_self.context.get('to_include', set()):
                    included_data = schema_self.context.setdefault('included_data', [])
                    included_data.append(related_schema_cls.get_jsonapi_resource_object_schema()().dump(obj))
                if attr == 'data':
                    return obj
                return super().get_attribute(obj, attr, default)

        return RelationshipSchema
