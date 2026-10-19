from pathlib import Path
from decimal import Decimal
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    database_url: str = "postgresql+psycopg://fintech_demo:fintech_demo_local_only@127.0.0.1:5434/insurance_payment_demo"
    demo_mode: bool = True
    allow_real_payments: bool = False
    payment_provider: str = "mock"
    airwallex_enabled: bool = False
    app_session_secret: str
    mock_webhook_secret: str
    demo_operator_code: str
    frontend_origin: str = "http://localhost:3000"
    frontend_extra_origins: str = ""
    fx_demo_vnd_per_cny: Decimal = Decimal("3500")
    fx_demo_variable_fee_percent: Decimal = Decimal("1.5")
    fx_demo_fixed_fee_vnd: Decimal = Decimal("5000")
    fx_quote_ttl_seconds: int = 600
    provider_worker_enabled: bool = True
    ocr_max_workers: int = Field(default=2, ge=1, le=2)
    gemini_enabled: bool = False
    gemini_api_key: SecretStr = Field(default=SecretStr(""), repr=False, exclude=True)
    gemini_model: str = Field(default="gemini-3.8-flash", pattern=r"^[a-z0-9][a-z0-9.-]{1,79}$")
    gemini_timeout_seconds: int = Field(default=25, ge=5, le=45)
    # PAID_PRIVATE requires an operator-verified paid Google Cloud project/DPA.
    gemini_data_mode: str = Field(default="DEMO_ONLY", pattern=r"^(DEMO_ONLY|PAID_PRIVATE)$")
    rag_admin_email: str = ""
    rag_admin_password: SecretStr = Field(default=SecretStr(""), repr=False, exclude=True)
    cookie_secure: bool = False
    session_hours: int = 24
    fx_reference_cache_hours: int = 6
    fx_reference_max_age_days: int = 7
    service_fee_percent: Decimal = Decimal("0")
    service_fixed_fee_vnd: Decimal = Decimal("0")

    @property
    def frontend_origins(self) -> list[str]:
        return list(dict.fromkeys([self.frontend_origin, *[origin.strip().rstrip("/") for origin in self.frontend_extra_origins.split(",") if origin.strip()]]))

    @model_validator(mode="after")
    def safe_config(self):
        if self.allow_real_payments or self.payment_provider != "mock" or self.airwallex_enabled:
            raise ValueError("Only mock payments are implemented; real payments cannot be enabled")
        for value in (self.app_session_secret, self.mock_webhook_secret, self.demo_operator_code):
            if len(value) < 16 or value.startswith("REPLACE_"):
                raise ValueError("Run scripts/bootstrap.py to generate local demo secrets")
        if self.fx_demo_vnd_per_cny <= 0 or self.fx_demo_variable_fee_percent < 0 or self.fx_demo_fixed_fee_vnd < 0:
            raise ValueError("Invalid FX/fee settings")
        if self.fx_demo_fixed_fee_vnd != self.fx_demo_fixed_fee_vnd.to_integral_value() or self.fx_quote_ttl_seconds < 1:
            raise ValueError("VND fee must be integral and quote TTL positive")
        if self.service_fee_percent < 0 or self.service_fixed_fee_vnd < 0 or self.service_fixed_fee_vnd != self.service_fixed_fee_vnd.to_integral_value():
            raise ValueError("Invalid service fee settings")
        if not 1 <= self.session_hours <= 168 or self.fx_reference_cache_hours < 1 or self.fx_reference_max_age_days < 1:
            raise ValueError("Invalid session/cache lifetime")
        return self


settings = Settings()
