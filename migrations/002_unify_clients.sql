-- Migration: One hospital = one client (audio + image)
-- Makes registration idempotent by client_name

BEGIN;

-- 1. Remove duplicate client_names (keep latest by updated_at)
DELETE FROM clients a
USING clients b
WHERE a.client_name = b.client_name
  AND a.updated_at < b.updated_at;

-- 2. Make task_type nullable (client may train either modality)
ALTER TABLE clients ALTER COLUMN task_type DROP NOT NULL;

-- 3. Add unique constraint on client_name for upsert
ALTER TABLE clients ADD CONSTRAINT uq_clients_client_name UNIQUE (client_name);

COMMIT;
