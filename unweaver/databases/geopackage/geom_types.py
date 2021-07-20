from enum import Enum, auto


class GeoPackageGeoms(Enum):
    POINT = auto()
    LINESTRING = auto()

    def __repr__(self) -> str:
        return f"<${self.__class__.name}.${self.name}>"
