string_or_integer = {"oneof": [{"type": "string"}, {"type": "integer"}]}
string_or_integer_required = {
    "required": True,
    "oneof": [
        {"type": "string"},
        {"type": "integer"},
    ],
}

schema = {
    "connection": {
        "type": "dict",
        "required": True,
        "schema": {
            "url": {"type": "string", "required": True},
            "project_id": {"type": "integer", "required": True},
            "private_token": {
                "required": True,
                "anyof": [
                    {"type": "string"},
                    {
                        "type": "dict",
                        "schema": {"env": {"type": "string", "required": True}},
                    },
                ],
            },
            "api_version": {"type": "string"},
            "timeout": {"type": "integer"},
            "ssl_verify": {"type": "boolean"},
        },
    },
    "labels": {
        "type": "dict",
        "required": True,
        "schema": {
            "to_do": string_or_integer_required,
            "in_progress": string_or_integer_required,
            "in_review": string_or_integer_required,
            "merged": string_or_integer_required,
            "backend": string_or_integer,
            "frontend": string_or_integer,
            "bug": string_or_integer,
        },
    },
}
