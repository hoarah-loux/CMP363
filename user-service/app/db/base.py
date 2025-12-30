from typing import Any, Dict

from sqlalchemy import MetaData, inspect
from sqlalchemy.ext.declarative import as_declarative, declared_attr
import re

metadata = MetaData()


def _pascal_to_snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


@as_declarative(metadata=metadata)
class Base:
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        return _pascal_to_snake(cls.__name__)

    def to_dict(self) -> Dict[str, Any]:
        return {
            attr.key: getattr(self, attr.key)
            for attr in inspect(self).mapper.column_attrs
        }
