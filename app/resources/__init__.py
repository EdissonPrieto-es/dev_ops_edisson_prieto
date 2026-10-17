from .blacklist import BlacklistEmailResource, BlacklistResource
from .health import HealthResource


def register_resources(api):
    api.add_resource(HealthResource, "/health")
    api.add_resource(BlacklistResource, "/blacklists")
    api.add_resource(BlacklistEmailResource, "/blacklists/<string:email>")
