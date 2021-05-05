"""Tests for the xAPI object fields"""

import json

from ralph.models.xapi.fields.object import PageObjectField


def test_models_xapi_fields_object_page_object_field():
    """Tests that the PageObjectField returns the expected dictionary."""

    id_ = "https://fun-mooc.fr/"
    assert json.loads(PageObjectField(id=id_).json()) == {
        "id": id_,
        "definition": {
            "type": "http://activitystrea.ms/schema/1.0/page",
            "name": {"en": "page"},
        },
    }
