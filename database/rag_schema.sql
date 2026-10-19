-- Managed RAG extension; Alembic 73c9794e8f35 is authoritative.

ALTER TABLE demo_users ADD COLUMN is_rag_admin boolean NOT NULL DEFAULT false;


CREATE TABLE rag_documents (
	title VARCHAR NOT NULL,
	publisher VARCHAR NOT NULL,
	source_url VARCHAR,
	source_kind VARCHAR NOT NULL,
	license_note VARCHAR NOT NULL,
	category VARCHAR NOT NULL,
	language VARCHAR NOT NULL,
	jurisdiction VARCHAR NOT NULL,
	revision INTEGER NOT NULL,
	published BOOLEAN NOT NULL,
	deleted BOOLEAN NOT NULL,
	origin VARCHAR NOT NULL,
	filename VARCHAR NOT NULL,
	content_type VARCHAR NOT NULL,
	original_bytes BYTEA NOT NULL,
	sha256 VARCHAR NOT NULL,
	pages JSONB NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_by UUID,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT ck_rag_state CHECK (revision > 0 AND (NOT deleted OR NOT published)),
	CONSTRAINT ck_rag_kind CHECK (source_kind IN ('PUBLIC_REFERENCE','TEST_FIXTURE')),
	CONSTRAINT ck_rag_metadata CHECK (category IN ('POLICY','CLAIMS','GLOSSARY') AND language IN ('vi','en','zh') AND jurisdiction IN ('CN','VN','WORLD')),
	FOREIGN KEY(updated_by) REFERENCES demo_users (id)
)

;


CREATE TABLE rag_chunks (
	document_id UUID NOT NULL,
	revision INTEGER NOT NULL,
	ordinal INTEGER NOT NULL,
	page INTEGER NOT NULL,
	start INTEGER NOT NULL,
	"end" INTEGER NOT NULL,
	content VARCHAR NOT NULL,
	terms JSONB NOT NULL,
	token_count INTEGER NOT NULL,
	id UUID NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (document_id, revision, ordinal),
	CONSTRAINT ck_rag_chunk CHECK (revision > 0 AND page > 0 AND start >= 0 AND "end" > start AND token_count > 0),
	FOREIGN KEY(document_id) REFERENCES rag_documents (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_rag_chunks_document_id ON rag_chunks (document_id);


CREATE TABLE rag_revisions (
	document_id UUID NOT NULL,
	revision INTEGER NOT NULL,
	actor_id UUID,
	action VARCHAR NOT NULL,
	snapshot JSONB NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (document_id, revision),
	FOREIGN KEY(document_id) REFERENCES rag_documents (id) ON DELETE CASCADE,
	FOREIGN KEY(actor_id) REFERENCES demo_users (id)
)

;

CREATE INDEX ix_rag_revisions_document_id ON rag_revisions (document_id);
