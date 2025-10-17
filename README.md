# API Documentation

This document provides details on the available API endpoints, including request structures, parameters, and example responses.

---

## 0. Authentication API Endpoints

These endpoints handle user registration and login.

---

### 0.1. User Sign Up

Registers a new user with a unique login and password.

- **URL:** `/auth/signUp`
- **Method:** `POST`

#### Request Body

A JSON object containing the user's login and password.

| Parameter  | Type   | Required | Description                            |
| :--------- | :----- | :------- | :------------------------------------- |
| `login`    | string | Yes      | The user's unique login (e.g., email). |
| `password` | string | Yes      | The user's chosen password.            |

#### Example Request

```http
POST /auth/signUp
Content-Type: application/json

{
  "login": "user@example.com",
  "password": "securepassword123"
}
```

#### Example Response

**On Success (201 Created):**

```json
{
  "success": true,
  "message": "Usuário registrado com sucesso."
}
```

**On Error (400 Bad Request):**

If `login` or `password` is missing.

```json
{
  "success": false,
  "error": "Login e senha são obrigatórios."
}
```

**On Error (409 Conflict):**

If the `login` already exists.

```json
{
  "success": false,
  "error": "Usuário já existe."
}
```

---

### 0.2. User Login

Authenticates a user with their login and password.

- **URL:** `/auth/login`
- **Method:** `POST`

#### Request Body

A JSON object containing the user's login and password.

| Parameter  | Type   | Required | Description          |
| :--------- | :----- | :------- | :------------------- |
| `login`    | string | Yes      | The user's login.    |
| `password` | string | Yes      | The user's password. |

#### Example Request

```http
POST /auth/login
Content-Type: application/json

{
  "login": "user@example.com",
  "password": "securepassword123"
}
```

#### Example Response

**On Success (200 OK):**

```json
{
  "success": true,
  "message": "Login bem-sucedido."
}
```

**On Error (400 Bad Request):**

If `login` or `password` is missing.

```json
{
  "success": false,
  "error": "Login e senha são obrigatórios."
}
```

**On Error (401 Unauthorized):**

If the credentials are invalid.

```json
{
  "success": false,
  "error": "Credenciais inválidas."
}
```

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

---

## 3. Get Bar Chart Data

Retrieves aggregated monthly income and expense data for a specific client, suitable for rendering a bar chart.

- **URL:** `/transactions/graphs/barChart`
- **Method:** `GET`

### Query Parameters

| Parameter | Type   | Required | Description                          |
| :-------- | :----- | :------- | :----------------------------------- |
| `id`      | string | Yes      | The unique identifier of the client. |

### Example Request

```http
GET /transactions/graphs/barChart?id=CLIENT_ID_123
```

### Example Response

**On Success (200 OK):**

Returns a JSON array where each object represents a month with its total income and expenses.

```json
[
  {
    "month": "Set",
    "income": 25000,
    "expense": 12000
  },
  {
    "month": "Out",
    "income": 32000,
    "expense": 18500
  }
]
```

---

## 4. Get CNAE Pie Chart Data

Retrieves aggregated data of the top 5 business activities (CNAE) based on total revenue, suitable for rendering a pie chart.

- **URL:** `/cnae/graphs/pieChart`
- **Method:** `GET`

### Query Parameters

This endpoint does not require any query parameters.

### Example Request

```http
GET /cnae/graphs/pieChart
```

### Example Response

**On Success (200 OK):**

Returns a JSON array where each object represents one of the top 5 CNAEs, including the count of accounts associated with it.

```json
[
  {
    "cnae": "Comércio varejista de mercadorias em geral",
    "accounts": 42
  },
  {
    "cnae": "Atividades de consultoria em gestão empresarial",
    "accounts": 25
  }
]
```

---

## 5. Get Accounts by CNAE

Retrieves a paginated list of accounts belonging to a specific business activity (CNAE). For accounts with multiple records, only the most recent one is returned.

- **URL:** `/cnae/list`
- **Method:** `GET`

### Query Parameters

| Parameter | Type    | Required | Description                                                                     |
| :-------- | :------ | :------- | :------------------------------------------------------------------------------ |
| `cnae`    | string  | Yes      | The exact "DS_CNAE" description to filter accounts by.                          |
| `page`    | integer | No       | The page number for pagination (defaults to 1). Each page contains 12 accounts. |

### Example Request

```http
GET /cnae/list?cnae=Cultivo%20de%20soja&page=1
```

### Example Response

**On Success (200 OK):**

Returns a JSON object containing pagination info and an array of account objects.

```json
{
  "totalPages": 3,
  "accounts": [
    {
      "account": "ACCOUNT_ID_001",
      "invoicing": "R$75000",
      "date": "15/03/2018"
    },
    {
      "account": "ACCOUNT_ID_002",
      "invoicing": "R$120000",
      "date": "22/07/2020"
    }
  ]
}
```

---

## 6. Get Maturity Overview

Retrieves a summary of company maturity classifications. It returns the count of companies in each maturity stage (`Iniciante`, `Madura`, `Expansão`, `Declínio`).

- **URL:** `/maturity/overview`
- **Method:** `GET`

### Query Parameters

This endpoint does not require any query parameters.

### Example Request

```http
GET /maturity/overview
```

### Example Response

**On Success (200 OK):**

Returns a JSON object where keys are the maturity stages and values are the count of companies in that stage.

```json
{
  "Iniciante": 150,
  "Madura": 450,
  "Expansão": 200,
  "Declínio": 50
}
}
```

---

## 7. Get Accounts by Maturity

Retrieves a paginated list of company accounts, with an optional filter for maturity state. For each account, only the most recent data record is returned.

- **URL:** `/maturity/list`
- **Method:** `GET`

### Query Parameters

| Parameter | Type    | Required | Description                                                                            |
| :-------- | :------ | :------- | :------------------------------------------------------------------------------------- |
| `state`   | string  | No       | The maturity state to filter by (e.g., `Iniciante`, `Madura`, `Expansão`, `Declínio`). |
| `page`    | integer | No       | The page number for pagination (defaults to 1). Each page contains 20 accounts.        |

### Example Requests

**Basic Request (all states):**

```http
GET /maturity/list?page=1
```

**Filtered Request (only "Madura" companies):**

```http
GET /maturity/list?state=Madura&page=1
```

### Example Response

**On Success (200 OK):**

Returns a JSON object containing pagination info and an array of account objects.

```json
{
  "totalPages": 10,
  "accounts": [
    {
      "ID": "ID_EMPRESA_001",
      "FATURAMENTO": "R$500000",
      "SALDO": "R$120000",
      "DATA_ABERTURA": "10/05/2015",
      "CNAE": "Comércio varejista de mercadorias em geral",
      "DATA_REFERENCIA": "31/12/2023"
    }
  ]
}
```
