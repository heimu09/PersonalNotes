from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from . import models, schemas, crud, auth
from .database import get_db
from datetime import timedelta
from typing import List

app = FastAPI()


@app.post("/register/", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.post("/token", response_model=dict)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/notes/", response_model=schemas.Note)
def create_note(note: schemas.NoteCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    return crud.create_note(db=db, note=note, user_id=current_user.id)

@app.get("/notes/", response_model=List[schemas.Note])
def read_notes(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    notes = crud.get_notes_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return notes

@app.put("/notes/{note_id}", response_model=schemas.Note)
def update_note(note_id: int, note: schemas.NoteUpdate, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    db_note = crud.get_note_by_id(db, note_id=note_id)
    if db_note is None or db_note.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")
    return crud.update_note(db=db, note_id=note_id, note=note)

@app.delete("/notes/{note_id}", response_model=schemas.Note)
def delete_note(note_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    db_note = crud.get_note_by_id(db, note_id=note_id)
    if db_note is None or db_note.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")
    return crud.delete_note(db=db, note_id=note_id)

@app.get("/notes/search/", response_model=List[schemas.Note])
async def search_notes_by_tags(tags: str, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    tags_list = tags.split(",")
    notes = crud.get_notes_by_tags(db, user_id=current_user.id, tags=tags_list)
    if not notes:
        raise HTTPException(status_code=404, detail="Заметки не найдены")
    return notes
