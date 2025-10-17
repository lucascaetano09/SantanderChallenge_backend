-- SQLite
CREATE TABLE ID (
    ID TEXT PRIMARY KEY,                  -- Número do registro do cliente
    VL_FATU INTEGER,                      -- Valor do faturamento
    VL_SLDO INTEGER,                      -- Valor do saldo em conta
    DT_ABRT DATE,                         -- Data de abertura da empresa
    DS_CNAE TEXT,                         -- Descrição CNAE
    DT_REFE DATE                          -- Data de referência
);

CREATE TABLE TRANSACOES (
    ID INTEGER PRIMARY KEY AUTOINCREMENT, -- Chave técnica
    ID_PGTO TEXT,                         -- ID do cliente pagador
    ID_RCBE TEXT,                         -- ID do cliente recebedor
    VL INTEGER,                           -- Valor transacionado
    DS_TRAN TEXT,                         -- Descrição da transação
    DT_REFE DATE,                         -- Data de referência
    FOREIGN KEY (ID_PGTO) REFERENCES ID(ID),
    FOREIGN KEY (ID_RCBE) REFERENCES ID(ID)
);

CREATE TABLE IF NOT EXISTS USERS (
    ID INTEGER PRIMARY KEY AUTOINCREMENT, -- Chave técnica do usuário
    login TEXT UNIQUE NOT NULL,           -- Login do usuário (e.g., email)
    pwd TEXT NOT NULL                     -- Senha hash
);
