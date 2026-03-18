import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.auth.password_reset import send_password_reset_email
from backend.config.runtime_validation import validate_runtime_settings


class RuntimeValidationTests(unittest.TestCase):
    def test_validate_runtime_settings_allows_development_defaults(self) -> None:
        with patch("backend.config.runtime_validation.is_production_env", return_value=False):
            validate_runtime_settings()

    def test_validate_runtime_settings_requires_database_url_in_production(self) -> None:
        with patch("backend.config.runtime_validation.is_production_env", return_value=True), patch(
            "backend.config.runtime_validation.DATABASE_URL",
            None,
        ):
            with self.assertRaises(RuntimeError):
                validate_runtime_settings()

    def test_validate_runtime_settings_requires_non_default_jwt_secret(self) -> None:
        with patch("backend.config.runtime_validation.is_production_env", return_value=True), patch(
            "backend.config.runtime_validation.DATABASE_URL",
            "mysql+pymysql://user:pass@db/app",
        ), patch("backend.config.runtime_validation.JWT_SECRET", "change_me"):
            with self.assertRaises(RuntimeError):
                validate_runtime_settings()

    def test_validate_runtime_settings_requires_smtp_in_production(self) -> None:
        with patch("backend.config.runtime_validation.is_production_env", return_value=True), patch(
            "backend.config.runtime_validation.DATABASE_URL",
            "mysql+pymysql://user:pass@db/app",
        ), patch("backend.config.runtime_validation.JWT_SECRET", "good-secret"), patch(
            "backend.config.runtime_validation.SMTP_HOST",
            None,
        ), patch("backend.config.runtime_validation.SMTP_FROM_EMAIL", None):
            with self.assertRaises(RuntimeError):
                validate_runtime_settings()

    def test_password_reset_email_logs_in_development_when_smtp_missing(self) -> None:
        with patch("backend.auth.password_reset.SMTP_HOST", None), patch(
            "backend.auth.password_reset.SMTP_FROM_EMAIL",
            None,
        ), patch("backend.auth.password_reset.is_production_env", return_value=False):
            send_password_reset_email("reader@example.com", "reset-token")

    def test_password_reset_email_raises_in_production_when_smtp_missing(self) -> None:
        with patch("backend.auth.password_reset.SMTP_HOST", None), patch(
            "backend.auth.password_reset.SMTP_FROM_EMAIL",
            None,
        ), patch("backend.auth.password_reset.is_production_env", return_value=True):
            with self.assertRaises(HTTPException):
                send_password_reset_email("reader@example.com", "reset-token")


if __name__ == "__main__":
    unittest.main()
