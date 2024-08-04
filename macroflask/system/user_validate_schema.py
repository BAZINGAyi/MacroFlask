import re
from pydantic import BaseModel, constr, field_validator, Field


class UserSchema(BaseModel):
    username: constr(min_length=4, max_length=25)
    email: str
    password: constr(min_length=6)
    phone_number: str = None  # Optional field
    is_active: bool = True    # Default field
    locale: str = Field(pattern=r'^[a-z]{2}-[A-Z]{2}$', default='en-US')
    role_id: int

    @field_validator('email')
    def validate_email(cls, value):
        email_regex = re.compile(
            r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        )
        if not email_regex.match(value):
            raise ValueError('Invalid email address')
        return value


class RoleSchema(BaseModel):
    name: constr(min_length=4, max_length=25)
    description: str = None
    is_active: bool = True