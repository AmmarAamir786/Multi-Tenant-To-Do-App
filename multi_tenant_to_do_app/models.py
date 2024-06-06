
from fastapi import Form
from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from typing import Annotated

# Create the model for our Todos
class Todo (SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(index=True, min_length=3, max_length=54)
    is_completed: bool = Field(default=False)
    user_id: int = Field(foreign_key="user.id")

# Create the model for our Users
class User (SQLModel, table=True):
        id: int = Field(default=None, primary_key=True)
        username: str
        email:str
        password:str

# Create the model for when a new user registers
class Register_User (BaseModel):
            username: Annotated[
            str,
            Form(),
        ]
            email: Annotated[
            str,
            Form(),
        ]
            password: Annotated[
            str,
            Form(),
        ]

# Create the models used in token creation and 
class Token (BaseModel):
        access_token:str
        token_type: str
        refresh_token: str

class TokenData (BaseModel):
        username:str

class RefreshTokenData (BaseModel):
        email:str


# Create the models to modify and create Todos
class Todo_Create (BaseModel):
    content: str

class Todo_Edit (BaseModel):
       content:str
       is_completed: bool

