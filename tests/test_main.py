def test_team_schema_jsonapi_simple(team_schema_cls, team_1):
    team_schema_cls = team_schema_cls.get_jsonapi_resource_object_schema()
    serialized = team_schema_cls().dump(team_1)
    assert serialized == {
        'id': team_1.id,
        'type': 'teams',
        'attributes': {
            'name': team_1.name,
        },
    }


def test_user_schema_jsonapi_empty_relationships(user_schema_cls, user_1):
    user_schema_cls = user_schema_cls.get_jsonapi_resource_object_schema()
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
    user_schema_cls = user_schema_cls.get_jsonapi_resource_object_schema()
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
    user_schema_cls = user_schema_cls.get_jsonapi_resource_object_schema()
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
    user_schema_cls = user_schema_cls.get_jsonapi_resource_object_schema()
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
    user_schema_cls = user_schema_cls.get_jsonapi_resource_object_schema()
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


def test_top_level_schema(user_schema_cls, user_1):
    top_level_schema = user_schema_cls.get_jsonapi_top_level_schema()
    serialized = top_level_schema().dump(user_1)
    assert serialized == {
        'data': {
            'id': user_1.id,
            'type': 'users',
            'attributes': {
                'name': user_1.name,
                'email': user_1.email,
            },
        },
    }


def test_top_level_schema_many(user_schema_cls, user_1, user_2):
    top_level_schema = user_schema_cls.get_jsonapi_top_level_schema(many=True)
    serialized = top_level_schema().dump([user_1, user_2])
    assert serialized == {
        'data': [
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
                            'type': 'users'
                        }
                    }
                }
            },
        ]
    }


def test_top_level_schema_errors(user_schema_cls):
    top_level_schema = user_schema_cls.get_jsonapi_top_level_schema()
    top_level_schema_many = user_schema_cls.get_jsonapi_top_level_schema(many=True)

    class TestHttpException(Exception):
        def __init__(
                self, id: str = None, links: dict = None, status: str = None,
                code: str = None, title: str = None, detail: str = None,
                source: dict = None, meta: dict = None,
        ):
            self.id = id
            self.links = links
            self.status = status
            self.code = code
            self.title = title
            self.detail = detail
            self.source = source
            self.meta = meta

    exc = TestHttpException(id='exc-id-test', status='404', code='1234', detail='something went wrong')

    serialized = top_level_schema().dump(exc)
    serialized_many = top_level_schema_many().dump(exc)
    assert serialized == serialized_many == {
        'errors': [
            {
                'id': 'exc-id-test',
                'status': '404',
                'code': '1234',
                'detail': 'something went wrong',
            },
        ]
    }


def test_top_level_schema_jsonapi_info(user_schema_cls, user_1):
    top_level_schema = user_schema_cls.get_jsonapi_top_level_schema()
    serialized = top_level_schema(context={'jsonapi_info': {'version': '1.0'}}).dump(user_1)
    assert serialized == {
        'jsonapi': {
            'version': '1.0',
        },
        'data': {
            'id': user_1.id,
            'type': 'users',
            'attributes': {
                'name': user_1.name,
                'email': user_1.email,
            },
        },
    }


def test_top_level_schema_only(user_schema_cls, user_1, user_2):
    top_level_schema = user_schema_cls.get_jsonapi_top_level_schema()
    serialized = top_level_schema(only=['name']).dump(user_2)
    assert serialized == {
        'data': {
            'id': user_2.id,  # type is required
            'type': 'users',  # id is required
            'attributes': {
                'name': user_2.name,
            },
        },
    }

    serialized = top_level_schema(only=['referrer']).dump(user_2)
    assert serialized == {
        'data': {
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
        },
    }


def test_top_level_schema_meta(user_schema_cls, user_1):
    top_level_schema = user_schema_cls.get_jsonapi_top_level_schema()
    serialized = top_level_schema(context={'top_level_meta': {'custom_field': 'custom_value'}}).dump(user_1)
    assert serialized == {
        'meta': {
            'custom_field': 'custom_value',
        },
        'data': {
            'id': user_1.id,
            'type': 'users',
            'attributes': {
                'name': user_1.name,
                'email': user_1.email,
            },
        },
    }


def test_top_level_schema_only_maintains_other_top_level_fields(user_schema_cls, user_2):
    top_level_schema = user_schema_cls.get_jsonapi_top_level_schema()
    serialized = top_level_schema(only=['name'], context={'jsonapi_info': {'version': '1.0'}}).dump(user_2)
    assert serialized == {
        'jsonapi': {
            'version': '1.0',
        },
        'data': {
            'id': user_2.id,
            'type': 'users',
            'attributes': {
                'name': user_2.name,
            },
        },
    }


def test_load_top_level_schema(user_schema_cls, user_1, user_2):
    top_level_schema = user_schema_cls.get_jsonapi_top_level_schema()
    deserialized = top_level_schema().load(
        {
            'data': {
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
                    }
                }
            }
        }
    )
    assert deserialized == {
        'id': user_2.id,
        'name': user_2.name,
        'email': user_2.email,
        'referrer': user_1.id,
    }


def test_top_level_included(user_schema_cls, user_1, user_2):
    top_level_schema = user_schema_cls.get_jsonapi_top_level_schema()
    tls = top_level_schema(context={'to_include': {'referrer'}})
    serialized = tls.dump(user_2)
    assert serialized == {
        'data': {
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
                }
            },
        },
        'included': [
            {
                'id': user_1.id,
                'type': 'users',
                'attributes': {
                    'name': user_1.name,
                    'email': user_1.email,
                },
            }
        ],
    }


def test_top_level_included_deduplication(user_schema_cls, team_1, team_2, user_1, user_2, user_3):
    top_level_schema = user_schema_cls.get_jsonapi_top_level_schema(many=True)
    tls = top_level_schema(context={'to_include': {'referrer'}})
    serialized = tls.dump([user_2, user_3])
    assert serialized == {
        'data': [
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
                    }
                },
            },
            {
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
                },
            },
        ],
        'included': [
            {
                'id': user_1.id,
                'type': 'users',
                'attributes': {
                    'name': user_1.name,
                    'email': user_1.email,
                },
            }
        ],
    }
