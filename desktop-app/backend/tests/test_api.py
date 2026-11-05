import json
import os
from datetime import datetime

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.auth import create_token, hash_password, verify_password
from app.database import Base, SessionLocal, engine
from app.main import calculate_grade, fallback_answer, notify_contacts, verified_tutor_facts
from app.models import Attempt, Lesson, LessonCompletion, Notification, Question, StudentContact, Subject, User
from app.seed import seed

def test_auth_curriculum_completion_and_saved_quiz_flow():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
        assert db.query(Subject).count() == 10
        assert db.query(Lesson).count() == 360
        assert all(db.query(Lesson).filter_by(subject_id=s.id).count() == 36 for s in db.query(Subject).all())
        assert db.query(Question).count() == 100
        assert "Python" in db.query(Question).filter_by(subject_id=1).first().prompt or "len(" in db.query(Question).filter_by(subject_id=1).first().prompt
        assert all(db.query(Question).filter_by(subject_id=s.id).count() == 10 for s in db.query(Subject).all())

        email = "test.student@example.com"
        existing = db.query(User).filter_by(email=email).first()
        if existing:
            db.delete(existing); db.commit()
        user = User(name="Test Student", email=email, password_hash=hash_password("safe-password-123"), created_at=datetime.utcnow().isoformat())
        db.add(user); db.commit(); db.refresh(user)
        assert verify_password("safe-password-123", user.password_hash)
        assert create_token(user)

        lesson = db.query(Lesson).filter_by(subject_id=1).order_by(Lesson.month, Lesson.week).first()
        assert lesson.content and lesson.example and lesson.exercise
        db.add(LessonCompletion(user_id=user.id, lesson_id=lesson.id)); db.commit()
        assert db.query(LessonCompletion).filter_by(user_id=user.id).count() == 1

        questions = db.query(Question).filter_by(subject_id=1).all()
        answers = [q.answer for q in questions]
        score, percent, grade = calculate_grade([q.answer for q in questions], answers)
        attempt = Attempt(user_id=user.id, subject_id=1, score=score, total=len(questions), percentage=percent, grade=grade, answers=json.dumps(answers), created_at=datetime.utcnow().isoformat())
        db.add(attempt); db.commit()
        saved = db.query(Attempt).filter_by(user_id=user.id).one()
        assert (saved.score, saved.total, saved.percentage, saved.grade) == (10, 10, 100.0, "A")
        parent = User(name="Parent",email="parent@example.com",password_hash=hash_password("safe-password-123"),role="parent")
        db.add(parent); db.commit(); db.refresh(parent)
        db.add(StudentContact(student_id=user.id,contact_id=parent.id,contact_role="parent",approved=True,created_at=datetime.utcnow().isoformat())); db.commit()
        notify_contacts(db,user,"quiz","Quiz result","Test Student scored 100%."); db.commit()
        alert=db.query(Notification).filter_by(recipient_id=parent.id,event="quiz").one()
        assert alert.student_id == user.id and "100%" in alert.body
    finally:
        db.close()

def test_quiz_grade_and_adaptive_thresholds():
    assert calculate_grade([0, 1, 2, 3], [0, 0, 0, 0]) == (1, 25.0, "F")
    assert calculate_grade([0, 1, 2, 3], [0, 1, 0, 0]) == (2, 50.0, "F")
    assert calculate_grade([0, 1, 2, 3], [0, 1, 2, 0]) == (3, 75.0, "C")
    assert calculate_grade([0, 1, 2, 3], [0, 1, 2, 3]) == (4, 100.0, "A")

def test_offline_tutor_never_claims_to_be_ai():
    answer=fallback_answer("Can you give me a hint?", "Mathematics")
    assert answer["mode"] == "local-fallback"
    assert "not an AI model" in answer["disclaimer"]
    assert answer["reply"]

def test_tutor_grounding_has_correct_python_loop_behavior():
    facts=verified_tutor_facts("Python Programming","What happens in a for loop over an empty list?")
    assert "does not test" in facts
    assert "zero times" in facts
