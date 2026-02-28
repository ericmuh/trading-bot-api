from __future__ import annotations

from pydantic import BaseModel, Field


class LicenseActivateRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    license_key: str = Field(..., min_length=4)


class LicenseStatusResponse(BaseModel):
    user_id: str
    has_license: bool
    valid: bool
    status: str | None = None
    message: str
    license_key: str | None = None
    expires_at: str | None = None


class AdminLicenseCreateRequest(BaseModel):
    license_key: str = Field(..., min_length=4)
    expires_at: str = Field(..., min_length=10)
    status: str = Field(default="active", pattern="^(active|expired|revoked)$")


class AdminLicenseUpdateRequest(BaseModel):
    status: str | None = Field(default=None, pattern="^(active|expired|revoked)$")
    expires_at: str | None = Field(default=None, min_length=10)


class AdminLicenseResponse(BaseModel):
    id: int
    license_key: str
    status: str
    assigned_user_id: str | None = None
    expires_at: str
    created_at: str
    updated_at: str
