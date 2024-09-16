from sqlalchemy.orm import Session
from . import models, schemas, auth

def get_note_by_id(db: Session, note_id: int):
    return db.query(models.Note).filter(models.Note.id == note_id).first()

def get_notes(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Note).offset(skip).limit(limit).all()

def get_notes_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    return db.query(models.Note).filter(models.Note.owner_id == user_id).offset(skip).limit(limit).all()

def create_note(db: Session, note: schemas.NoteCreate, user_id: int):
    db_note = models.Note(title=note.title, content=note.content, tags=note.tags, owner_id=user_id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

def update_note(db: Session, note_id: int, note: schemas.NoteUpdate):
    db_note = get_note_by_id(db, note_id)
    if db_note:
        db_note.title = note.title
        db_note.content = note.content
        db_note.tags = note.tags
        db.commit()
        db.refresh(db_note)
    return db_note

def delete_note(db: Session, note_id: int):
    db_note = get_note_by_id(db, note_id)
    if db_note:
        db.delete(db_note)
        db.commit()
    return db_note

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_notes_by_tags(db: Session, user_id: int, tags: list):
    return db.query(models.Note).filter(
        models.Note.owner_id == user_id,
        models.Note.tags.op("&&")(tags)
    ).all()
