import typing as t

import pytest
from marshmallow import class_registry, fields

from mjapi.schemas import JSONAPISchema
from mjapi.fields import RelationshipType


@pytest.fixture(autouse=True)
def cleanup_marshmallow_registry():
    yield
    class_registry._registry.clear()  # noqa


class Team:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name


class User:
    def __init__(self, id: str, name: str, email: str, referrer: 'User' = None, teams: t.List[Team] = None):
        self.id: str = id
        self.name: str = name
        self.email: str = email

        self.referrer = referrer
        self.teams = teams


@pytest.fixture()
def team_schema_cls() -> t.Type[JSONAPISchema]:
    class TeamSchema(JSONAPISchema):
        class Meta:
            type_ = 'teams'

        id = fields.String()

        # attributes
        name = fields.String()

    return TeamSchema


@pytest.fixture()
def user_schema_cls(team_schema_cls) -> t.Type[JSONAPISchema]:
    class UserSchema(JSONAPISchema):
        class Meta:
            type_ = 'users'

        id = fields.String()

        # attributes
        name = fields.String()
        email = fields.Email()

        # relationships
        referrer = RelationshipType(related_schema='UserSchema')
        teams = RelationshipType(related_schema=team_schema_cls, many=True)

    return UserSchema


@pytest.fixture()
def user_schema_cls_required_fields(team_schema_cls) -> t.Type[JSONAPISchema]:
    class UserSchema(JSONAPISchema):
        class Meta:
            type_ = 'users'

        id = fields.String()

        # attributes
        name = fields.String(required=True)
        email = fields.Email(required=True)

        # relationships
        referrer = RelationshipType(related_schema='UserSchema', required=True)
        teams = RelationshipType(related_schema=team_schema_cls, many=True)

    return UserSchema


@pytest.fixture()
def team_1():
    return Team(id='t1', name='team-1')


@pytest.fixture()
def team_2():
    return Team(id='t2', name='team-2')


@pytest.fixture()
def user_1():
    return User(id='u1', name='user-1', email='user-1@test.local')


@pytest.fixture()
def user_2(user_1):
    return User(id='u2', name='user-2', email='user-2@test.local', referrer=user_1)


@pytest.fixture()
def user_3(user_1, team_1, team_2):
    return User(id='u3', name='user-3', email='user-3@test.local', referrer=user_1, teams=[team_1, team_2])


@pytest.fixture()
def user_4(user_3):
    return User(id='u4', name='user-4', email='user-4@test.local', referrer=user_3)


@pytest.fixture()
def user_schema_cls_links(team_schema_cls) -> t.Type[JSONAPISchema]:
    class UserSchema(JSONAPISchema):
        class Meta:
            type_ = 'users'
            self_url = '/api/v1/users/{id}'
            self_url_kwargs = {'id': '<id>'}
            self_url_many = '/api/v1/users/'

        id = fields.String()

        # attributes
        name = fields.String(required=True)
        email = fields.Email(required=True)

        # relationships
        referrer = RelationshipType(related_schema='UserSchema', required=True)
        teams = RelationshipType(
            related_schema=team_schema_cls,
            many=True,
            self_url='/api/v1/users/{id}/relationships/teams',
            self_url_kwargs={'id': '<id>'},
            related_url='/api/v1/users/{id}/teams',
            related_url_kwargs={'id': '<id>'},
        )

    return UserSchema
