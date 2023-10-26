from typing import Optional

from pydantic import BaseModel, EmailStr, constr


class CreateUser(BaseModel):
    email: EmailStr
    password: constr(min_length=8)


class CreateAdv(BaseModel):
    title: str
    description: Optional[str] = None


class UpdateAdv(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None