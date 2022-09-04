import typing as t

from marshmallow import Schema, SchemaOpts, fields

from mjapi.fields import RelationshipType


class JSONAPISchema(Schema):
    type: str

    @classmethod
    def get_jsonapi_schema(cls) -> t.Type[Schema]:
        schema_declared_fields = cls._declared_fields.copy()
        schema_id_field = schema_declared_fields.pop('id')
        schema_type_field = fields.Constant(getattr(cls, 'type', 'unknown'))

        schema_attributes = {}
        schema_relationships = {}
        for field_name, field in schema_declared_fields.items():
            if isinstance(field, RelationshipType):
                schema_relationships[field_name] = fields.Nested(field.get_jsonapi_relationship_schema())
            else:
                schema_attributes[field_name] = field

        class _JSONAPISchema(Schema):

            class Meta(SchemaOpts):
                register = False

            id = schema_id_field
            type = schema_type_field
            attributes = fields.Nested(Schema.from_dict(schema_attributes))
            relationships = fields.Nested(Schema.from_dict(schema_relationships))

            def __init__(self, *, only=None, **kwargs):
                new_only = [] if only else None
                if only:
                    for field_name in only:
                        if field_name in cls._declared_fields:
                            if isinstance(cls._declared_fields[field_name], RelationshipType):
                                new_only.append(f'relationships.{field_name}')
                            else:
                                new_only.append(f'attributes.{field_name}')

                    new_only += ['id', 'type']
                super().__init__(only=new_only, **kwargs)

            def get_attribute(self, obj: t.Any, attr: str, default: t.Any):
                if attr in ('attributes', 'relationships'):
                    return obj
                return super().get_attribute(obj, attr, default)

            def load(self, *args, **kwargs):
                """ Overwrite to flatten attributes, relationships and remove type. """
                ret = super().load(*args, **kwargs)
                ret.update(**ret.pop('attributes', {}))
                ret.pop('type', None)
                ret.update({rel_name: rel['data']['id'] for rel_name, rel in ret.pop('relationships', {}).items()})
                return ret

            def dump(self, *args, **kwargs):
                """ Overwrite to remove empty relationships. """
                ret = super().dump(*args, **kwargs)
                many = kwargs.get('many')
                ret = ret if many else [ret]

                for ret_item in ret:
                    ret_relationships = ret_item.pop('relationships', {})
                    for rel_name, rel_data in ret_relationships.copy().items():
                        if rel_data is None:
                            del ret_relationships[rel_name]
                    if ret_relationships:
                        ret_item['relationships'] = ret_relationships

                return ret if many else ret[0]

        return _JSONAPISchema
