from sqlalchemy import (
    Column,
    String,
    BigInteger,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Poll(Base):
    """Represents a specific poll instance sent to a chat."""
    __tablename__ = 'polls'
    
    id = Column(String, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=False, unique=True)
    
    # Change this line to use timezone-aware timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    votes = relationship("Vote", back_populates="poll", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Poll(id='{self.id}', chat_id={self.chat_id}, created_at='{self.created_at}')>"

class Vote(Base):
    """
    Represents a single vote, linking a user's ID, name, and handle to a Poll for one option.
    """
    __tablename__ = 'votes'

    # Composite primary key to ensure a user's vote is unique per option
    poll_id = Column(String, ForeignKey('polls.id'), primary_key=True)
    user_id = Column(BigInteger, primary_key=True)
    option_text = Column(String, primary_key=True)
    
    # User details are stored directly in the vote record
    user_first_name = Column(String, nullable=False)
    # The user's Telegram handle (@username). Can be NULL.
    user_username = Column(String, nullable=True) 

    # Relationship to get the parent poll object from a vote instance
    poll = relationship("Poll", back_populates="votes")

    def __repr__(self):
        return f"<Vote(user_id={self.user_id}, name='{self.user_first_name}', username='{self.user_username}', option='{self.option_text}')>"