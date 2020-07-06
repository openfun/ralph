"""Mixins for event factories"""

import json


class JSONFactoryMixin:
    """Overwrites Factory._create() to produce JSON serialized models"""

    @classmethod
    def _create(cls, model_class, *args, **kwargs):  # pylint: disable=unused-argument
        """Override the default ``_create`` with our custom call."""
        schema = model_class()
        kwargs_json = json.dumps(kwargs)
        event = schema.loads(kwargs_json)
        return schema.dumps(event)


class ObjFactoryMixin:
    """Overwrites Factory._create() to produce deserialized models"""

    @classmethod
    def _create(cls, model_class, *args, **kwargs):  # pylint: disable=unused-argument
        """Override the default ``_create`` with our custom call."""
        schema = model_class()
        kwargs_json = json.dumps(kwargs)
        event = schema.loads(kwargs_json)
        return schema.dump(event)
