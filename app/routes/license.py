from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.db import store
from app.schemas.license import (
    AdminLicenseCreateRequest,
    AdminLicenseResponse,
    AdminLicenseUpdateRequest,
    LicenseActivateRequest,
    LicenseStatusResponse,
)

router = APIRouter(tags=["license"])


@router.post("/license/activate", response_model=LicenseStatusResponse)
def activate_license(payload: LicenseActivateRequest) -> LicenseStatusResponse:
    existing = store.get_license_by_key(payload.license_key)
    if existing is None:
        raise HTTPException(status_code=404, detail="License key not found")
    if existing["assigned_user_id"] not in (None, payload.user_id):
        raise HTTPException(status_code=409, detail="License key already assigned to another user")

    activated = store.activate_license_for_user(
        license_key=payload.license_key,
        user_id=payload.user_id,
    )
    if activated is None:
        raise HTTPException(status_code=500, detail="Failed to activate license")

    valid, message = store.is_license_valid_for_user(payload.user_id)
    current = store.get_license_by_user(payload.user_id)
    if current is None:
        return LicenseStatusResponse(
            user_id=payload.user_id,
            has_license=False,
            valid=False,
            message="License activation failed",
        )

    return LicenseStatusResponse(
        user_id=payload.user_id,
        has_license=True,
        valid=valid,
        status=str(current["status"]),
        message=message,
        license_key=str(current["license_key"]),
        expires_at=str(current["expires_at"]),
    )


@router.get("/license/status", response_model=LicenseStatusResponse)
def license_status(user_id: str = Query(..., min_length=1)) -> LicenseStatusResponse:
    row = store.get_license_by_user(user_id)
    if row is None:
        return LicenseStatusResponse(
            user_id=user_id,
            has_license=False,
            valid=False,
            message="No license is activated",
        )

    valid, message = store.is_license_valid_for_user(user_id)
    refreshed = store.get_license_by_user(user_id) or row
    return LicenseStatusResponse(
        user_id=user_id,
        has_license=True,
        valid=valid,
        status=str(refreshed["status"]),
        message=message,
        license_key=str(refreshed["license_key"]),
        expires_at=str(refreshed["expires_at"]),
    )


@router.post("/admin/licenses", response_model=AdminLicenseResponse)
def create_admin_license(payload: AdminLicenseCreateRequest) -> AdminLicenseResponse:
    if store.get_license_by_key(payload.license_key) is not None:
        raise HTTPException(status_code=409, detail="License key already exists")

    row = store.create_license(
        license_key=payload.license_key,
        expires_at=payload.expires_at,
        status=payload.status,
    )
    return AdminLicenseResponse(**row)


@router.put("/admin/licenses/{license_id}", response_model=AdminLicenseResponse)
def update_admin_license(license_id: int, payload: AdminLicenseUpdateRequest) -> AdminLicenseResponse:
    row = store.update_license(
        license_id=license_id,
        status=payload.status,
        expires_at=payload.expires_at,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="License not found")
    return AdminLicenseResponse(**row)


@router.post("/admin/licenses/{license_id}/revoke", response_model=AdminLicenseResponse)
def revoke_admin_license(license_id: int) -> AdminLicenseResponse:
    row = store.revoke_license(license_id)
    if row is None:
        raise HTTPException(status_code=404, detail="License not found")
    return AdminLicenseResponse(**row)


@router.get("/admin/licenses", response_model=list[AdminLicenseResponse])
def list_admin_licenses(limit: int = Query(default=200, ge=1, le=1000)) -> list[AdminLicenseResponse]:
    return [AdminLicenseResponse(**row) for row in store.list_licenses(limit=limit)]
