-- LocalLedger schema.
--
-- Money is NUMERIC, never floating point: these are financial records and
-- binary floats cannot represent decimal cents exactly.

CREATE TYPE document_status AS ENUM (
    'pending',      -- accepted, not yet processed
    'processing',   -- claimed by a worker
    'extracted',    -- fields extracted and validated
    'review'        -- something went wrong; original moved to /review
);

CREATE TABLE documents (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sha256            CHAR(64)        NOT NULL,
    original_filename TEXT            NOT NULL,
    mime_type         TEXT            NOT NULL,
    byte_size         BIGINT          NOT NULL CHECK (byte_size >= 0),
    status            document_status NOT NULL DEFAULT 'pending',
    stored_path       TEXT,
    error_message     TEXT,
    created_at        TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ     NOT NULL DEFAULT now(),
    processed_at      TIMESTAMPTZ,

    -- Idempotency: the same bytes are the same document, forever. A re-drop of
    -- an already-seen receipt hits this constraint and is treated as a no-op.
    CONSTRAINT documents_sha256_key UNIQUE (sha256)
);

CREATE INDEX documents_status_idx     ON documents (status);
CREATE INDEX documents_created_at_idx ON documents (created_at DESC);

CREATE TABLE extractions (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id   BIGINT       NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    vendor        TEXT,
    document_date DATE,
    subtotal      NUMERIC(14, 2),
    tax           NUMERIC(14, 2),
    total         NUMERIC(14, 2),
    currency      CHAR(3),
    category      TEXT,
    model_name    TEXT         NOT NULL,
    raw_response  JSONB        NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),

    -- One current extraction per document; re-running replaces it.
    CONSTRAINT extractions_document_id_key UNIQUE (document_id)
);

CREATE INDEX extractions_vendor_idx        ON extractions (vendor);
CREATE INDEX extractions_document_date_idx ON extractions (document_date);

CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER documents_touch_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
