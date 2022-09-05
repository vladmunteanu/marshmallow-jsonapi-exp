import pytest

from marshmallow import ValidationError, missing

from mjapi.fields import RelationshipType


def test_relationship_load_data_single(team_schema_cls):
    field = RelationshipType(
        many=False,
        related_schema=team_schema_cls,
    )
    value = {'data': {'type': 'teams', 'id': '1'}}
    ret = field.get_jsonapi_relationship_schema('field')().load(value)
    assert ret == '1'


def test_relationship_load_data_many(team_schema_cls):
    field = RelationshipType(
        many=True,
        related_schema=team_schema_cls,
    )
    value = {'data': [{'type': 'teams', 'id': '1'}, {'type': 'teams', 'id': '2'}]}
    ret = field.get_jsonapi_relationship_schema('field')().load(value)
    assert ret == ['1', '2']


def test_relationship_load_data_missing_id(team_schema_cls):
    field = RelationshipType(
        many=False,
        related_schema=team_schema_cls,
    )
    with pytest.raises(ValidationError) as excinfo:
        value = {'data': {'type': 'teams'}}
        field.get_jsonapi_relationship_schema('field')().load(value)
    assert excinfo.value.messages == {'data': {'id': ['Missing data for required field.']}}


def test_relationship_load_data_missing_type(team_schema_cls):
    field = RelationshipType(
        many=False,
        related_schema=team_schema_cls,
    )
    with pytest.raises(ValidationError) as excinfo:
        value = {'data': {'id': '123'}}
        field.get_jsonapi_relationship_schema('field')().load(value)
    assert excinfo.value.messages == {'data': {'type': ['Missing data for required field.']}}


def test_relationship_load_data_incorrect_type(team_schema_cls):
    field = RelationshipType(
        many=False,
        related_schema=team_schema_cls,
    )
    with pytest.raises(ValidationError) as excinfo:
        value = {'data': {'type': 'posts', 'id': '1'}}
        field.get_jsonapi_relationship_schema('field')().load(value)
    assert excinfo.value.messages == {'data': {'type': ['Invalid `type` specified']}}


def test_relationship_load_null_data_value(team_schema_cls):
    field = RelationshipType(
        allow_none=True,
        many=False,
        related_schema=team_schema_cls,
    )
    result = field.get_jsonapi_relationship_schema('field')().load({'data': None})
    assert result is None


def test_relationship_load_null_value_disallow_none(team_schema_cls):
    field = RelationshipType(
        allow_none=False,
        many=False,
        related_schema=team_schema_cls,
    )
    with pytest.raises(ValidationError) as excinfo:
        field.get_jsonapi_relationship_schema('field')().load({'data': None})
    assert excinfo.value.messages == {'data': ['Field may not be null.']}


def test_relationship_load_empty_data_list(team_schema_cls):
    field = RelationshipType(
        many=True,
        related_schema=team_schema_cls,
    )
    result = field.get_jsonapi_relationship_schema('field')().load({'data': []})
    assert result == []


def test_relationship_load_empty_data(team_schema_cls):
    field = RelationshipType(
        many=False,
        related_schema=team_schema_cls,
    )
    with pytest.raises(ValidationError) as excinfo:
        field.get_jsonapi_relationship_schema('field')().load({'data': {}})
    assert excinfo.value.messages == {
        'data': {
            'id': ['Missing data for required field.'],
            'type': ['Missing data for required field.'],
        }
    }
