import typing as t

from marshmallow import Schema, SchemaOpts, fields, validate
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

        self._related_schema_cls = None
        self._related_jsonapi_schema_cls = None
        super().__init__(**kwargs)

    @property
    def related_schema_cls(self) -> 'JSONAPISchema':
        if not self._related_schema_cls:
            if isinstance(self.related_schema, str):
                self._related_schema_cls = get_class(self.related_schema)
            else:
                self._related_schema_cls = self.related_schema
        return self._related_schema_cls

    @property
    def related_jsonapi_schema_cls(self):
        if not self._related_jsonapi_schema_cls:
            self._related_jsonapi_schema_cls = self.related_schema_cls.get_jsonapi_resource_object_schema()
        return self._related_jsonapi_schema_cls

    def get_jsonapi_relationship_schema(self, relationship_name: str) -> t.Type[Schema]:
        relationship = {
            'id': fields.String(required=True),  # use self to preserve parameters defined on the initial schema
            'type': fields.String(
                dump_default=self.related_schema_cls.type,
                required=True,
                validate=validate.Equal(self.related_schema_cls.type, error='Invalid `type` specified'),
            ),
        }

        data_field = fields.Nested(Schema.from_dict(relationship), required=True, allow_none=self.allow_none)
        if self.many:
            data_field = fields.List(data_field)

        class RelationshipSchema(Schema):
            data = data_field

            class Meta(SchemaOpts):
                register = False

            def get_attribute(schema_self, obj, attr, default):
                """ Overwrite to handle included data. """
                # handle included data

                if relationship_name in schema_self.context.get('to_include', set()):
                    # serialize related object
                    obj_many = obj
                    if not self.many:
                        obj_many = [obj_many]
                    for rel_obj in obj_many:
                        included_repr = self.related_jsonapi_schema_cls(context=schema_self.context).dump(rel_obj)
                        # add to already included data from context
                        included_data = schema_self.context.setdefault('included_data', {})
                        included_data[(included_repr['type'], included_repr['id'])] = included_repr
                if attr == 'data':
                    return obj
                return super().get_attribute(obj, attr, default)

            def load(schema_self, *args, **kwargs):
                """ Overwrite to flatten data. """
                ret = super().load(*args, **kwargs)
                if self.many:
                    ret = [related_item['id'] for related_item in ret['data']]
                else:
                    if ret['data']:
                        ret = ret['data'].get('id')
                    else:
                        ret = None
                return ret

        return RelationshipSchema
