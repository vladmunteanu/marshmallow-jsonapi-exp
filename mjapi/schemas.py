import typing as t

from marshmallow import Schema, fields

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

        jsonapi_schema = {
            'id': schema_id_field,
            'type': schema_type_field,
            'attributes': fields.Nested(Schema.from_dict(schema_attributes)),
            'relationships': fields.Nested(Schema.from_dict(schema_relationships)),
        }

        new_schema_cls = Schema.from_dict(jsonapi_schema, name=f'{cls.__name__}_JSONAPI')

        def _get_attribute(schema_self, obj, attr, default):
            if attr == 'attributes':
                return obj
            if attr == 'relationships':
                return obj
            return super(schema_self.__class__, schema_self).get_attribute(obj, attr, default)

        new_schema_cls.get_attribute = _get_attribute

        def _load_and_flatten(schema_self, *args, **kwargs):
            ret = super(schema_self.__class__, schema_self).load(*args, **kwargs)
            ret.update(**ret.pop('attributes', {}))
            ret.pop('type', None)
            ret.update({rel_name: rel['data']['id'] for rel_name, rel in ret.pop('relationships', {}).items()})
            return ret

        new_schema_cls.load = _load_and_flatten

        def _dump_and_remove_empty_relationships(schema_self, *args, **kwargs):
            ret = super(schema_self.__class__, schema_self).dump(*args, **kwargs)
            if not kwargs.get('many'):
                ret_list = [ret]
            else:
                ret_list = ret

            for ret_item in ret_list:
                ret_relationships = ret_item.pop('relationships', {})
                for rel_name, rel_data in ret_relationships.copy().items():
                    if rel_data is None:
                        del ret_relationships[rel_name]
                if ret_relationships:
                    ret_item['relationships'] = ret_relationships

            if not kwargs.get('many'):
                return ret_list[0]
            return ret_list

        new_schema_cls.dump = _dump_and_remove_empty_relationships

        return new_schema_cls
