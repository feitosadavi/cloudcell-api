# Chatwoot → Gemini → Evolution API Bot

Webhook service que recebe mensagens do Chatwoot, processa com o Google Gemini e envia a resposta pela Evolution API.

## Fluxo

```
Chatwoot (webhook) → POST /webhook/chatwoot
        ↓
  Histórico de mensagens (em memória, carregado na inicialização)
        ↓
  Google Gemini (contexto completo da conversa)
        ↓
  Evolution API (envia resposta ao cliente)
```

## Configuração

### 1. Copie o arquivo de variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:

| Variável                 | Descrição                                                    |
| ------------------------ | ------------------------------------------------------------ |
| `AUTHENTICATION_API_KEY` | Token Bearer para a Evolution API                            |
| `CHATWOOT_URL`           | URL da sua instância Chatwoot                                |
| `CHATWOOT_API_TOKEN`     | `user_access_token` do Chatwoot (Settings → Profile)         |
| `CHATWOOT_ACCOUNT_ID`    | ID da conta no Chatwoot (padrão: `1`)                        |
| `EVOLUTION_URL`          | URL da sua instância Evolution API                           |
| `GEMINI_API_KEY`         | Chave da API do Google Gemini (Google AI Studio)             |
| `GEMINI_MODEL`           | Modelo Gemini a usar (padrão: `gemini-1.5-flash`)            |
| `GEMINI_SYSTEM_PROMPT`   | Prompt de sistema para personalizar o assistente             |
| `MAX_HISTORY_MESSAGES`   | Máximo de mensagens por conversa no histórico (padrão: `20`) |

### 2. Suba com Docker Compose

```bash
docker compose up -d --build
```

Verifique os logs:

```bash
docker compose logs -f
```

### 3. Configure o Webhook no Chatwoot

No Chatwoot: **Settings → Integrations → Webhooks → Add new webhook**

- URL: `http://SEU_IP:4000/webhook/chatwoot`
- Events: ✅ `Message Created`

## Endpoints

| Método | Path                | Descrição                  |
| ------ | ------------------- | -------------------------- |
| `GET`  | `/health`           | Health check               |
| `POST` | `/webhook/chatwoot` | Recebe eventos do Chatwoot |

## Arquitetura

- **FastAPI** + **Uvicorn** com 4 workers assíncronos — suporta múltiplos clientes simultaneamente
- **Histórico em memória** por `conversation_id` com tamanho máximo configurável
- **Startup**: busca todas as conversas do Chatwoot para seedar o histórico
- **httpx async** para todas as chamadas externas (Gemini, Evolution, Chatwoot)
- Container roda como usuário **não-root** por segurança
- Logs com rotação via Docker json-file driver

## Desenvolvimento local

```bash
pip install -r requirements.txt
cp .env.example .env   # preencha as variáveis
uvicorn app.main:app --reload --port 4000
```

## Escalonamento

Para aumentar a capacidade, basta aumentar o número de workers no `Dockerfile`:

```dockerfile
CMD ["uvicorn", "app.main:app", "--workers", "8", ...]
```

Ou usar múltiplas réplicas com um load balancer na frente.
