from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, BigInteger, Column, Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Boolean, Column

class EntryStatus(str, Enum):
    """Enumeration for state of journal entry."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class UserRole(int, Enum):
    """Enumeration for user roles."""

    USER = 0
    PREMIUM_USER = 1
    ADMIN = 2


# Forward declaration for relationships
class JournalEntry: ...


class UserBadge: ...


class Streak: ...


class UserPrompt: ...


class AIResponse: ...


class Badge: ...


class User(SQLModel, table=True):
    """User model representing app users."""

    __tablename__ = "user"

    user_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BigInteger, primary_key=True, index=True, autoincrement=True
        ),  # autoincrement=True is default for PK
    )
    name: str = Field(sa_column=Column(String(255), nullable=False))
    email: str = Field(
        sa_column=Column(String(255), unique=True, index=True, nullable=False)
    )
    password_hash: str = Field(sa_column=Column(String(255), nullable=False))
    background_info: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    role: int = Field(
        default=UserRole.USER.value,
        sa_column=Column(Integer, default=UserRole.USER.value, nullable=False),
    )
    avatar_url: Optional[str] = Field(
        default=None, sa_column=Column(String(500), nullable=True)
    )
    preferences: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,  # For Pydantic model
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,  # For Pydantic model
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )
    last_login: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    # Relationships
    journal_entries: List["JournalEntry"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    user_badges: List["UserBadge"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    streak: Optional["Streak"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )
    sessions: List["Session"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, email='{self.email}')>"

class Session(SQLModel, table=True):
    """Represents a user session for a logged-in device."""

    __tablename__ = "session"

    id: Optional[int] = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, index=True)
    )
    user_id: int = Field(
        sa_column=Column(
            BigInteger, ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False
        )
    )
    token: str = Field(
        sa_column=Column(String(512), unique=True, index=True, nullable=False)
    )
    issued_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    revoked: bool = Field(
        default=False, sa_column=Column(Boolean, default=False, nullable=False)
    )
    device_info: Optional[str] = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )
    ip_address: Optional[str] = Field(
        default=None, sa_column=Column(String(100), nullable=True)
    )

    # Relationship to User
    user: "User" = Relationship(back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id}, revoked={self.revoked})>"

class Badge(SQLModel, table=True):
    """Badge model representing achievements users can earn."""

    __tablename__ = "badge"

    badges_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, index=True, autoincrement=True),
    )
    description: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    condition_type: str = Field(sa_column=Column(String(100), nullable=False))
    condition_value: int = Field(sa_column=Column(Integer, nullable=False))
    image_url: Optional[str] = Field(
        default=None, sa_column=Column(String(500), nullable=True)
    )

    # Relationships
    user_badges: List["UserBadge"] = Relationship(
        back_populates="badge", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    def __repr__(self) -> str:
        return f"<Badge(badges_id={self.badges_id}, condition_type='{self.condition_type}')>"


class UserBadge(SQLModel, table=True):
    """Junction table for many-to-many relationship between users and badges."""

    __tablename__ = "user_badge"

    user_badge_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, index=True, autoincrement=True),
    )
    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("user.user_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    badges_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("badge.badges_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    earned_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
    )

    # Relationships
    user: Optional["User"] = Relationship(back_populates="user_badges")
    badge: Optional["Badge"] = Relationship(back_populates="user_badges")

    def __repr__(self) -> str:
        return f"<UserBadge(user_id={self.user_id}, badges_id={self.badges_id})>"


class Streak(SQLModel, table=True):
    """Streak model tracking user's journaling consistency."""

    __tablename__ = "streak"

    streak_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, index=True, autoincrement=True),
    )
    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("user.user_id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
            index=True,
        )
    )
    current_streak: int = Field(
        default=0, sa_column=Column(Integer, default=0, nullable=False)
    )
    longest_streak: int = Field(
        default=0, sa_column=Column(Integer, default=0, nullable=False)
    )
    last_entry_date: Optional[date] = Field(
        default=None, sa_column=Column(Date, nullable=True)
    )

    # Relationships
    user: Optional["User"] = Relationship(back_populates="streak")

    def __repr__(self) -> str:
        return f"<Streak(user_id={self.user_id}, current={self.current_streak})>"


class JournalEntry(SQLModel, table=True):
    """Journal entry model representing user's daily journal entries."""

    __tablename__ = "journal_entry"

    journal_entry_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, index=True, autoincrement=True),
    )
    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("user.user_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    entry_date: date = Field(sa_column=Column(Date, nullable=False, index=True))
    text: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    sentiment_score: Optional[int] = Field(
        default=None, sa_column=Column(SmallInteger, nullable=True)
    )
    ai_suggestion: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    chat_log: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    entry_status: Optional[EntryStatus] = Field(
        default=None, sa_column=Column(SQLEnum(EntryStatus), nullable=True)
    )
    word_count: int = Field(
        default=0, sa_column=Column(Integer, default=0, nullable=False)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )

    # Relationships
    user: Optional["User"] = Relationship(back_populates="journal_entries")
    user_prompts: List["UserPrompt"] = Relationship(
        back_populates="journal_entry",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    def __repr__(self) -> str:
        return f"<JournalEntry(id={self.journal_entry_id}, date={self.entry_date})>"


class AIResponse(SQLModel, table=True):
    """AI response model storing AI-generated responses."""

    __tablename__ = "ai_response"

    ai_response_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, index=True, autoincrement=True),
    )
    response_text: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )

    # Relationships
    user_prompts: List["UserPrompt"] = Relationship(back_populates="ai_response")

    def __repr__(self) -> str:
        return f"<AIResponse(id={self.ai_response_id})>"


class UserPrompt(SQLModel, table=True):
    """User prompt model for AI-generated prompts and responses."""

    __tablename__ = "user_prompt"

    user_prompt_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, index=True, autoincrement=True),
    )
    journal_entry_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("journal_entry.journal_entry_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    prompt_id: int = Field(sa_column=Column(BigInteger, nullable=False, index=True))
    prompt_text: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    ai_response_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            ForeignKey("ai_response.ai_response_id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    completed_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    # Relationships
    journal_entry: Optional["JournalEntry"] = Relationship(
        back_populates="user_prompts"
    )
    ai_response: Optional["AIResponse"] = Relationship(back_populates="user_prompts")

    def __repr__(self) -> str:
        return f"<UserPrompt(id={self.user_prompt_id}, journal_entry_id={self.journal_entry_id})>"


# Type aliases for better code readability
UserID = int
BadgeID = int
JournalEntryID = int
StreakID = int
