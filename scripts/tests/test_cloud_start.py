"""Cloud startup must preserve HTTPS, explicit database and sandbox boundaries."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("cloud_start", Path(__file__).resolve().parents[1] / "cloud_start.py")
cloud = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cloud)


class CloudConfigurationTests(unittest.TestCase):
    def base(self, **changes):
        return {"DATABASE_URL": "postgresql://test_user:placeholder-password@db.internal:5432/demo", "RENDER_EXTERNAL_URL": "https://demo.example.org", "APP_SESSION_SECRET": "local-test-session-not-production", "MOCK_WEBHOOK_SECRET": "local-test-provider-not-production", "DEMO_OPERATOR_CODE": "local-test-operator-not-production", **changes}

    def test_platform_postgres_uses_installed_psycopg_driver(self):
        for scheme in ("postgres", "postgresql", "postgresql+psycopg"):
            original = self.base(DATABASE_URL=scheme + "://user:p%40ss%3Aword@db/demo?sslmode=require")
            result = cloud.prepare_environment(original)
            self.assertEqual(result["DATABASE_URL"], "postgresql+psycopg://user:p%40ss%3Aword@db/demo?sslmode=require")
            self.assertEqual(original["DATABASE_URL"].split(":", 1)[0], scheme)

    def test_no_implicit_local_database_fallback(self):
        for value in ("", "sqlite:///demo.db", "mysql://user@db/demo"):
            with self.assertRaises(ValueError):
                cloud.prepare_environment(self.base(DATABASE_URL=value))

    def test_public_origin_is_exact_https_and_cookies_are_secure(self):
        result = cloud.prepare_environment(self.base(COOKIE_SECURE="false", FRONTEND_EXTRA_ORIGINS="http://untrusted.example"))
        self.assertEqual(result["FRONTEND_ORIGIN"], "https://demo.example.org")
        self.assertEqual(result["COOKIE_SECURE"], "true")
        self.assertEqual(result["FRONTEND_EXTRA_ORIGINS"], "")
        self.assertEqual(result["OCR_MAX_WORKERS"], "1")
        self.assertEqual(result["HOSTNAME"], "0.0.0.0")

    def test_invalid_public_origins_are_rejected(self):
        for value in ("", "http://demo.example.org", "https://demo.example.org/path", "https://demo.example.org?query=1", "https://demo.example.org#fragment", "https://user:password@demo.example.org"):
            with self.assertRaises(ValueError):
                cloud.prepare_environment(self.base(RENDER_EXTERNAL_URL=value))

    def test_custom_domain_overrides_platform_domain(self):
        result = cloud.prepare_environment(self.base(PUBLIC_APP_URL="https://custom.example.org/"))
        self.assertEqual(result["FRONTEND_ORIGIN"], "https://custom.example.org")

    def test_loopback_http_exception_cannot_be_used_for_public_http(self):
        with self.assertRaises(ValueError):
            cloud.prepare_environment(self.base(RENDER_EXTERNAL_URL="http://demo.example.org"), True)
        result = cloud.prepare_environment(self.base(PUBLIC_APP_URL="http://localhost:3102", PORT="3102", INTERNAL_API_PORT="8102"), True)
        self.assertEqual(result["HOSTNAME"], "127.0.0.1")
        self.assertEqual(result["COOKIE_SECURE"], "false")

    def test_port_collision_and_incorrect_production_proxy_are_rejected(self):
        for changes in ({"PORT": "8000"}, {"PORT": "0"}, {"PORT": "70000"}, {"INTERNAL_API_PORT": "8102"}):
            with self.assertRaises(ValueError):
                cloud.prepare_environment(self.base(**changes))

    def test_real_payment_configuration_is_rejected(self):
        for key, value in {"DEMO_MODE": "false", "ALLOW_REAL_PAYMENTS": "true", "PAYMENT_PROVIDER": "live", "AIRWALLEX_ENABLED": "true"}.items():
            with self.assertRaises(ValueError):
                cloud.prepare_environment(self.base(**{key: value}))

    def test_secret_placeholders_are_rejected(self):
        for key in ("APP_SESSION_SECRET", "MOCK_WEBHOOK_SECRET", "DEMO_OPERATOR_CODE"):
            for value in ("", "short", "REPLACE_WITH_A_SECRET"):
                with self.assertRaises(ValueError):
                    cloud.prepare_environment(self.base(**{key: value}))


if __name__ == "__main__":
    unittest.main()
