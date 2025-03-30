from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class OrganizationBase(BaseModel):
    name: str


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None


class OrganizationUserLink(BaseModel):
    user_id: int


class OrganizationResponse(OrganizationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
