import json, os, re
from datetime import datetime
from pathlib import Path
import httpx
from sqlalchemy import or_
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import User, Subject, Lesson, Question, LessonCompletion, Attempt, StudentContact, Notification
from .schemas import RegisterIn, LoginIn, QuizIn, ChatIn, SubjectInput, LessonInput, StudentUpdateIn, ContactRequestIn
from .auth import hash_password, verify_password, create_token, current_user, admin_user
from .seed import seed

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Adaptive AI Tutor", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    db = next(get_db())
    try:
        seed(db)
        email, password = os.getenv("ADMIN_EMAIL"), os.getenv("ADMIN_PASSWORD")
        if email and password and not db.query(User).filter(User.email == email.lower()).first():
            db.add(User(name="Administrator", email=email.lower(), password_hash=hash_password(password), role="admin", created_at=datetime.utcnow().isoformat()))
            db.commit()
    finally:
        db.close()

@app.get("/api/health")
def health():
    return {"status": "ok", "ai_configured": bool(os.getenv("LLM_BASE_URL")), "ai_model": os.getenv("LLM_MODEL", "")}

@app.post("/api/auth/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "An account with this email already exists")
    user = User(name=data.name.strip(), email=email, password_hash=hash_password(data.password), role=data.role, created_at=datetime.utcnow().isoformat())
    db.add(user); db.commit(); db.refresh(user)
    return {"token": create_token(user), "user": user_out(user)}

def user_out(user):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}

@app.post("/api/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect")
    return {"token": create_token(user), "user": user_out(user)}

@app.get("/api/auth/me")
def me(user=Depends(current_user)):
    return user_out(user)

@app.get("/api/subjects")
def subjects(db: Session = Depends(get_db), user=Depends(current_user)):
    out=[]
    for subject in db.query(Subject).order_by(Subject.id).all():
        total = db.query(Lesson).filter(Lesson.subject_id == subject.id).count()
        done = db.query(LessonCompletion).join(Lesson).filter(LessonCompletion.user_id == user.id, Lesson.subject_id == subject.id).count()
        out.append({"id":subject.id,"name":subject.name,"description":subject.description,"icon":subject.icon,"lesson_count":total,"completed":done,"progress":round(done*100/total) if total else 0})
    return out

@app.get("/api/subjects/{subject_id}/lessons")
def lessons(subject_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject: raise HTTPException(404, "Subject not found")
    done = set(x[0] for x in db.query(LessonCompletion.lesson_id).filter(LessonCompletion.user_id == user.id).all())
    attempts = db.query(Attempt).filter(Attempt.user_id == user.id, Attempt.subject_id == subject_id).order_by(Attempt.id.desc()).all()
    best = max([a.percentage for a in attempts], default=None)
    lessons = db.query(Lesson).filter(Lesson.subject_id == subject_id).order_by(Lesson.month, Lesson.week).all()
    result=[]
    for l in lessons:
        unlocked = l.month <= 3 if best is None else (l.month <= 1 if best < 50 else (l.month <= 6 if best <= 75 else True))
        result.append({"id":l.id,"month":l.month,"week":l.week,"title":l.title,"content":l.content,"example":l.example,"exercise":l.exercise,"level":l.level,"completed":l.id in done,"unlocked":unlocked})
    return {"subject":{"id":subject.id,"name":subject.name,"icon":subject.icon},"lessons":result}

@app.post("/api/lessons/{lesson_id}/complete")
def complete_lesson(lesson_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    lesson=db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson: raise HTTPException(404,"Lesson not found")
    if not db.query(LessonCompletion).filter_by(user_id=user.id,lesson_id=lesson_id).first():
        db.add(LessonCompletion(user_id=user.id,lesson_id=lesson_id))
        subject=db.query(Subject).filter(Subject.id == lesson.subject_id).first()
        notify_contacts(db,user,"lesson", "Lesson completed", "%s completed %s in %s." % (user.name,lesson.title,subject.name))
        db.commit()
    return {"completed": True}

@app.get("/api/subjects/{subject_id}/quiz")
def quiz(subject_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    subject=db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject: raise HTTPException(404,"Subject not found")
    questions=db.query(Question).filter(Question.subject_id == subject_id).order_by(Question.id).all()
    previous=db.query(Attempt).filter_by(user_id=user.id,subject_id=subject_id).order_by(Attempt.id.desc()).first()
    if previous and previous.percentage < 50:
        recommendation="Revision recommended: revisit the month 1 review lesson before trying again."
    elif previous and previous.percentage <= 75:
        recommendation="You are building confidence. Complete another practice round to strengthen recall."
    elif previous:
        recommendation="Great work. Try the advanced lessons and explain each answer in your own words."
    else: recommendation="Take this short check to get your personalized next step."
    return {"subject_id":subject_id,"subject":subject.name,"recommendation":recommendation,"questions":[{"id":q.id,"prompt":q.prompt,"options":json.loads(q.options)} for q in questions]}

@app.post("/api/quiz/submit")
def submit_quiz(data: QuizIn, db: Session = Depends(get_db), user=Depends(current_user)):
    subject=db.query(Subject).filter(Subject.id == data.subject_id).first()
    if not subject: raise HTTPException(404,"Subject not found")
    questions=db.query(Question).filter(Question.subject_id == data.subject_id).order_by(Question.id).all()
    if not questions: raise HTTPException(404,"No quiz available for this subject")
    if len(data.answers) != len(questions): raise HTTPException(400,"Submit one answer for every question")
    score, percentage, grade = calculate_grade([q.answer for q in questions], data.answers)
    attempt=Attempt(user_id=user.id,subject_id=subject.id,score=score,total=len(questions),percentage=percentage,grade=grade,answers=json.dumps(data.answers),created_at=datetime.utcnow().isoformat())
    db.add(attempt)
    notify_contacts(db,user,"quiz", "Quiz result: %s%% (%s)" % (percentage,grade), "%s scored %s%% (%s/%s) in %s." % (user.name,percentage,score,len(questions),subject.name))
    db.commit(); db.refresh(attempt)
    feedback=[]
    for q,a in zip(questions,data.answers):
        feedback.append({"question_id":q.id,"correct":a==q.answer,"correct_answer":q.answer,"your_answer":a,"explanation":q.explanation})
    next_step="Revise foundational lessons and retry an easier practice set." if percentage<50 else "Practice a few more examples to reinforce the concepts." if percentage<=75 else "Advanced lessons are ready. Try a harder challenge next."
    return {"id":attempt.id,"score":score,"total":len(questions),"percentage":percentage,"grade":grade,"feedback":feedback,"next_step":next_step}

def calculate_grade(correct_answers, answers):
    score = sum(1 for correct, answer in zip(correct_answers, answers) if answer == correct)
    percentage = round(score * 100.0 / len(correct_answers), 1) if correct_answers else 0
    grade = "A" if percentage >= 90 else "B" if percentage >= 80 else "C" if percentage >= 70 else "D" if percentage >= 60 else "F"
    return score, percentage, grade

@app.get("/api/results")
def results(db: Session = Depends(get_db), user=Depends(current_user)):
    attempts=db.query(Attempt).filter(Attempt.user_id == user.id).order_by(Attempt.id.desc()).all()
    return [{"id":a.id,"subject":db.query(Subject).get(a.subject_id).name,"subject_id":a.subject_id,"score":a.score,"total":a.total,"percentage":a.percentage,"grade":a.grade,"created_at":a.created_at} for a in attempts]

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db), user=Depends(current_user)):
    all_lessons=db.query(Lesson).count(); completed=db.query(LessonCompletion).filter_by(user_id=user.id).count()
    attempts=db.query(Attempt).filter_by(user_id=user.id).order_by(Attempt.id.desc()).all()
    subjects_total=db.query(Subject).count()
    latest=[]
    for a in attempts[:5]: latest.append({"subject":db.query(Subject).get(a.subject_id).name,"percentage":a.percentage,"grade":a.grade,"created_at":a.created_at})
    return {"student":user_out(user),"lessons_completed":completed,"lessons_total":all_lessons,"completion":round(completed*100/all_lessons) if all_lessons else 0,"subjects_count":subjects_total,"quiz_count":len(attempts),"average_score":round(sum(a.percentage for a in attempts)/len(attempts)) if attempts else 0,"recent_results":latest}

@app.get("/api/profile")
def profile(user=Depends(current_user)):
    return user_out(user)

def notify_contacts(db, student, event, title, body):
    links=db.query(StudentContact).filter_by(student_id=student.id,approved=True).all()
    now=datetime.utcnow().isoformat()
    for link in links:
        db.add(Notification(recipient_id=link.contact_id,student_id=student.id,event=event,title=title,body=body,created_at=now))

@app.post("/api/contacts/request")
def request_contact(data: ContactRequestIn, db: Session = Depends(get_db), user=Depends(current_user)):
    if user.role != "student": raise HTTPException(403,"Only students can invite a parent or teacher")
    contact=db.query(User).filter(User.email == data.email.lower(),User.role == data.role).first()
    if not contact: raise HTTPException(404,"Create the parent/teacher account first, then invite their registered email")
    existing=db.query(StudentContact).filter_by(student_id=user.id,contact_id=contact.id).first()
    if existing: raise HTTPException(409,"This account is already linked or has a pending request")
    now=datetime.utcnow().isoformat()
    link=StudentContact(student_id=user.id,contact_id=contact.id,contact_role=contact.role,approved=False,created_at=now)
    db.add(link); db.flush()
    db.add(Notification(recipient_id=contact.id,student_id=user.id,event="link_request",title="Student link request",body="%s asked to share learning progress with you. Review and accept to receive updates." % user.name,created_at=now))
    db.commit()
    return {"id":link.id,"status":"pending","contact":user_out(contact)}

@app.post("/api/contacts/{link_id}/approve")
def approve_contact(link_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    link=db.query(StudentContact).filter_by(id=link_id,contact_id=user.id).first()
    if not link: raise HTTPException(404,"Contact request not found")
    link.approved=True
    db.query(Notification).filter_by(recipient_id=user.id,student_id=link.student_id,event="link_request",is_read=False).update({"is_read":True},synchronize_session=False)
    student=db.query(User).filter(User.id == link.student_id).first()
    db.add(Notification(recipient_id=student.id,student_id=student.id,event="link_approved",title="Progress sharing enabled",body="%s accepted your progress-sharing request." % user.name,created_at=datetime.utcnow().isoformat()))
    db.commit()
    return {"approved":True,"student":user_out(student)}

@app.get("/api/contacts")
def contacts(db: Session = Depends(get_db), user=Depends(current_user)):
    if user.role == "student":
        links=db.query(StudentContact).filter_by(student_id=user.id).all()
        return [{"id":x.id,"name":db.query(User).get(x.contact_id).name,"email":db.query(User).get(x.contact_id).email,"role":x.contact_role,"approved":x.approved} for x in links]
    if user.role in ("teacher","parent"):
        links=db.query(StudentContact).filter_by(contact_id=user.id,approved=True).all()
        return [{"id":x.id,"student":user_out(db.query(User).get(x.student_id))} for x in links]
    return []

@app.get("/api/relationships")
def relationships(db: Session = Depends(get_db), user=Depends(current_user)):
    if user.role not in ("teacher","parent"): raise HTTPException(403,"This view is for linked parents and teachers")
    links=db.query(StudentContact).filter_by(contact_id=user.id,approved=True).all()
    result=[]
    for link in links:
        student=db.query(User).get(link.student_id)
        attempts=db.query(Attempt).filter_by(user_id=student.id).order_by(Attempt.id.desc()).limit(5).all()
        completed=db.query(LessonCompletion).filter_by(user_id=student.id).count()
        result.append({"student":user_out(student),"lessons_completed":completed,"recent_results":[{"subject":db.query(Subject).get(a.subject_id).name,"percentage":a.percentage,"grade":a.grade,"created_at":a.created_at} for a in attempts]})
    return result

@app.get("/api/notifications")
def get_notifications(db: Session = Depends(get_db), user=Depends(current_user)):
    rows=db.query(Notification).filter_by(recipient_id=user.id).order_by(Notification.id.desc()).limit(100).all()
    return [{"id":n.id,"student":db.query(User).get(n.student_id).name,"student_id":n.student_id,"event":n.event,"title":n.title,"body":n.body,"is_read":n.is_read,"created_at":n.created_at,"link_id":(db.query(StudentContact).filter_by(student_id=n.student_id,contact_id=user.id).first().id if n.event=="link_request" and db.query(StudentContact).filter_by(student_id=n.student_id,contact_id=user.id).first() else None)} for n in rows]

@app.post("/api/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    row=db.query(Notification).filter_by(id=notification_id,recipient_id=user.id).first()
    if not row: raise HTTPException(404,"Notification not found")
    row.is_read=True; db.commit()
    return {"read":True}

def fallback_answer(message, subject):
    text=message.strip()
    low=text.lower()
    if any(x in low for x in ("solve", "equation", "math", "calculate")):
        reply="Local study guide (no AI model connected):\n1. Write down what is known and what you need to find.\n2. Choose a rule that links them.\n3. Substitute one step at a time and keep units.\n4. Check the result in the original question.\n\nShare the exact problem and I can help you set up the steps."
    elif any(x in low for x in ("python", "code", "error", "java", "c program")):
        reply="Local study guide (no AI model connected):\nRead the error message from the first line, inspect the named line and nearby values, then reduce the code to a tiny reproducible example. Trace variable values by hand.\n\nPaste a short snippet and its error; configure an LLM endpoint for tailored code explanations."
    elif "hint" in low or "answer" in low:
        reply="Local study guide (no AI model connected): start by naming the concept involved, then write what you already know. Try one small case and compare it with the definition before revealing a final answer."
    else:
        reply="Local study guide (no AI model connected): break the topic into a definition, a worked example, and one practice problem. Explain why each step is valid.\n\nSet LLM_BASE_URL, LLM_API_KEY, and LLM_MODEL in backend/.env to connect an OpenAI-compatible service such as local Ollama."
    return {"reply":reply,"mode":"local-fallback","disclaimer":"This response was generated by the built-in study guide, not an AI model."}

def verified_tutor_facts(subject, message):
    text=message.lower()
    if subject == "Python Programming" and any(term in text for term in ("for loop","for-loop","empty list","loop")):
        return "Verified Python loop behavior: `for item in iterable` asks the iterable for its next item on each pass. It does not test `item` for truthiness. An empty iterable runs the loop body zero times. A `while` loop, by contrast, repeats while its Boolean condition is true."
    if subject in ("C Programming","Java Programming") and any(term in text for term in ("for loop","for-loop","empty array","loop")):
        return "Verified loop behavior: a loop iterates according to its control expression or iterable. A normal for loop does not test each item for truthiness. An empty range or array produces zero body executions."
    return ""

@app.post("/api/chat")
async def chat(data: ChatIn, db: Session = Depends(get_db), user=Depends(current_user)):
    base=os.getenv("LLM_BASE_URL"); key=os.getenv("LLM_API_KEY", ""); model=os.getenv("LLM_MODEL", "")
    if not base or not model: return fallback_answer(data.message,data.subject)
    system="You are a patient college tutor. Explain in simple English, reason step-by-step for math, help debug code, give hints before full solutions, and keep answers safe and concise. Ground course answers in the provided lesson notes. Do not invent facts; if the notes do not cover something, say so and explain what is known. For code, use valid syntax and explain the output."
    try:
        subject_row=db.query(Subject).filter(Subject.name.ilike(data.subject)).first() if data.subject else None
        words=[w for w in dict.fromkeys(re.findall(r"[a-zA-Z]{3,}",data.message.lower())) if w not in {"the","and","for","this","that","with","what","when","where","which","could","would","should","please","explain","simply","simple","about","help","give","show","tell","from","into","your","have","does","make","step","steps"}][:6]
        lesson_query=db.query(Lesson)
        if subject_row: lesson_query=lesson_query.filter(Lesson.subject_id == subject_row.id)
        if words:
            matches=[Lesson.title.ilike("%%%s%%" % w) | Lesson.content.ilike("%%%s%%" % w) for w in words]
            lesson_query=lesson_query.filter(or_(*matches))
        notes=lesson_query.order_by(Lesson.month,Lesson.week).limit(2).all()
        context="\n\nRelevant curriculum notes:\n" + "\n".join("- %s: %s Example: %s" % (lesson.title,lesson.content[:700],lesson.example[:400]) for lesson in notes) if notes else ""
        verified=verified_tutor_facts(subject_row.name if subject_row else data.subject,data.message)
        if verified: context += "\n\nVerified reference facts (follow these exactly): " + verified
        messages=[{"role":"system","content":system + (" Current subject: " + data.subject if data.subject else "") + context}]
        messages.extend([{"role":turn.role,"content":turn.content} for turn in data.history[-8:]])
        messages.append({"role":"user","content":data.message})
        base=base.rstrip("/")
        native_ollama=":11434" in base and not base.endswith("/v1")
        if native_ollama:
            url=base + ("/chat" if base.endswith("/api") else "/api/chat")
            headers={}
            payload={"model":model,"messages":messages,"stream":False,"options":{"temperature":0.2,"num_predict":512}}
        else:
            url=base if base.endswith("/chat/completions") else base + "/chat/completions"
            headers={"Authorization":"Bearer " + key} if key else {}
            payload={"model":model,"messages":messages,"temperature":0.2,"max_tokens":512}
        async with httpx.AsyncClient(timeout=45) as client:
            response=await client.post(url,headers=headers,json=payload)
        response.raise_for_status()
        body=response.json()
        answer=body.get("message",{}).get("content") if native_ollama else body.get("choices",[{}])[0].get("message",{}).get("content")
        if not answer: raise ValueError("AI provider returned an empty answer")
        return {"reply":answer,"mode":"llm","model":model}
    except Exception as exc:
        message = "The configured AI service is unavailable. Check the backend connection and model settings."
        fallback = fallback_answer(data.message, data.subject)
        return {"error":message,"detail":str(exc)[:240],"reply":message + "\n\nLocal study guide (not AI): " + fallback["reply"],"mode":"error"}

@app.get("/api/admin/overview")
def admin_overview(db: Session = Depends(get_db), user=Depends(admin_user)):
    students=db.query(User).filter(User.role=="student").all()
    return {"students":[user_out(s) for s in students],"subjects":db.query(Subject).count(),"lessons":db.query(Lesson).count(),"attempts":db.query(Attempt).count(),"recent_attempts":[{"student":db.query(User).get(a.user_id).name,"subject":db.query(Subject).get(a.subject_id).name,"percentage":a.percentage,"created_at":a.created_at} for a in db.query(Attempt).order_by(Attempt.id.desc()).limit(10).all()]}

@app.get("/api/admin/subjects")
def admin_subjects(db: Session = Depends(get_db), user=Depends(admin_user)):
    return [{"id":s.id,"name":s.name,"description":s.description,"icon":s.icon} for s in db.query(Subject).all()]

@app.post("/api/admin/subjects")
def create_subject(data: SubjectInput, db: Session = Depends(get_db), user=Depends(admin_user)):
    name=data.name.strip()
    if db.query(Subject).filter(Subject.name == name).first():
        raise HTTPException(409, "A subject with this name already exists")
    subject=Subject(name=name,description=data.description.strip(),icon=data.icon)
    db.add(subject); db.commit(); db.refresh(subject)
    return {"id":subject.id,"name":subject.name,"description":subject.description,"icon":subject.icon}

@app.put("/api/admin/subjects/{subject_id}")
def update_subject(subject_id: int, data: SubjectInput, db: Session = Depends(get_db), user=Depends(admin_user)):
    subject=db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject: raise HTTPException(404, "Subject not found")
    name=data.name.strip()
    other=db.query(Subject).filter(Subject.name == name, Subject.id != subject_id).first()
    if other: raise HTTPException(409, "A subject with this name already exists")
    subject.name=name; subject.description=data.description.strip(); subject.icon=data.icon; db.commit()
    return {"id":subject.id,"name":subject.name,"description":subject.description,"icon":subject.icon}

@app.post("/api/admin/subjects/{subject_id}/lessons")
def create_lesson(subject_id: int, data: LessonInput, db: Session = Depends(get_db), user=Depends(admin_user)):
    if not db.query(Subject).filter(Subject.id == subject_id).first(): raise HTTPException(404, "Subject not found")
    lesson=Lesson(subject_id=subject_id,month=data.month,week=data.week,title=data.title.strip(),content=data.content.strip(),example=data.example.strip(),exercise=data.exercise.strip(),level=data.level)
    db.add(lesson); db.commit(); db.refresh(lesson)
    return {"id":lesson.id,"subject_id":lesson.subject_id,"month":lesson.month,"week":lesson.week,"title":lesson.title}

@app.put("/api/admin/lessons/{lesson_id}")
def update_lesson(lesson_id: int, data: LessonInput, db: Session = Depends(get_db), user=Depends(admin_user)):
    lesson=db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson: raise HTTPException(404, "Lesson not found")
    for field in ("month","week","title","content","example","exercise","level"):
        value=getattr(data,field)
        setattr(lesson,field,value.strip() if isinstance(value,str) else value)
    db.commit()
    return {"id":lesson.id,"subject_id":lesson.subject_id,"month":lesson.month,"week":lesson.week,"title":lesson.title}

@app.put("/api/admin/students/{student_id}")
def update_student(student_id: int, data: StudentUpdateIn, db: Session = Depends(get_db), user=Depends(admin_user)):
    student=db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student: raise HTTPException(404, "Student not found")
    email=data.email.lower()
    if db.query(User).filter(User.email == email, User.id != student_id).first():
        raise HTTPException(409, "That email is already in use")
    student.name=data.name.strip(); student.email=email; db.commit()
    return user_out(student)

@app.delete("/api/admin/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db), user=Depends(admin_user)):
    student=db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student: raise HTTPException(404, "Student not found")
    db.query(Attempt).filter(Attempt.user_id == student_id).delete(synchronize_session=False)
    db.query(LessonCompletion).filter(LessonCompletion.user_id == student_id).delete(synchronize_session=False)
    db.query(StudentContact).filter(or_(StudentContact.student_id == student_id,StudentContact.contact_id == student_id)).delete(synchronize_session=False)
    db.query(Notification).filter(or_(Notification.recipient_id == student_id,Notification.student_id == student_id)).delete(synchronize_session=False)
    db.delete(student); db.commit()
    return {"deleted":True,"student_id":student_id}

@app.get("/")
def root():
    index = Path(__file__).resolve().parents[2] / "frontend" / "dist" / "index.html"
    if index.exists(): return FileResponse(index)
    return {"message":"Adaptive AI Tutor API","docs":"/docs"}

frontend=Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend.exists(): app.mount("/", StaticFiles(directory=str(frontend), html=True), name="frontend")
