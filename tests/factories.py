"""Mock model generation for testing."""

from decimal import Decimal
from typing import Any, Callable, Dict, Optional

from polyfactory.factories.base import BaseFactory
from polyfactory.factories.pydantic_factory import (
    ModelFactory as PolyfactoryModelFactory,
)
from polyfactory.factories.pydantic_factory import (
    T,
)
from polyfactory.fields import Ignore
from pydantic import BaseModel

from ralph.models.edx.navigational.fields.events import NavigationalEventField
from ralph.models.edx.navigational.statements import UISeqNext, UISeqPrev
from ralph.models.xapi.base.common import IRI, LanguageTag, MailtoEmail
from ralph.models.xapi.base.contexts import (
    BaseXapiContext,
)
from ralph.models.xapi.base.results import BaseXapiResultScore
from ralph.models.xapi.lms.contexts import (
    LMSContextContextActivities,
    LMSProfileActivity,
)
from ralph.models.xapi.video.contexts import (
    VideoContextContextActivities,
    VideoProfileActivity,
)
from ralph.models.xapi.virtual_classroom.contexts import (
    VirtualClassroomAnsweredPollContextActivities,
    VirtualClassroomContextContextActivities,
    VirtualClassroomPostedPublicMessageContextActivities,
    VirtualClassroomProfileActivity,
    VirtualClassroomStartedPollContextActivities,
)


def prune(d: Any, exemptions: Optional[list] = None):
    """Remove all empty leaves from a dict, except fo those in `exemptions`."""

    if exemptions is None:
        exemptions = []

    if isinstance(d, BaseModel):
        d = d.model_dump()
    if isinstance(d, dict):
        d_dict_not_exemptions = {
            k: prune(v) for k, v in d.items() if k not in exemptions
        }
        d_dict_not_exemptions = {k: v for k, v in d.items() if v}
        d_dict_exemptions = {k: v for k, v in d.items() if k in exemptions}
        return {**d_dict_not_exemptions, **d_dict_exemptions}
    elif isinstance(d, list):
        d_list = [prune(v) for v in d]
        return [v for v in d_list if v]
    if d:
        return d
    return False


class ModelFactory(PolyfactoryModelFactory[T]):
    __allow_none_optionals__ = False
    __is_base_factory__ = True

    @classmethod
    def get_provider_map(cls) -> Dict[Any, Callable[[], Any]]:
        provider_map = super().get_provider_map()
        return provider_map

    @classmethod
    def _get_or_create_factory(cls, model: type):
        created_factory = super()._get_or_create_factory(model)
        created_factory.get_provider_map = cls.get_provider_map
        created_factory._get_or_create_factory = cls._get_or_create_factory
        return created_factory


class BaseXapiResultScoreFactory(ModelFactory[BaseXapiResultScore]):
    __set_as_default_factory_for_type__ = True
    __model__ = BaseXapiResultScore

    min = Decimal("0.0")
    max = Decimal("20.0")
    raw = Decimal("11")


class BaseXapiContextFactory(ModelFactory[BaseXapiContext]):
    __model__ = BaseXapiContext
    __set_as_default_factory_for_type__ = True

    revision = Ignore()
    platform = Ignore()


class LMSContextContextActivitiesFactory(ModelFactory[LMSContextContextActivities]):
    __model__ = LMSContextContextActivities
    __set_as_default_factory_for_type__ = True

    category = lambda: mock_xapi_instance(LMSProfileActivity)  # noqa: E731


class VideoContextContextActivitiesFactory(ModelFactory[VideoContextContextActivities]):
    __model__ = VideoContextContextActivities
    __set_as_default_factory_for_type__ = True

    category = lambda: mock_xapi_instance(VideoProfileActivity)  # noqa: E731


class VirtualClassroomStartedPollContextActivitiesFactory(
    ModelFactory[VirtualClassroomStartedPollContextActivities]
):
    __model__ = VirtualClassroomStartedPollContextActivities
    __set_as_default_factory_for_type__ = True

    category = lambda: mock_xapi_instance(VirtualClassroomProfileActivity)  # noqa: E731


class VirtualClassroomAnsweredPollContextActivitiesFactory(
    ModelFactory[VirtualClassroomAnsweredPollContextActivities]
):
    __model__ = VirtualClassroomAnsweredPollContextActivities
    __set_as_default_factory_for_type__ = True

    category = lambda: mock_xapi_instance(VirtualClassroomProfileActivity)  # noqa: E731


class VirtualClassroomPostedPublicMessageContextActivitiesFactory(
    ModelFactory[VirtualClassroomPostedPublicMessageContextActivities]
):
    __model__ = VirtualClassroomPostedPublicMessageContextActivities
    __set_as_default_factory_for_type__ = True

    category = lambda: mock_xapi_instance(VirtualClassroomProfileActivity)  # noqa: E731


class UISeqPrevFactory(ModelFactory[UISeqPrev]):
    __model__ = UISeqPrev
    __set_as_default_factory_for_type__ = True

    event = lambda: mock_instance(NavigationalEventField, old=1, new=0)  # noqa: E731


class UISeqNextFactory(ModelFactory[UISeqNext]):
    __model__ = UISeqNext
    __set_as_default_factory_for_type__ = True

    event = lambda: mock_instance(NavigationalEventField, old=0, new=1)  # noqa: E731


class VirtualClassroomContextContextActivitiesFactory(
    ModelFactory[VirtualClassroomContextContextActivities]
):
    __model__ = VirtualClassroomContextContextActivities
    __set_as_default_factory_for_type__ = True

    category = lambda: mock_instance(VirtualClassroomProfileActivity)  # noqa: E731


class LanguageTagFactory(ModelFactory[LanguageTag]):
    __model__ = LanguageTag
    __set_as_default_factory_for_type__ = True

    root = lambda: LanguageTag("en-US")  # noqa: E731


class IRIFactory(ModelFactory[IRI]):
    __model__ = IRI
    __set_as_default_factory_for_type__ = True

    root = lambda: IRI(mock_url())  # noqa: E731


class MailtoEmailFactory(ModelFactory[MailtoEmail]):
    __model__ = MailtoEmail
    __set_as_default_factory_for_type__ = True

    root = lambda: "mailto:test@example.com"  # noqa: E731


def mock_xapi_instance(klass, *args, **kwargs):
    """Generate a mock instance of a given xAPI model."""

    # Avoid redifining custom factories
    if klass not in BaseFactory._factory_type_mapping:

        class KlassFactory(ModelFactory[klass]):
            __model__ = klass

    else:
        KlassFactory = BaseFactory._factory_type_mapping[klass]

    kwargs = KlassFactory.process_kwargs(*args, **kwargs)

    # Remove `None` values
    kwargs = prune(kwargs, exemptions=["extensions"])

    return klass(**kwargs)


def mock_instance(klass, *args, **kwargs):
    """Generate a mock instance of a given model."""

    # Avoid redifining custom factories
    if klass not in BaseFactory._factory_type_mapping:

        class KlassFactory(ModelFactory[klass]):
            __model__ = klass

    else:
        KlassFactory = BaseFactory._factory_type_mapping[klass]

    return KlassFactory.build(*args, **kwargs)


def mock_url():
    """Mock a URL."""
    return ModelFactory.__faker__.url()
