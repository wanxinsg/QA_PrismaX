"""Pydantic request/response models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ---------- users / auth ----------
class UserOut(BaseModel):
    id: int
    name: str
    initials: str
    email: Optional[str] = None
    avatar_color: Optional[str] = None


class DemoLoginIn(BaseModel):
    # Either pick a preset persona by external_id, or supply a free-form name.
    external_id: Optional[str] = None
    name: Optional[str] = Field(default=None, max_length=120)


# ---------- blocks (editor body) ----------
class Block(BaseModel):
    type: Literal["p", "h2", "quote", "bullet", "code", "divider", "image"]
    html: str = ""
    text: str = ""
    caption: str = ""
    src: Optional[str] = None


# ---------- threads ----------
class ThreadBase(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    category: str = Field(default="Discourse", max_length=80)
    excerpt: str = ""
    cover_image: Optional[str] = None
    content: list[Block] = Field(default_factory=list)


class ThreadCreate(ThreadBase):
    status: Literal["draft", "published"] = "published"


class ThreadUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=300)
    category: Optional[str] = Field(default=None, max_length=80)
    excerpt: Optional[str] = None
    cover_image: Optional[str] = None
    content: Optional[list[Block]] = None
    status: Optional[Literal["draft", "published"]] = None


class ThreadCard(BaseModel):
    """Compact shape used by the list view."""

    id: int
    title: str
    excerpt: str
    category: str
    cover_image: Optional[str] = None
    author: UserOut
    accent: bool = False
    badge: Optional[str] = None
    status: str
    date: str            # human label, e.g. "Oct 24"
    created_at: datetime
    comment_count: int
    like_count: int
    liked: bool = False
    saved: bool = False


class ThreadDetail(ThreadCard):
    content: list[Block]


class ThreadList(BaseModel):
    items: list[ThreadCard]
    total: int


# ---------- comments ----------
class CommentCreate(BaseModel):
    body: str = Field(min_length=1)
    parent_id: Optional[int] = None


class CommentOut(BaseModel):
    id: int
    body: str
    author: UserOut
    parent_id: Optional[int] = None
    created_at: datetime
    time: str            # human label, e.g. "2h ago"
    like_count: int
    liked: bool = False
    replies: list["CommentOut"] = Field(default_factory=list)


class ToggleResult(BaseModel):
    active: bool         # is the like/save now on?
    count: int           # resulting count (for likes)


class CategoryOut(BaseModel):
    label: str
    count: int


class Message(BaseModel):
    detail: str
