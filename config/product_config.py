from dataclasses import dataclass, field

@dataclass
class ProductConfig:
    product_name: str = "ZYRA AI"
    environment: str = "development"
    local_only: bool = True
    remote_access_enabled: bool = False
    telemetry_enabled: bool = True
    notifications_enabled: bool = True
    auto_start_agent: bool = False
    require_confirmation_for_sensitive_actions: bool = True
    allowed_web_origins: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if self.environment not in {"development", "staging", "production"}:
            raise ValueError("invalid environment")
        if self.remote_access_enabled and self.local_only:
            raise ValueError("remote access cannot be enabled while local_only is true")
        if not self.product_name.strip():
            raise ValueError("product_name is required")

    @classmethod
    def production_defaults(cls) -> "ProductConfig":
        cfg = cls(
            environment="production",
            local_only=True,
            remote_access_enabled=False,
            telemetry_enabled=False,
            notifications_enabled=True,
            auto_start_agent=False,
            require_confirmation_for_sensitive_actions=True,
        )
        cfg.validate()
        return cfg
