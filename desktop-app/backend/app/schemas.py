from pydantic import BaseModel, EmailStr, Field, conlist
from typing import List, Optional, Literal

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="student", regex="^(student|teacher|parent)$")

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class QuizIn(BaseModel):
    subject_id: int
    answers: List[int]

class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)

class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    subject: Optional[str] = None
    history: conlist(ChatTurn, max_items=12) = Field(default_factory=list)

class SubjectInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=10, max_length=2000)
    icon: str = Field(default="📘", max_length=10)

class LessonInput(BaseModel):
    month: int = Field(ge=1, le=9)
    week: int = Field(ge=1, le=4)
    title: str = Field(min_length=2, max_length=180)
    content: str = Field(min_length=10)
    example: str = Field(min_length=1)
    exercise: str = Field(min_length=5)
    level: str = Field(default="beginner", max_length=30)

class StudentUpdateIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr

class ContactRequestIn(BaseModel):
    email: EmailStr
    role: str = Field(regex="^(teacher|parent)$")
