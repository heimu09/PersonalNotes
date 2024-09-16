from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class NoteBase(BaseModel):
    title: str
    content: str
    tags: List[str] = []

class NoteCreate(NoteBase):
    pass

class NoteUpdate(NoteBase):
    pass

class Note(NoteBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
