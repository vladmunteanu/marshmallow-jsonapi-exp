def test_team_schema_jsonapi_simple(team_schema_cls, team_1):
    team_schema_cls = team_schema_cls.get_jsonapi_schema()
    serialized = team_schema_cls().dump(team_1)
    assert serialized == {
        'id': team_1.id,
        'type': 'teams',
        'attributes': {
            'name': team_1.name,
        },
    }


def test_user_schema_jsonapi_empty_relationships(user_schema_cls, user_1):
    user_schema_cls = user_schema_cls.get_jsonapi_schema()
    serialized = user_schema_cls().dump(user_1)
    assert serialized == {
        'id': user_1.id,
        'type': 'users',
        'attributes': {
            'name': user_1.name,
            'email': user_1.email,
        },
    }


def test_user_schema_jsonapi_relationship(user_schema_cls, user_1, user_2):
    user_schema_cls = user_schema_cls.get_jsonapi_schema()
    serialized = user_schema_cls().dump(user_2)
    assert serialized == {
        'id': user_2.id,
        'type': 'users',
        'attributes': {
            'name': user_2.name,
            'email': user_2.email,
        },
        'relationships': {
            'referrer': {
                'data': {
                    'id': user_1.id,
                    'type': 'users',
                }
            },
        }
    }


def test_user_schema_jsonapi_many_relationship(
        user_schema_cls, user_1, team_1, team_2, user_3,
):
    user_schema_cls = user_schema_cls.get_jsonapi_schema()
    serialized = user_schema_cls().dump(user_3)
    assert serialized == {
        'id': user_3.id,
        'type': 'users',
        'attributes': {
            'name': user_3.name,
            'email': user_3.email,
        },
        'relationships': {
            'referrer': {
                'data': {
                    'id': user_1.id,
                    'type': 'users',
                }
            },
            'teams': {
                'data': [
                    {
                        'id': team_1.id,
                        'type': 'teams',
                    },
                    {
                        'id': team_2.id,
                        'type': 'teams',
                    },
                ]
            }
        }
    }


def test_user_schema_dump_many(user_schema_cls, user_1, user_2):
    user_schema_cls = user_schema_cls.get_jsonapi_schema()
    serialized = user_schema_cls().dump([user_1, user_2], many=True)
    assert serialized == [
        {
            'id': user_1.id,
            'type': 'users',
            'attributes': {
                'name': user_1.name,
                'email': user_1.email,
            },
        },
        {
            'id': user_2.id,
            'type': 'users',
            'attributes': {
                'name': user_2.name,
                'email': user_2.email,
            },
            'relationships': {
                'referrer': {
                    'data': {
                        'id': user_1.id,
                        'type': 'users',
                    }
                },
            }
        },
    ]


def test_user_schema_only(user_schema_cls, user_1, user_2):
    user_schema_cls = user_schema_cls.get_jsonapi_schema()
    serialized = user_schema_cls(only=['name']).dump(user_2)
    assert serialized == {
        'id': user_2.id,  # type is required
        'type': 'users',  # id is required
        'attributes': {
            'name': user_2.name,
        },
    }

    serialized = user_schema_cls(only=['referrer']).dump(user_2)
    assert serialized == {
        'id': user_2.id,  # type is required
        'type': 'users',  # id is required
        'relationships': {
            'referrer': {
                'data': {
                    'id': user_1.id,
                    'type': 'users',
                }
            }
        }
    }
