from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=3, max_length=32)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=128)


class AuthResponse(BaseModel):
    token: str
    username: str
