from .blacklist import BlacklistResource
from .health import HealthResource


def register_resources(api):
    api.add_resource(HealthResource, "/health")
    api.add_resource(BlacklistResource, "/blacklists")
