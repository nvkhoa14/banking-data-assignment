-- 1. Create schema and enable extensions
CREATE SCHEMA IF NOT EXISTS banking;
SET search_path = banking;

-- 2. Customer table
CREATE TABLE IF NOT EXISTS customer (
  customer_id   UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name     TEXT             NOT NULL,
  birth_date    DATE             NOT NULL,
  id_number     TEXT             NOT NULL,    
  contact       TEXT             UNIQUE NOT NULL,
  created_at    TIMESTAMPTZ      NOT NULL DEFAULT now()
);

-- 3. Account table
CREATE TABLE IF NOT EXISTS account (
  account_id   UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id  UUID             NOT NULL REFERENCES customer(customer_id),
  type         VARCHAR(20)      NOT NULL,      -- e.g., 'savings', 'checking'
  status       VARCHAR(10)      NOT NULL DEFAULT 'active',      -- e.g., 'active', 'blocked'
  balance      NUMERIC(18,2)    NOT NULL DEFAULT 0,
  opened_at    TIMESTAMPTZ      NOT NULL DEFAULT now()
);

-- 4. Device tracking table
CREATE TABLE IF NOT EXISTS device (
  device_id   UUID              PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID              NOT NULL REFERENCES customer(customer_id),
  device_type VARCHAR(30)       NOT NULL,      -- 'desktop', 'mobile', etc.
  ip_address  INET              NOT NULL,
  active      BOOLEAN           NOT NULL DEFAULT TRUE,
  first_seen  TIMESTAMPTZ       NOT NULL DEFAULT now()
);

-- 5. Transaction table
CREATE TABLE IF NOT EXISTS transaction (
  tx_id        UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id   UUID             NOT NULL REFERENCES account(account_id),
  device_id    UUID,                           -- for tracking
  target_id    UUID,                           -- for transfers, can be NULL for deposits/withdrawals
  amount       NUMERIC(18,2)    NOT NULL,
  method       VARCHAR(20)      NOT NULL,      -- 'online', 'card', etc.
  status       VARCHAR(10)      NOT NULL,      -- 'pending', 'posted', 'failed'
  timestamp    TIMESTAMPTZ      NOT NULL DEFAULT now()
);

-- 6. Authentication log table
CREATE TABLE IF NOT EXISTS auth_log (
  auth_id      UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
  tx_id        UUID             NOT NULL REFERENCES transaction(tx_id),
  auth_type    VARCHAR(20)      NOT NULL,      -- 'PIN', 'otp', 'biometric'
  success_flag BOOLEAN          ,
  auth_time    TIMESTAMPTZ      NOT NULL DEFAULT now()
);

-- 7. Fraud risk tagging table
CREATE TABLE IF NOT EXISTS risk_tag (
  risk_id     UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
  tx_id       UUID             NOT NULL REFERENCES transaction(tx_id),
  tag_reason  TEXT             NOT NULL,
  severity    SMALLINT         NOT NULL,       -- e.g., 1 (low) to 5 (high)
  flagged_at  TIMESTAMPTZ      NOT NULL DEFAULT now()
);

-- 8. Indexes & Performance Hints
CREATE INDEX IF NOT EXISTS idx_account_customer  ON account(customer_id);
CREATE INDEX IF NOT EXISTS idx_tx_account        ON transaction(account_id);
CREATE INDEX IF NOT EXISTS idx_auth_tx           ON auth_log(tx_id);
CREATE INDEX IF NOT EXISTS idx_device_cust       ON device(customer_id);
CREATE INDEX IF NOT EXISTS idx_risk_tx           ON risk_tag(tx_id);
