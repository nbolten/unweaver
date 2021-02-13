from entwiner import GeoPackageNetwork
from .transit_mixin import TransitMixin


class TransitNetwork(GeoPackageNetwork, TransitMixin):
    pass
