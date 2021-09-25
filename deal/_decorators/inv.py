from functools import partial, update_wrapper
from types import MethodType
from typing import Callable, TypeVar

from .._exceptions import InvContractError
from .._types import ExceptionType
from .base import Base


T = TypeVar('T', bound=type)


class InvariantedClass:
    _validate_base: Callable[..., None]

    def _validate(self) -> None:
        """
        Step 5 (1st flow) or Step 4 (2nd flow). Process contract for object.
        """
        # validation by Invariant.validate
        self._validate_base(self)

    def _patched_method(self, method: Callable, *args, **kwargs):
        """
        Step 4 (1st flow). Call method
        """
        self._validate()
        result = method(*args, **kwargs)
        self._validate()
        return result

    def __getattribute__(self, name: str):
        """
        Step 3 (1st flow). Get method
        """
        attr = super().__getattribute__(name)
        # disable patching for InvariantedClass methods
        if name in ('_patched_method', '_validate', '_validate_base'):
            return attr
        # disable patching for attributes (not methods)
        if not isinstance(attr, MethodType):
            return attr
        # patch
        patched_method = partial(self._patched_method, attr)
        return update_wrapper(patched_method, attr)

    def __setattr__(self, name: str, value):
        """
        Step 3 (2nd flow). Set some attribute
        """
        # set
        super().__setattr__(name, value)
        # validation only after set
        self._validate()


class Invariant(Base[T]):
    exception: ExceptionType

    def _init(self, *args, **kwargs):
        self.signature = None
        self.validator = self._make_validator()
        self.validate = self._validate
        return self.validate(*args, **kwargs)

    @classmethod
    def _default_exception(cls) -> ExceptionType:
        return InvContractError

    def _validate(self, obj) -> None:
        """
        Step 6. Process contract (validator)
        """

        if hasattr(self.validator, 'is_valid') and hasattr(obj, '__dict__'):
            self._vaa_validation(**vars(obj))
        else:
            self._simple_validation(obj)

    def validate_chain(self, *args, **kwargs) -> None:
        self.validate(*args, **kwargs)
        self.child_validator(*args, **kwargs)

    def __call__(self, _class: T) -> T:
        """
        Step 2. Return wrapped class.
        """
        # patch class parents and add method for validation

        # if already invarianted
        if hasattr(_class, '_validate_base'):
            self.child_validator = _class._validate_base  # type: ignore
            patched_class = type(
                _class.__name__,
                (_class, ),
                {'_validate_base': self.validate_chain},
            )
        # if it's first invariant
        else:
            patched_class = type(
                _class.__name__ + 'Invarianted',
                (InvariantedClass, _class),
                {'_validate_base': self.validate},
            )
        # Magic: _validate_base method uses Invariant as self, not _class

        # return update_wrapper(patched_class, _class)
        return patched_class  # type: ignore[return-value]
