# Chatbot API Documentation

This document provides details on the API endpoints available for interacting with the AI-powered chatbot assistant.

---

## 1. Send a Chat Message

Sends a user's question to the chatbot and receives a contextualized response.

- **URL:** `/api/chat`
- **Method:** `POST`

### Request Body

A JSON object containing the user's question.

```json
{
  "pergunta": "Como funciona o dashboard de vendas?"
}
```

### Example Response

**On Success (200 OK):**

Returns the chatbot's answer based on the provided context and conversation history.

```json
{
  "success": true,
  "pergunta": "Como funciona o dashboard de vendas?",
  "resposta": "O dashboard de vendas permite visualizar a performance em tempo real, com filtros por período, região e produto. Os gráficos são interativos, permitindo um aprofundamento nos dados (drill-down) ao clicar neles. Precisa de mais alguma ajuda?",
  "timestamp": "2024-05-21T11:30:00.123456"
}
```

**On Error (400 Bad Request):**

If the `pergunta` field is missing or empty.

```json
{
  "success": false,
  "error": "Pergunta é obrigatória"
}
```

---

## 2. Update Chat Context

Updates the chatbot's knowledge of the current application state (e.g., active filters, current screen). This should be called whenever the user navigates or changes filters in the UI to ensure the chatbot's answers are relevant.

- **URL:** `/api/atualizar-dados`
- **Method:** `POST`

### Request Body

A JSON object containing the new contextual data. Any key provided will update the existing context.

```json
{
  "dados": {
    "tela_atual": "Relatório de Vendas - Região Sudeste",
    "filtros_ativos": {
      "periodo": "Última semana",
      "regiao": "Sudeste"
    }
  }
}
```

### Example Response

**On Success (200 OK):**

```json
{
  "success": true,
  "message": "Dados atualizados com sucesso!",
  "dados_atuais": {
    "data_atual": "15/01/2024",
    "usuario_logado": "Analista",
    "tela_atual": "Relatório de Vendas - Região Sudeste",
    "filtros_ativos": {
      "periodo": "Última semana",
      "regiao": "Sudeste",
      "produto": "Todos"
    }
  }
}
```

---

## 3. Get Chat Status

Checks the operational status of the chat API and retrieves the chatbot's current contextual data. Useful for debugging.

- **URL:** `/api/status`
- **Method:** `GET`

### Example Response

**On Success (200 OK):**

```json
{
  "success": true,
  "status": "API funcionando",
  "dados_atuais": {
    "tela_atual": "Dashboard Principal",
    "filtros_ativos": { "periodo": "Último mês" }
  },
  "total_conversas": 5,
  "ultima_atualizacao": "2024-05-21T11:35:00.123456"
}
```

---

## 4. Get Chat History

Retrieves the last 10 interactions from the current conversation history.

- **URL:** `/api/historico`
- **Method:** `GET`

### Example Response

**On Success (200 OK):**

```json
{
  "success": true,
  "historico": [
    {
      "timestamp": "11:30:00",
      "usuario": "Como funciona o dashboard de vendas?",
      "assistente": "O dashboard de vendas permite visualizar a performance em tempo real..."
    }
  ],
  "total": 1
}
```

---

## 5. Clear Chat History

Clears the entire conversation history for the current session. This can be used to "reset" the chatbot.

- **URL:** `/api/limpar-historico`
- **Method:** `POST`

### Example Response

**On Success (200 OK):**

```json
{
  "success": true,
  "message": "Histórico limpo com sucesso!"
}
```

---

## 6. Configure System (For Admin/Debug)

Allows dynamic alteration of the chatbot's core system information.

- **URL:** `/api/configurar-sistema`
- **Method:** `POST`

### Example Response

**On Success (200 OK):**

```json
{
  "success": true,
  "message": "Sistema configurado com sucesso!"
}
```
