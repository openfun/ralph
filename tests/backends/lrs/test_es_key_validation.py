"""Tests for Elasticsearch-compatible dict key validation."""

import pytest

from ralph.backends.lrs.es_key_validation import (
    ElasticsearchKeyValidationError,
    find_invalid_elasticsearch_keys,
    validate_elasticsearch_keys,
)


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"actor": {"mbox": "mailto:a@b.com"}}, []),
        (
            {"context": {"extensions": {"http://example.com/ext": {"": 1}}}},
            ["elasticsearch-incompatible key: empty string at context.extensions.http://example.com/ext"],
        ),
        (
            {
                "context": {
                    "extensions": {
                        "http://id.tincanapi.com/extension/quiz": {"match": "a"},
                    }
                }
            },
            [],
        ),
        (
            {"context": {"extensions": {"http://example.com/ext": {"nested.key": 1}}}},
            ["elasticsearch-incompatible key: '.' in 'context.extensions.http://example.com/ext.nested.key'"],
        ),
        (
            {
                "result": {
                    "extensions": {
                        "http://example.com/quiz": {"": "bad", "ok.key": 2},
                    }
                }
            },
            [
                "elasticsearch-incompatible key: empty string at result.extensions.http://example.com/quiz",
                "elasticsearch-incompatible key: '.' in 'result.extensions.http://example.com/quiz.ok.key'",
            ],
        ),
    ],
)
def test_find_invalid_elasticsearch_keys(payload, expected):
    assert find_invalid_elasticsearch_keys(payload) == expected


def test_validate_elasticsearch_keys_raises():
    with pytest.raises(
        ElasticsearchKeyValidationError,
        match="empty string at context.extensions",
    ):
        validate_elasticsearch_keys(
            {"context": {"extensions": {"http://example.com/ext": {"": 1}}}}
        )
