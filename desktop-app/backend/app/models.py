from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="student", nullable=False)
    created_at = Column(String(30), default="")
    attempts = relationship("Attempt", back_populates="user")

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(10), default="📘")
    lessons = relationship("Lesson", back_populates="subject", cascade="all, delete-orphan")

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    month = Column(Integer, nullable=False)
    week = Column(Integer, nullable=False)
    title = Column(String(180), nullable=False)
    content = Column(Text, nullable=False)
    example = Column(Text, nullable=False)
    exercise = Column(Text, nullable=False)
    level = Column(String(30), default="beginner")
    subject = relationship("Subject", back_populates="lessons")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    month = Column(Integer, nullable=False)
    prompt = Column(Text, nullable=False)
    options = Column(Text, nullable=False)
    answer = Column(Integer, nullable=False)
    explanation = Column(Text, nullable=False)

class LessonCompletion(Base):
    __tablename__ = "lesson_completions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson"),)

class Attempt(Base):
    __tablename__ = "attempts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    score = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    grade = Column(String(2), nullable=False)
    answers = Column(Text, nullable=False)
    created_at = Column(String(30), nullable=False)
    user = relationship("User", back_populates="attempts")

class StudentContact(Base):
    __tablename__ = "student_contacts"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_role = Column(String(20), nullable=False)
    approved = Column(Boolean, default=False, nullable=False)
    created_at = Column(String(30), nullable=False)
    __table_args__ = (UniqueConstraint("student_id", "contact_id", name="uq_student_contact"),)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event = Column(String(30), nullable=False)
    title = Column(String(180), nullable=False)
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(String(30), nullable=False)
