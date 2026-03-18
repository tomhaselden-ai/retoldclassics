from backend.config.settings import DATABASE_URL, JWT_SECRET, SMTP_FROM_EMAIL, SMTP_HOST, is_production_env


def validate_runtime_settings() -> None:
    if not is_production_env():
        return

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL must be configured when APP_ENV is production")

    if not JWT_SECRET or JWT_SECRET == "change_me":
        raise RuntimeError("JWT_SECRET must be configured with a non-default value when APP_ENV is production")

    if not SMTP_HOST or not SMTP_FROM_EMAIL:
        raise RuntimeError(
            "SMTP_HOST and SMTP_FROM_EMAIL must be configured when APP_ENV is production so password reset email can be delivered"
        )
