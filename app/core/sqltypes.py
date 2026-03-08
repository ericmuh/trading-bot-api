from sqlalchemy import JSON, LargeBinary, String
from sqlalchemy.dialects.postgresql import BYTEA, JSONB, UUID

GUID = UUID(as_uuid=True).with_variant(String(36), "sqlite")
JSON_TYPE = JSONB().with_variant(JSON(), "sqlite")
BINARY_TYPE = BYTEA().with_variant(LargeBinary(), "sqlite")
