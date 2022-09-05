import typing as t

from marshmallow import Schema, SchemaOpts, fields

from mjapi.fields import RelationshipType


class ErrorObjectSchema(Schema):
    id = fields.String()
    links = fields.Dict()  # TODO: schema for links
    status = fields.String()
    code = fields.String()
    title = fields.String()
    detail = fields.String()
    source = fields.Dict()  # TODO: schema for source
    meta = fields.Dict()

    def dump(self, *args, **kwargs):
        """ Overwrite to remove empty fields. """
        ret = super().dump(*args, **kwargs)
        for field_name in self._declared_fields.keys():
            if ret.get(field_name) is None:
                ret.pop(field_name)
        return ret


class JSONAPIObjectSchema(Schema):
    version = fields.String()


class JSONAPISchema(Schema):
    jsonapi_object_schema: t.Type[Schema] = JSONAPIObjectSchema
    error_object_schema: t.Type[Schema] = ErrorObjectSchema
    type: str = ''

    @classmethod
    def get_jsonapi_resource_object_schema(cls) -> t.Type[Schema]:
        schema_declared_fields = cls._declared_fields.copy()
        # using the id field that is defined on the schema
        schema_id_field = schema_declared_fields.pop('id')
        schema_type_field = fields.Constant(cls.type)

        # add fields for attributes and relationships
        schema_attributes = {}
        schema_relationships = {}
        for field_name, field in schema_declared_fields.items():
            if isinstance(field, RelationshipType):
                schema_relationships[field_name] = fields.Nested(
                    field.get_jsonapi_relationship_schema(relationship_name=field_name)
                )
            else:
                schema_attributes[field_name] = field

        class ResourceObjectSchema(Schema):

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

        return ResourceObjectSchema

    @classmethod
    def get_jsonapi_top_level_schema(cls, many: bool = False) -> t.Type[Schema]:
        resource_object_schema_cls = cls.get_jsonapi_resource_object_schema()

        class TopLevelSchema(Schema):
            class Meta(SchemaOpts):
                register = False
                ordered = True

            data = fields.Nested(resource_object_schema_cls)
            if many:
                data = fields.List(data)
            errors = fields.List(fields.Nested(cls.error_object_schema))
            meta = fields.Dict()
            included = fields.List(fields.Dict())
            jsonapi = fields.Nested(cls.jsonapi_object_schema)
            # TODO schema for links
            links = fields.Dict(keys=fields.String(), values=fields.String())

            def __init__(self, *, only=None, **kwargs):
                new_only = [] if only else None
                if only:
                    for field_name in only:
                        # this will get stripped when passed to nested schemas
                        new_only.append(f'data.{field_name}')

                    new_only += ['errors', 'meta', 'included', 'jsonapi', 'links']
                super().__init__(only=new_only, **kwargs)

            def get_attribute(self, obj: t.Any, attr: str, default: t.Any):
                if attr == 'data' and not isinstance(obj, Exception):
                    return obj
                elif attr == 'errors' and isinstance(obj, Exception):
                    # TODO support multiple errors
                    return [obj]
                elif attr == 'included':
                    # TODO included data and deduplication
                    return self.context.get('included_data', default)
                elif attr == 'meta':
                    return self.context.get('top_level_meta', default)
                elif attr == 'jsonapi':
                    return self.context.get('jsonapi_info', default)
                return default

            def load(self, *args, **kwargs):
                """ Overwrite to flatten data. """
                ret = super().load(*args, **kwargs)
                ret.update(**ret.pop('data', {}))
                return ret

        return TopLevelSchema
