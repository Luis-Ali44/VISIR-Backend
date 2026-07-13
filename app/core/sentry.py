import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

from app.core.config import settings


def configurar_sentry() -> None:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.environment,
        integrations=[CeleryIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
