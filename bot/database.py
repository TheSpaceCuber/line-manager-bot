# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, delete
from datetime import datetime, timedelta
from typing import List, Optional
import pytz
from bot.config import Config
from bot.schema import Base, Poll, Vote
import re

db_url = Config.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Remove sslmode and channel_binding parameters (asyncpg doesn't accept these)
db_url = re.sub(r'[?&]sslmode=[^&]*', '', db_url)
db_url = re.sub(r'[?&]channel_binding=[^&]*', '', db_url)
db_url = re.sub(r'[?&]$', '', db_url)  # Clean up trailing ? or &

# Create async engine with proper Lambda configuration
engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    connect_args={"ssl": "require"},  # SSL for Neon
    pool_pre_ping=True,    # Verify connections before using
    pool_size=1,           # Lambda = single concurrent execution
    max_overflow=0,        # No overflow for Lambda
    pool_recycle=3600      # Recycle connections after 1 hour
)
# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Singapore timezone
SGT = pytz.timezone('Asia/Singapore')


# Flag to track initialization
_db_initialized = False

async def init_db():
    """Initialize the database by creating all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 
               
async def ensure_db_initialized():
    """Ensure database is initialized before any operation."""
    global _db_initialized
    if not _db_initialized:
        await init_db()
        _db_initialized = True

async def get_week_bounds(reference_date: datetime = datetime.now(SGT)) -> tuple[datetime, datetime]:
    """
    Get the start (Sunday 00:00) and end (Saturday 23:59:59) of the week
    for a given reference date in SGT timezone.
    
    Args:
        reference_date: The date to get week bounds for. Defaults to now.
    
    Returns:
        Tuple of (week_start, week_end) as timezone-aware datetime objects
    """
    if reference_date is None:
        reference_date = datetime.now(SGT)
    elif reference_date.tzinfo is None:
        reference_date = SGT.localize(reference_date)
    else:
        reference_date = reference_date.astimezone(SGT)
    
    # Find the most recent Sunday (or today if it's Sunday)
    days_since_sunday = reference_date.weekday()
    if days_since_sunday == 6:  # Sunday
        days_to_subtract = 0
    else:
        days_to_subtract = days_since_sunday + 1
    
    week_start = reference_date - timedelta(days=days_to_subtract)
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Week ends on Saturday 23:59:59
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    return week_start, week_end


async def save_poll(poll_id: str, chat_id: int, message_id: int) -> Poll:
    """
    Save a new poll to the database.
    
    Args:
        poll_id: The unique Telegram poll ID
        chat_id: The chat where the poll was sent
        message_id: The message ID of the poll
    
    Returns:
        The created Poll object
    """
    await ensure_db_initialized()  
    async with AsyncSessionLocal() as session:
        poll = Poll(
            id=poll_id,
            chat_id=chat_id,
            message_id=message_id
        )
        session.add(poll)
        await session.commit()
        await session.refresh(poll)
        return poll


async def get_current_week_poll(chat_id: int) -> Optional[Poll]:
    """
    Get the poll for the current week (Sunday-Saturday) in a specific chat.
    
    Args:
        chat_id: The chat ID to search in
    
    Returns:
        Poll object if found, None otherwise
    """
    await ensure_db_initialized()  
    week_start, week_end = await get_week_bounds()
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Poll)
            .where(
                Poll.chat_id == chat_id,
                Poll.created_at >= week_start,
                Poll.created_at <= week_end
            )
            .order_by(Poll.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


async def save_votes(poll_id: str, user_id: int, user_first_name: str, 
                     user_username: Optional[str], option_texts: List[str]) -> List[Vote]:
    """
    Save all votes from a user for a poll. This will first remove any existing
    votes from this user for this poll, then add the new votes.
    
    Args:
        poll_id: The poll ID
        user_id: The user's Telegram ID
        user_first_name: The user's first name
        user_username: The user's username (without @), can be None
        option_texts: List of option texts the user voted for
    
    Returns:
        List of created Vote objects
    """
    await ensure_db_initialized()  
    async with AsyncSessionLocal() as session:
        # First, remove all existing votes from this user for this poll
        await session.execute(
            delete(Vote).where(
                Vote.poll_id == poll_id,
                Vote.user_id == user_id
            )
        )
        
        # Then add the new votes
        votes = []
        for option_text in option_texts:
            vote = Vote(
                poll_id=poll_id,
                user_id=user_id,
                option_text=option_text,
                user_first_name=user_first_name,
                user_username=user_username
            )
            session.add(vote)
            votes.append(vote)
        
        await session.commit()
        
        # Refresh all votes to get any server-side defaults
        for vote in votes:
            await session.refresh(vote)
        
        return votes


async def remove_user_votes(poll_id: str, user_id: int) -> int:
    """
    Remove all votes from a specific user for a specific poll.
    
    Args:
        poll_id: The poll ID
        user_id: The user's Telegram ID
    
    Returns:
        Number of votes deleted
    """
    await ensure_db_initialized()  
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            delete(Vote).where(
                Vote.poll_id == poll_id,
                Vote.user_id == user_id
            )
        )
        await session.commit()
        return result.rowcount


async def get_poll_votes(poll_id: str) -> List[Vote]:
    """
    Get all votes for a specific poll, ordered by option and user name.
    
    Args:
        poll_id: The poll ID
    
    Returns:
        List of Vote objects
    """
    await ensure_db_initialized()  
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Vote)
            .where(Vote.poll_id == poll_id)
            .order_by(Vote.option_text, Vote.user_first_name)
        )
        votes = result.scalars().all()
        
        # Return a list copy since the session will close
        return list(votes)


async def get_poll_by_id(poll_id: str) -> Optional[Poll]:
    """
    Get a poll by its ID.
    
    Args:
        poll_id: The poll ID
    
    Returns:
        Poll object if found, None otherwise
    """
    await ensure_db_initialized()  
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Poll).where(Poll.id == poll_id)
        )
        return result.scalar_one_or_none()