import json
from json import JSONEncoder
from typing import Optional, Tuple, Type, Any, Dict, Iterable, TypeVar

from log import Log
from .searchable import SearchableSubclasses


class Attribute:
    class _DefaultNone:
        pass

    def __init__(self, description: Optional[str] = None, default=_DefaultNone()):
        self.name = None
        self.description = description
        self.default = default

    def __get__(self, instance: "AttributeStorage", owner: Type["AttributeStorage"]):
        if instance is None:
            return self

        value = instance._storage.get(self.name, self.default)
        assert not isinstance(value, self._DefaultNone)
        return value

    def __set__(self, instance: "AttributeStorage", value: "Any"):
        instance._storage[self.name] = value

    @property
    def is_required(self):
        return isinstance(self.default, Attribute._DefaultNone)


class KwargsAttribute(Attribute):
    pass


class MetaAttributeStorage(type):
    logger = Log("MetaAttributeStorage")
    def __new__(mcs, name: str, bases: Tuple[Type["AttributeStorage"]], attrs: Dict[str, Any]):
        __attributes__ = attrs.get("__attributes__", None)
        if __attributes__:
            raise NotImplementedError("Do not set __attributes__ manually")

        __kwargs_attribute__ = attrs.get("__kwargs_attributes__", None)
        if __kwargs_attribute__:
            raise NotImplementedError("Do not set __kwargs_attributes__ manually")

        __attributes__ = {}
        __kwargs_attribute__ = None
        __kwargs_attribute_class__ = None

        for base in bases:
            base: Type["AttributeStorage"]
            if hasattr(base, "__attributes__"):
                __attributes__.update(base.__attributes__)
            if hasattr(base, "__kwargs_attribute__"):
                if __kwargs_attribute__:
                    assert __kwargs_attribute__ is base.__kwargs_attribute__
                else:
                    __kwargs_attribute__ = base.__kwargs_attribute__
                    __kwargs_attribute_class__ = base.__name__

        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, KwargsAttribute):
                if __kwargs_attribute__:
                    raise NameError("Two KwargsAttribute: "
                                    f"{__kwargs_attribute__.name} from {__kwargs_attribute_class__} "
                                    f"and {attr_name} from {name}")
                else:
                    __kwargs_attribute_class__ = name
                    __kwargs_attribute__ = attr_value
            elif isinstance(attr_value, Attribute):
                __attributes__[attr_name] = attr_value

            if isinstance(attr_value, Attribute):
                attr_value.name = attr_name

        attrs['__attributes__'] = __attributes__
        attrs['__kwargs_attribute__'] = __kwargs_attribute__

        return super().__new__(mcs, name, bases, attrs)


class AttributeStorageEncoder(JSONEncoder):
    def default(self, o):
        print(o)
        if isinstance(o, AttributeStorage):
            return {
                "@class": o.__class__.__name__,
                **dict(o)
            }
        return super().default(o)


def _attribute_storage_hook(dct):
    if "@class" in dct:
        msg_class_name = dct['@class']
        AttributeStorageClass = AttributeStorage.search(msg_class_name)
        del dct['@class']
        return AttributeStorageClass(**dct)
    return dct


AS_T = TypeVar("AS_T", "AttributeStorage", "AttributeStorage")


class AttributeStorage(SearchableSubclasses, metaclass=MetaAttributeStorage):
    __attributes__: Dict[str, Attribute]
    __kwargs_attribute__: Optional[Attribute] = None

    def __init__(self, **kwargs):
        self._storage = {}

        for k, attr in self.__attributes__.items():
            if not isinstance(attr, KwargsAttribute) \
                    and (k not in kwargs):
                if attr.is_required:
                    raise TypeError(f"Missed argument: {k}; Set value or set default")
                else:
                    setattr(self, k, attr.default)

        for k, v in {**kwargs}.items():
            if k in self.__attributes__:
                setattr(self, k, v)
                del kwargs[k]

        if self.__class__.__kwargs_attribute__:
            setattr(self, self.__class__.__kwargs_attribute__.name, kwargs)
        else:
            if kwargs:
                raise TypeError(f"In class {self.__class__.__name__}, "
                                f"extra arguments: {','.join(kwargs.keys())}. "
                                f"Try one of: {self.__attributes__.keys()}")

    def __iter__(self) -> Iterable[Tuple[str, Any]]:
        data = self._storage
        if self.__class__.__kwargs_attribute__:
            data = {**data}
            kwargs = data[self.__class__.__kwargs_attribute__.name]
            del data[self.__class__.__kwargs_attribute__.name]
            data.update(kwargs)

        yield from data.items()

    def serialize(self) -> str:
        return json.dumps(self, cls=AttributeStorageEncoder)

    @classmethod
    def deserialize(cls: Type[AS_T], data: str, force=False) -> AS_T:
        obj = json.loads(data, object_hook=_attribute_storage_hook)
        if (type(obj) is not cls) and not force:
            raise TypeError(f"Deserialized object must be {cls.__name__} type "
                            f"instead {type(obj).__name__}")
        return obj

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False

        return self._storage == other._storage

    def __repr__(self) -> str:
        attrs = "; ".join(
            f"{k}={getattr(self, k, None)}" for k in self.__attributes__
        )
        additional_repr = self._additional_repr()
        if additional_repr:
            additional_repr = f"{additional_repr} "

        return f"<{self.__class__.__name__}: {additional_repr}{attrs}>"

    def _additional_repr(self) -> str:
        return ""

