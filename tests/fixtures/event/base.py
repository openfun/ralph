"""
Base class definitions for the event fixture
"""
from faker import Faker

# Faker.seed(0)
FAKE = Faker()


class BaseEventField:
    """BaseEventField Interface.
    The Event Field is just a wrapper around it's value which is obtained
    by calling it's generator function.
    """

    def __init__(
        self,
        generator,
        removed=False,
        optional=False,
        dependency=None,
        **generator_kwargs
    ):
        """BaseEventField Constuctor

        Args:
            generator (function): A function returning the value of the
                EventField. The function will be called with the
                generator_kwargs keyword arguments
            removed (boolean): Defines if the Field will be removed
                from the Event
            optional (boolean): Defines if the Field might be removed
                from the Event at random
            dependency (list or string): A list of lists containing strings or
                a single list of strings or just a string. Each
                list defines a path to a Field from the root of the Event,
                which value is required in order to compute this Event
                value. For example, if the Event is:
                    Event = {
                        "key1": {
                            "key2": "value2",
                            "key3": "value3",
                            "key4": {
                                "key5": "value5",
                                "key6": "value6"
                            }
                        },
                        "key7": "value7"
                    }
                and the dependency argument is:
                    dependency = [["key1", "key3"], ["key1", "key4"]]
                this would mean that the Event["key1"]["key3"] Field and
                the Event["key1"]["key4"] Object should be computed prior to
                this event.
                In case the EventField depends on only one other EventFiled
                we can use just a list of strings. For example:
                     dependency = ["key1", "key3"]
                (this is equivalent to: dependency = [["key1", "key3"]])
                In case the EventField depends on only one other EventField
                and the EventField is at the root of the Event
                we can use just a string. For example:
                    dependency = "key1"
                (this is equivalent to: dependency = [["key1"]])
            generator_kwargs (kwargs): The generator_kwargs will be
                passed to the `generator` function as kwargs
        """
        self.generator = generator
        self.removed = removed
        self.optional = optional
        self.dependency = dependency
        self.generator_kwargs = generator_kwargs
        if dependency is not None:
            if isinstance(self.dependency, str):
                self.dependency = [[dependency]]
            if isinstance(self.dependency[0], str):
                self.dependency = [dependency]

    def __add__(self, other):
        """Delegates the addition opreration to the EventField value
        Args:
            other (any object): any object supporting
                `this_field_value` + other
        """
        raise NotImplementedError

    def __radd__(self, other):
        """see self.__add__"""
        raise NotImplementedError

    def __getitem__(self, key):
        """Delegates the [] opreration to the EventField value
        Args:
            key (string or slice): any string or slice supporting
                `this_field_value`[key]
        """
        raise NotImplementedError


class EventFieldProperties:
    """A data class holding the properies needed for the FreeEventField"""

    def __init__(self, nullable=False, emptiable_str=False, emptiable_dict=False):
        """EventFieldProperties Constuctor

        Args:
            nullable (boolean):  Defines if the Field might be None
            emptiable_str (boolean): Defines if the Field might be an
                empty string
            emptiable_dict (boolean): Defines if the Field might be an
                empty dictionary
        """
        self.nullable = nullable
        self.emptiable_str = emptiable_str
        self.emptiable_dict = emptiable_dict

    def get_true_properties(self):
        """Returns an array of property names which are set to True"""
        properties = []
        for option in self.__dict__:
            if self.__dict__[option]:
                properties.append(option)
        return properties


class FreeEventField(BaseEventField):
    """Concrete class of BaseEventField.
    The FreeEventField does not depend on other EventFields.
    """

    def __init__(
        self,
        generator,
        removed=False,
        optional=False,
        properties=EventFieldProperties(),
        **generator_kwargs
    ):
        """FreeEventField Constuctor

        Args:
            properties (EventFieldProperties): Data object containing
                properties for this EventField which alter it's behaviour
        """
        super(FreeEventField, self).__init__(
            generator, removed=removed, optional=optional, **generator_kwargs
        )
        self.properties = properties

    def get(self, *EVENT_ARGS):
        """Returns the Event value based on the EVENT_ARGS

        Args:
            *EVENT_ARGS (strings): one or more of the strings defined
                in the EVENT_ARGS dictionary. They behave like global
                arguments, changing the behaviour of all the Event Fields
                in an Event. Initially the root Event instance recieves
                the *EVENT_ARGS which it passes to its child instances
                and EventFields.
        """
        properties = self.properties.get_true_properties()
        if "set_all_filled" in EVENT_ARGS or len(properties) == 0:
            return self.generator(**self.generator_kwargs)
        set_all_null = "set_all_null" in EVENT_ARGS
        if FAKE.boolean() or set_all_null:
            choice = FAKE.random_element(properties)
            if choice == "nullable" or (set_all_null and "nullable" in properties):
                return None
            if choice == "emptiable_str" or (
                set_all_null and "emptiable_str" in properties
            ):
                return ""
            if choice == "emptiable_dict" or (
                set_all_null and "emptiable_dict" in properties
            ):
                return {}
        return self.generator(**self.generator_kwargs)

    def __add__(self, other):
        """Delegates the addition opreration to the EventField value
        Args:
            other (any object): any object supporting
                `this_field_value` + other
        """

        def wrap(**kwargs):
            return self.generator(**kwargs) + other

        return FreeEventField(
            wrap,
            removed=self.removed,
            optional=self.optional,
            dependency=self.dependency,
            properties=self.properties,
            **self.generator_kwargs
        )

    def __radd__(self, other):
        """see self.__add__"""

        def wrap(*args, **kwargs):
            return other + self.generator(*args, **kwargs)

        return FreeEventField(
            wrap,
            removed=self.removed,
            optional=self.optional,
            dependency=self.dependency,
            properties=self.properties,
            **self.generator_kwargs
        )

    def __getitem__(self, key):
        """Delegates the [] opreration to the EventField value
        Args:
            key (string or slice): any string or slice supporting
                `this_field_value`[key]
        """

        def wrap(*args, **kwargs):
            return self.generator(*args, **kwargs)[key]

        return FreeEventField(
            wrap,
            removed=self.removed,
            optional=self.optional,
            dependency=self.dependency,
            properties=self.properties,
            **self.generator_kwargs
        )


class TiedEventField(BaseEventField):
    """Concrete class of BaseEventField.
    The TiedEventField depends on other EventFields.
    """

    def __init__(
        self,
        generator,
        removed=False,
        optional=False,
        dependency=None,
        **generator_kwargs
    ):
        """TiedEventField constructor

        Args:
            generator (function): A function returning the value of the
                EventField. The function will be called with positional
                arguments corresponding to the values of the other Fields
                this EventField depends on
        """
        super(TiedEventField, self).__init__(
            generator,
            removed=removed,
            optional=optional,
            dependency=dependency,
            **generator_kwargs
        )

    def get(self, partial_event=None):
        """Returns the EventField value
        This method will not be called if `removed` is true
        This method is called during the constuction of the Event, at the
        point where all Fields this EventField depends on are created.
        Here we extract the values of the depending fields and passing
        them to the generator function to compute this EventField value

        Args:
            parital_event (dictionary): it contains the
                not-fully-constructed Event dictionary containing the
                Fields this EventField depends on.
        Returns:
            The output depends on what the passed generator function will
            return. The generator might return a string, integer, list,
            dictionnary or a BaseEventField. If the return value is a
            BaseEventField - this EventField will be removed. Else the
            returned value becomes the final EventField value.

        """
        if partial_event is None or self.dependency is None:
            return self.generator(**self.generator_kwargs)

        generator_args = []
        for key_list in self.dependency:
            temp = partial_event
            if isinstance(key_list, list):
                for key in key_list:
                    temp = temp[key]
            else:
                temp = temp[key_list]
            generator_args.append(temp)
        return self.generator(*generator_args, **self.generator_kwargs)

    def __add__(self, other):
        """Delegates the addition opreration to the EventField value
        Args:
            other (any object): any object supporting
                `this_field_value` + other
        """

        def wrap(*args, **kwargs):
            return self.generator(*args, **kwargs) + other

        return TiedEventField(
            wrap,
            removed=self.removed,
            optional=self.optional,
            dependency=self.dependency,
            **self.generator_kwargs
        )

    def __radd__(self, other):
        """see self.__add__"""

        def wrap(*args, **kwargs):
            return other + self.generator(*args, **kwargs)

        return TiedEventField(
            wrap,
            removed=self.removed,
            optional=self.optional,
            dependency=self.dependency,
            **self.generator_kwargs
        )

    def __getitem__(self, key):
        """Delegates the [] opreration to the EventField value
        Args:
            key (string or slice): any string or slice supporting
                `this_field_value`[key]
        """

        def wrap(*args, **kwargs):
            return self.generator(*args, **kwargs)[key]

        return TiedEventField(
            wrap,
            removed=self.removed,
            optional=self.optional,
            dependency=self.dependency,
            **self.generator_kwargs
        )


class BaseEvent:
    """Base class for all Event types.
    Contains common function definitions and unrelated event fields
    """

    def __init__(self, *args, removed=False, optional=False, **kwargs):
        self.exclude = ["exclude", "args", "kwargs", "optional", "removed"]
        self.args = args
        self.kwargs = kwargs
        self.removed = removed
        self.optional = optional

    def get(self):
        """Returns the Event as a json"""
        dependencies = []
        self.list_dependencies(self, dependencies)
        dependencies = self.get_task_batches(dependencies)
        result = {}
        for batch in dependencies:
            for field in batch:
                path = field[0].split("|")
                value = field[1]
                parent = field[2]
                if path[-1] in parent.kwargs:
                    value = parent.kwargs[path[-1]]
                    parent.__dict__[path[-1]] = value
                if self.is_removed(parent, parent):
                    continue
                if not isinstance(value, BaseEventField):
                    self.set_nested_key(result, path, value)
                    continue
                if self.is_removed(value, parent):
                    continue
                if isinstance(value, FreeEventField):
                    self.set_nested_key(result, path, value.get(*self.args))
                    continue
                # value == TiedEventField
                computed_value = value.get(partial_event=result)
                if isinstance(computed_value, BaseEventField):
                    continue
                self.set_nested_key(result, path, computed_value)
        return result

    @staticmethod
    def is_removed(child, parent):
        """Check if the child element has to be removed"""
        return (
            child.removed or (child.optional and "remove_optional" in parent.args)
        ) or ("keep_optional" not in parent.args and child.optional and FAKE.boolean())

    @staticmethod
    def list_dependencies(parent, dependencies, path=None):
        """Returns the list of all fields with their depedencies"""
        if path is None:
            path = []
        filtered_keys = [x for x in parent.__dict__ if x not in parent.exclude]
        if len(path) > 0:
            all_keys = set("|".join(path + [key]) for key in filtered_keys)
            dependencies.append(("|".join(path), all_keys, None, None))
        for key in filtered_keys:
            temp = "|".join(path + [key])
            value = parent.__dict__[key]
            if isinstance(value, TiedEventField):
                temp_value = set()
                if value.dependency is not None:
                    for deps in list(value.dependency):
                        temp_value.add("|".join(deps))
                dependencies.append((temp, temp_value, value, parent))
            elif isinstance(value, BaseEvent):
                path.append(key)
                BaseEvent.list_dependencies(value, dependencies, path)
                path.pop()
            else:
                dependencies.append((temp, set(), value, parent))

    @staticmethod
    def format_circular_dependencies_error(name_to_deps):
        """Formats the error message of an circular depencency error"""
        msg = []
        for name, deps in name_to_deps.items():
            for parent in deps:
                msg.append("%s -> %s" % (name, parent))
        return "\n".join(msg)

    @staticmethod
    def get_task_batches(dependencies):
        """Resolves the dependency graph"""
        name_to_instance = dict((n[0], [n[0], n[2], n[3]]) for n in dependencies)
        name_to_deps = dict((n[0], n[1]) for n in dependencies)
        batches = []
        while name_to_deps:
            ready = {name for name, deps in name_to_deps.items() if not deps}
            if not ready:
                msg = "Circular dependencies found!\n"
                msg += BaseEvent.format_circular_dependencies_error(name_to_deps)
                raise ValueError(msg)
            for name in ready:
                del name_to_deps[name]
            for deps in name_to_deps.values():
                deps.difference_update(ready)
            # batches.append([(name_to_instance[name][0:3:2]) for name in ready])
            for name in ready:
                if name_to_instance[name][-1] is not None:
                    batches.append([(name_to_instance[name])])
        return batches

    @staticmethod
    def set_nested_key(dic, path, value):
        """Returns a new dict including the value at the path"""
        if dic is None:
            dic = {}
        temp = dic
        for key in path[:-1]:
            if key in temp:
                temp = temp[key]
            else:
                temp = temp.setdefault(key, {})
        temp[path[-1]] = value
