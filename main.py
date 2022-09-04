import datetime as dt
import typing as t
from pprint import pprint

from marshmallow import fields

from mjapi.schemas import JSONAPISchema
from mjapi.fields import RelationshipType


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

schema_cls = UserSchema.get_jsonapi_schema()
schema = schema_cls()
first_output_result = schema.dump(first_user)
second_output_result = schema.dump(second_user)
third_output_result = schema.dump(third_user)

# test many serialization
fourth_output_result = schema.dump([first_user, second_user], many=True)

# test only
only_schema = schema_cls(only=['attributes.name'])
fifth_output_result = only_schema.dump(first_user)


print('\n' + ' FIRST USER RESULT IS '.center(100, '=') + '\n')
pprint(first_output_result)
print('\n' + ' SECOND USER RESULT IS '.center(100, '=') + '\n')
pprint(second_output_result)
print('\n' + ' THIRD USER RESULT IS '.center(100, '=') + '\n')
pprint(third_output_result)

print('\n' + ' FOURTH USER RESULT IS '.center(100, '=') + '\n')
pprint(fourth_output_result)

print('\n' + ' FIFTH USER RESULT IS '.center(100, '=') + '\n')
pprint(fifth_output_result)

team_schema_cls = TeamSchema.get_jsonapi_schema()
team_schema = team_schema_cls()
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
