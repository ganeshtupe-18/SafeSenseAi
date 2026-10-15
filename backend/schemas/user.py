from pydantic import BaseModel, EmailStr


class UserProfile(BaseModel):
    uid: str
    email: EmailStr
    display_name: str
    role: str
