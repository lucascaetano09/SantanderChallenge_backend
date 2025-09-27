# API Documentation

This document provides details on the available API endpoints, including request structures, parameters, and example responses.

---

## 1. Get Client Overview

Retrieves a summary of financial statistics for a specific client.

- **URL:** `/transactions/overview`
- **Method:** `GET`

### Query Parameters

| Parameter | Type   | Required | Description                          |
| :-------- | :----- | :------- | :----------------------------------- |
| `id`      | string | Yes      | The unique identifier of the client. |

### Example Request

```http
GET /transactions/overview?id=CLIENT_ID_123
```

### Example Response

**On Success (200 OK):**

Returns a JSON object containing the client's transaction summary.

```json
{
  "totalClientes": 15,
  "totalTransacoes": 50,
  "transactionBalance": 15000.75
}
```

**On Error (400 Bad Request):**

If the `id` parameter is missing.

```json
{
  "error": "O parâmetro \"id\" do cliente é obrigatório"
}
```

---

## 2. Get Transactions List

Retrieves a list of transactions for a specific client, with optional filters.

- **URL:** `/transactions/list`
- **Method:** `GET`

### Query Parameters

| Parameter    | Type    | Required | Description                                                                                     |
| :----------- | :------ | :------- | :---------------------------------------------------------------------------------------------- |
| `id`         | string  | Yes      | The unique identifier of the client.                                                            |
| `page`       | integer | No       | The page number for pagination (defaults to 1). Each page contains 10 transactions.             |
| `date`       | string  | No       | Comma-separated list of months to filter by (e.g., `1,2,12`).                                   |
| `type`       | string  | No       | Comma-separated list of transaction types to filter by (e.g., `Pagamento de Fornecedor,Venda`). |
| `inOut`      | integer | No       | Filter by direction: `1` for income (Entrada), `2` for expense (Saída).                         |
| `customProv` | string  | No       | Filter for transactions with a specific customer/provider ID.                                   |

### Example Requests

**Basic Request:**

```http
GET /transactions/list?id=CLIENT_ID_123
```

**Filtered Request (Income transactions from January and February):**

```http
GET /transactions/list?id=CLIENT_ID_123&inOut=1&date=1,2
```

### Example Response

**On Success (200 OK):**

Returns a JSON object containing pagination info and an array of transaction objects.

```json
{
  "totalPages": 5,
  "transactions": [
    {
      "inOut": "Entrada",
      "customProv": "CUSTOMER_ID_456",
      "date": "25/10/2023",
      "type": "Venda de Mercadoria",
      "value": "R$1500"
    },
    {
      "inOut": "Saída",
      "customProv": "PROVIDER_ID_789",
      "date": "22/10/2023",
      "type": "Pagamento de Fornecedor",
      "value": "R$850"
    }
  ]
}
```

**On Error (404 Not Found):**

If the client `id` does not exist in the database.

```json
{
  "error": "Cliente não encontrado"
}
```
