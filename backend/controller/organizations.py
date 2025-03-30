from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from utils.database import get_db
from models.organization import Organization
from schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    OrganizationUserLink,
)
from models.user import User

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post(
    "/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED
)
async def create_organization(
    organization: OrganizationCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new organization."""
    try:
        db_organization = Organization(name=organization.name)
        db.add(db_organization)
        await db.commit()
        await db.refresh(db_organization)
        return db_organization
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create organization: {str(e)}",
        )


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(organization_id: int, db: AsyncSession = Depends(get_db)):
    """Get organization by ID."""
    stmt = select(Organization).where(Organization.id == organization_id)
    result = await db.execute(stmt)
    organization = result.scalar_one_or_none()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )
    return organization


@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """List all organizations with pagination."""
    stmt = select(Organization).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: int,
    organization: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update organization details."""
    stmt = select(Organization).where(Organization.id == organization_id)
    result = await db.execute(stmt)
    db_organization = result.scalar_one_or_none()
    if not db_organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    try:
        for key, value in organization.dict(exclude_unset=True).items():
            setattr(db_organization, key, value)
        await db.commit()
        await db.refresh(db_organization)
        return db_organization
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update organization: {str(e)}",
        )


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(organization_id: int, db: AsyncSession = Depends(get_db)):
    """Delete organization."""
    stmt = select(Organization).where(Organization.id == organization_id)
    result = await db.execute(stmt)
    db_organization = result.scalar_one_or_none()
    if not db_organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    try:
        await db.delete(db_organization)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete organization: {str(e)}",
        )


@router.post("/{organization_id}/users", response_model=OrganizationResponse)
async def link_user_to_organization(
    organization_id: int,
    user_link: OrganizationUserLink,
    db: AsyncSession = Depends(get_db),
):
    """Link a user to an organization."""
    # Check if organization exists
    org_stmt = select(Organization).where(Organization.id == organization_id)
    org_result = await db.execute(org_stmt)
    organization = org_result.scalar_one_or_none()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # Check if user exists
    user_stmt = select(User).where(User.id == user_link.user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    try:
        user.organization_id = organization_id
        await db.commit()
        await db.refresh(organization)
        return organization
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to link user to organization: {str(e)}",
        )
