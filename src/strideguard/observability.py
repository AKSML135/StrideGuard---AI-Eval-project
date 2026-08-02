import os
from typing import Any

from strideguard.settings import Settings, get_settings


def configure_phoenix(
    settings: Settings | None = None,
) -> Any | None:
    settings = settings or get_settings()
    if not settings.enable_phoenix:
        return None

    os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = (
        settings.phoenix_collector_endpoint
    )
    os.environ["PHOENIX_PROJECT"] = settings.phoenix_project

    from phoenix.otel import register

    return register(
        project_name=settings.phoenix_project,
        auto_instrument=True,
    )


# Call configure_phoenix() before constructing the model or running the agent.
