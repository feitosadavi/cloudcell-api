from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Groq
    groq_api_key: str | None = None
    groq_model: str = ""
    groq_system_prompt: str | None = None

    # Chatwoot
    chatwoot_url: str
    chatwoot_api_token: str = ""          # user_access_token for REST calls
    chatwoot_account_id: str = "1"

    # Evolution API
    evolution_url: str
    evolution_instance: str
    evolution_api_key: str
    
    # Gemini
    gemini_api_key: str
    gemini_model: str = "gemini-1.5-flash"
    gemini_system_prompt: str = (
        "Você é um assistente de atendimento ao cliente prestativo e cordial. "
        "Responda sempre em português, de forma clara e objetiva."
    )

    # App
    max_history_messages: int = 20        # per conversation
    request_timeout: int = 30            # seconds


settings = Settings()
