from .health import HealthResource


def register_resources(api):
    api.add_resource(HealthResource, "/health")
