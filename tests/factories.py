"""Mock model generation for testing."""

from decimal import Decimal
from typing import Any, Callable

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
from ralph.models.xapi.base.common import IRI, LanguageTag
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
    VirtualClassroomPostedPublicMessageContextActivities,
    VirtualClassroomProfileActivity,
    VirtualClassroomStartedPollContextActivities,
)


def prune(d: Any, exceptions: list = []):
    """Remove all empty leaves from a dict, except fo those in `exceptions`."""
    # TODO: add test ?

    if isinstance(d, BaseModel):
        d = d.dict()
    if isinstance(d, dict):
        d_dict_not_exceptions = {
            k: prune(v) for k, v in d.items() if k not in exceptions
        }
        d_dict_not_exceptions = {k: v for k, v in d.items() if v}
        d_dict_exceptions = {k: v for k, v in d.items() if k in exceptions}
        return d_dict_not_exceptions | d_dict_exceptions
    elif isinstance(d, list):
        d_list = [prune(v) for v in d]
        return [v for v in d_list if v]
    if d not in [[], {}, ""]:
        return d
    return False


class ModelFactory(PolyfactoryModelFactory[T]):
    __allow_none_optionals__ = False
    __is_base_factory__ = True
    __random_seed__ = 6  # TODO: remove this

    @classmethod
    def get_provider_map(cls) -> dict[Any, Callable[[], Any]]:
        provider_map = super().get_provider_map()
        provider_map[LanguageTag] = lambda: LanguageTag("en-US")
        provider_map[IRI] = lambda: IRI("https://w3id.org/xapi/video/verbs/played")
        return provider_map

    @classmethod
    def _get_or_create_factory(cls, model: type):
        # print("Cls:", model)
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


# TODO: put back ?
# class BaseXapiActivityInteractionDefinitionFactory(
#     ModelFactory[BaseXapiActivityInteractionDefinition]
# ):
#     __set_as_default_factory_for_type__ = True
#     __model__ = BaseXapiActivityInteractionDefinition

#     correctResponsesPattern = None


def myfunc():
    raise Exception("WHAT ARE YOU EVEN DOING")


# TODO: put back ?
# class BaseXapiContextContextActivitiesFactory(
#     ModelFactory[BaseXapiContextContextActivities]
# ):
#     __model__ = BaseXapiContextContextActivities

#     category = myfunc


class BaseXapiContextFactory(ModelFactory[BaseXapiContext]):
    __model__ = BaseXapiContext
    __set_as_default_factory_for_type__ = True

    revision = Ignore()
    platform = Ignore()

    # TODO: see why this was added
    # contextActivities = (
    #     lambda: BaseXapiContextContextActivitiesFactory.build() or Ignore()
    # )


class LMSContextContextActivitiesFactory(ModelFactory[LMSContextContextActivities]):
    __model__ = LMSContextContextActivities
    __set_as_default_factory_for_type__ = True

    category = lambda: mock_xapi_instance(LMSProfileActivity)  # TODO: Uncomment


class VideoContextContextActivitiesFactory(ModelFactory[VideoContextContextActivities]):
    __model__ = VideoContextContextActivities
    __set_as_default_factory_for_type__ = True

    category = lambda: mock_xapi_instance(VideoProfileActivity)


class VirtualClassroomStartedPollContextActivitiesFactory(
    ModelFactory[VirtualClassroomStartedPollContextActivities]
):
    __model__ = VirtualClassroomStartedPollContextActivities
    __set_as_default_factory_for_type__ = True

    category = lambda: mock_xapi_instance(VirtualClassroomProfileActivity)


class VirtualClassroomAnsweredPollContextActivitiesFactory(
    ModelFactory[VirtualClassroomAnsweredPollContextActivities]
):
    __model__ = VirtualClassroomAnsweredPollContextActivities
    __set_as_default_factory_for_type__ = True

    category = lambda: mock_xapi_instance(VirtualClassroomProfileActivity)


class VirtualClassroomPostedPublicMessageContextActivitiesFactory(
    ModelFactory[VirtualClassroomPostedPublicMessageContextActivities]
):
    __model__ = VirtualClassroomPostedPublicMessageContextActivities
    __set_as_default_factory_for_type__ = True

    category = lambda: mock_xapi_instance(VirtualClassroomProfileActivity)


# class VirtualClassroomAnsweredPollFactory(ModelFactory[VirtualClassroomAnsweredPollContextActivities]):
#     __model__ = VirtualClassroomAnsweredPollContextActivities

#     category = lambda: mock_xapi_instance(VirtualClassroomProfileActivity)
#     parent = lambda: mock_xapi_instance(VirtualClassroomActivity) # TODO: Remove this. Check that this is valid


class UISeqPrev(ModelFactory[UISeqPrev]):
    __model__ = UISeqPrev
    __set_as_default_factory_for_type__ = True

    event = lambda: mock_instance(NavigationalEventField, old=1, new=0)


class UISeqNext(ModelFactory[UISeqNext]):
    __model__ = UISeqNext
    __set_as_default_factory_for_type__ = True

    event = lambda: mock_instance(NavigationalEventField, old=0, new=1)


def mock_xapi_instance(klass, *args, **kwargs):
    """Generate a mock instance of a given class (`klass`)."""

    # Avoid redifining custom factories
    if klass not in BaseFactory._factory_type_mapping:

        class KlassFactory(ModelFactory[klass]):
            __model__ = klass

    else:
        KlassFactory = BaseFactory._factory_type_mapping[klass]

    kwargs = KlassFactory.process_kwargs(*args, **kwargs)

    kwargs = prune(kwargs, exceptions=["extensions"])

    return klass(**kwargs)


def mock_instance(klass, *args, **kwargs):
    """Generate a mock instance of a given class (`klass`)."""

    # Avoid redifining custom factories
    if klass not in BaseFactory._factory_type_mapping:

        class KlassFactory(ModelFactory[klass]):
            __model__ = klass

    else:
        KlassFactory = BaseFactory._factory_type_mapping[klass]

    kwargs = KlassFactory.process_kwargs(*args, **kwargs)

    return klass(**kwargs)


def mock_url():
    return ModelFactory.__faker__.url()
