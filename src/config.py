from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    port: int = 3003
    host: str = "0.0.0.0"
    env: str = "development"
    log_level: str = "info"

    database_url: str = "sqlite:///./data/access_gate.db"

    core_business_url: str = "http://localhost:3006"
    core_business_event_path: str = "/api/v1/events/access"

    analytics_url: str = "http://localhost:3005"
    analytics_ingest_path: str = "/api/v1/ingest/access"

    integration_timeout_seconds: float = 3.0

    service_name: str = "access-gate-b3"
    service_product: str = "product-b"

    # Contract settings B6
    debounce_ttl_seconds: float = 2.0
    offline_mode: str = "fail_closed" # 'fail_closed' or 'fail_open'
    bulk_sync_batch_size: int = 100
    bulk_sync_max_rps: int = 5
    rate_limit_global_rps: int = 200
    rate_limit_log_rps: int = 50
    passage_timeout_seconds: int = 5

    # MQTT HiveMQ Config
    mqtt_host: str = "f6f78e87db4a4c189dd3d706745a5e93.s1.eu.hivemq.cloud"
    mqtt_port: int = 8883
    mqtt_username: str = "DVKN2026"
    mqtt_password: str = "ThaiBao12A@"
    mqtt_topic_input: str = "smart-campus/raw/access/rfid-uid"
    mqtt_topic_output: str = "smart-campus/events/access"

settings = Settings()
