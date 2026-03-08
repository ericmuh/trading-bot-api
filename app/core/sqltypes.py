import uuid

from sqlalchemy import JSON, LargeBinary, String
from sqlalchemy.types import CHAR, TypeDecorator
from sqlalchemy.dialects.postgresql import BYTEA, JSONB, UUID

class GUID(TypeDecorator):
	impl = CHAR
	cache_ok = True

	def load_dialect_impl(self, dialect):
		if dialect.name == "postgresql":
			return dialect.type_descriptor(UUID(as_uuid=True))
		return dialect.type_descriptor(CHAR(36))

	def process_bind_param(self, value, dialect):
		if value is None:
			return value

		if dialect.name == "postgresql":
			if isinstance(value, uuid.UUID):
				return value
			return uuid.UUID(str(value))

		if isinstance(value, uuid.UUID):
			return str(value)
		return str(uuid.UUID(str(value)))

	def process_result_value(self, value, dialect):
		if value is None:
			return value
		if isinstance(value, uuid.UUID):
			return value
		return uuid.UUID(str(value))


JSON_TYPE = JSONB().with_variant(JSON(), "sqlite")
BINARY_TYPE = BYTEA().with_variant(LargeBinary(), "sqlite")
