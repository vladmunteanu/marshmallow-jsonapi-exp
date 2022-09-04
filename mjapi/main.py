import datetime as dt
import typing as t
from pprint import pprint

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


class JSONAPISchema(Schema):
    type: str

    @classmethod
    def get_jsonapi_schema(cls) -> Schema:
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
            ret_relationships = ret.pop('relationships', {})
            for rel_name, rel_data in ret_relationships.copy().items():
                if rel_data is None:
                    del ret_relationships[rel_name]

            if ret_relationships:
                ret['relationships'] = ret_relationships
            return ret

        new_schema_cls.dump = _dump_and_remove_empty_relationships

        return new_schema_cls()


class Team:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name


class User:
    def __init__(self, id: str, name: str, email: str, referrer: 'User' = None, teams: t.List[Team] = None):
        self.id: str = id
        self.name: str = name
        self.email: str = email
        self.created_at = dt.datetime.now()

        self.referrer = referrer
        self.teams = teams


class TeamSchema(JSONAPISchema):
    type = 'teams'

    id = fields.String()

    # attributes
    name = fields.String()


class UserSchema(JSONAPISchema):
    type = 'users'

    id = fields.String()

    # attributes
    name = fields.String()
    email = fields.Email()
    created_at = fields.DateTime()

    # relationships
    referrer = RelationshipType(related_schema='UserSchema')
    teams = RelationshipType(related_schema=TeamSchema, many=True)


team_1 = Team(id='t1', name='Team 1')
team_2 = Team(id='t2', name='Team 2')

first_user = User(id='u1', name="First", email="first@python.org")
second_user = User(id='u2', name="Second", email="second@python.org", referrer=first_user)
third_user = User(id='u3', name="Third", email="third@python.org", referrer=first_user, teams=[team_1, team_2])

schema = UserSchema.get_jsonapi_schema()
first_output_result = schema.dump(first_user)
second_output_result = schema.dump(second_user)
third_output_result = schema.dump(third_user)


print('\n' + ' FIRST USER RESULT IS '.center(100, '=') + '\n')
pprint(first_output_result)
print('\n' + ' SECOND USER RESULT IS '.center(100, '=') + '\n')
pprint(second_output_result)
print('\n' + ' THIRD USER RESULT IS '.center(100, '=') + '\n')
pprint(third_output_result)

team_schema = TeamSchema.get_jsonapi_schema()
first_team_result = team_schema.dump(team_1)
print('\n' + ' FIRST TEAM RESULT IS '.center(100, '=') + '\n')
pprint(first_team_result)
second_team_result = team_schema.dump(team_2)
print('\n' + ' SECOND TEAM RESULT IS '.center(100, '=') + '\n')
pprint(second_team_result)

input = {
    'id': '5',
    'type': 'users',
    'attributes': {
        'name': 'Test Input',
        'email': 'test_input@mail.com',
    },
    'relationships': {
        'referrer': {
            'data': {
                'id': '123',
                'type': 'users',
            }
        }
    }
}

print('\n' + ' RESULT FROM INPUT IS '.center(100, '=') + '\n')
pprint(schema.load(input))
