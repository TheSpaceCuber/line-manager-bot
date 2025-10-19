# Telegram Poll Bot - Requirements

## Overview
A Telegram bot that creates weekly training polls with vote tracking in a database. The bot supports both local development (SQLite + polling) and production deployment (PostgreSQL + webhooks on Vercel).

## Functional Requirements

### 1. Poll Creation (`/poll` command)
- **Trigger**: User sends `/poll` command in a chat
- **Poll Configuration**:
  - Title: "Weekly training"
  - Options: 
    1. "Thu 730pm @ YCK"
    2. "Sat 945am (Location TBC)"
    3. "Cmi"
  - Type: Multi-select (users can choose multiple options)
  - Anonymous: No (must track who voted)
- **Week Definition**: Sunday 00:00 to Saturday 23:59:59 (Singapore Time, UTC+8)
- **Constraint**: Only one poll can be created per week per chat
  - If a poll already exists for the current week, return: "Poll previously created"
  - Otherwise, create a new poll and store it in the database

### 2. Vote Tracking
- **On Vote Submission**: When a user votes (selects one or more options), store each vote in the database
- **On Vote Retraction**: When a user retracts their vote (Telegram removes ALL votes), delete all their votes from the database
- **On Vote Update**: When a user changes their vote:
  1. Telegram automatically retracts the old vote (removes all votes)
  2. User submits new vote
  3. Bot removes all old votes and adds new votes
- **Stored Information per Vote**:
  - Poll ID (foreign key to Poll table)
  - User ID
  - Option text
  - User first name
  - User username (nullable - can be empty if user has no @username)

### 3. Lines Display (`/lines` command)
- **Trigger**: User sends `/lines` command in a chat
- **Behavior**: Display all votes for the current week's poll
- **Output Format**:
  ```
  Thu 730pm @ YCK:
  - @username1 (John Doe)
  - @username2 (Jane Smith)
  
  Sat 945am (Location TBC):
  - @username1 (John Doe)
  - @username3 (Bob Lee)
  
  Cmi:
  - @username4 (Alice Tan)
  ```
- **Special Cases**:
  - If no poll exists for the current week: "Poll not yet created"
  - If poll exists but no votes: "No votes yet for this week's poll"
  - If user has no username: Display "No username" instead of "@username"

### 4. Error Handling
- All errors should be:
  1. Logged to the application logs with full stack trace
  2. Sent as user-friendly error messages to the chat
- Error message format: "Error [action]: [error description]"

## Technical Requirements

### Database Schema
Uses the provided SQLAlchemy models (`models.py`):

**Poll Table**:
- `id` (String, Primary Key): Telegram poll ID
- `chat_id` (BigInteger): Telegram chat ID
- `message_id` (BigInteger, Unique): Telegram message ID
- `created_at` (DateTime with timezone): Timestamp of poll creation (auto-generated)

**Vote Table**:
- `poll_id` (String, Foreign Key, Primary Key): References Poll.id
- `user_id` (BigInteger, Primary Key): Telegram user ID
- `option_text` (String, Primary Key): The text of the voted option
- `user_first_name` (String): User's first name
- `user_username` (String, Nullable): User's Telegram handle (@username)

Composite primary key: (poll_id, user_id, option_text) - ensures one vote per user per option per poll

### Environment Configuration

**Required Environment Variables**:
- `TELEGRAM_BOT_TOKEN`: Bot token from BotFather
- `ENVIRONMENT`: Either "local" or "production"

**Production-only Variables**:
- `WEBHOOK_URL`: Base URL for webhooks (e.g., https://yourdomain.vercel.app)
- `DATABASE_URL`: PostgreSQL connection string (Neon serverless)

**Optional Variables**:
- `PORT`: Webhook server port (default: 8443)

### Deployment Modes

**Local Development** (`ENVIRONMENT=local`):
- Database: SQLite (`polls.db` file)
- Update Mode: Polling (bot continuously checks for updates)
- Use: For testing and development

**Production** (`ENVIRONMENT=production`):
- Database: PostgreSQL (via `DATABASE_URL`)
- Update Mode: Webhooks (Telegram sends updates to your server)
- Platform: Vercel serverless functions
- Database: Neon PostgreSQL serverless

### Database Initialization
- On bot startup, automatically create tables if they don't exist
- If tables already exist, simply connect to them
- Uses SQLAlchemy's `Base.metadata.create_all(engine)`

### Timezone Handling
- All week calculations use Singapore Time (Asia/Singapore, UTC+8)
- Database stores timestamps with timezone awareness
- Week boundaries: Sunday 00:00:00 SGT to Saturday 23:59:59 SGT

## Dependencies

**Python Packages** (install via pip):
- `python-telegram-bot` - Telegram Bot API wrapper
- `sqlalchemy` - Database ORM
- `pytz` - Timezone handling
- `fastAPI` - for webhooks in vercel

**Files Needed**:
- `bot.py` - Main bot application (generated code)
- `models.py` - SQLAlchemy models (provided by user)
- `.env` - Environment variables (not in version control)

## Bot Commands Summary

| Command | Description | Response |
|---------|-------------|----------|
| `/poll` | Create weekly training poll | Creates poll or "Poll previously created" |
| `/lines` | Show current week's votes | Formatted list of votes or "Poll not yet created" |

## Implementation Notes

1. **Week Calculation Logic**:
   - Convert current datetime to Singapore timezone
   - Find the most recent Sunday (day 0 of week)
   - Week ends on the following Saturday at 23:59:59

2. **Vote Update Flow**:
   - Telegram's poll answer update includes ALL current selections
   - Empty selection list = vote retracted
   - Bot always deletes existing votes first, then adds new ones
   - This handles both retractions and updates correctly

3. **Webhook Setup for Vercel**:
   - Bot listens on `/{TELEGRAM_BOT_TOKEN}` path
   - Vercel should route this to the bot handler
   - User must configure `vercel.json` separately

4. **Error Resilience**:
   - Database sessions are properly closed in finally blocks
   - Unknown polls (e.g., from other bots) are gracefully ignored
   - Missing usernames are handled (displayed as "No username")

## Testing Checklist

- [ ] Create a poll with `/poll` command
- [ ] Verify only one poll per week can be created
- [ ] Vote for multiple options
- [ ] Verify votes appear in database
- [ ] Check `/lines` displays votes correctly
- [ ] Retract vote and verify it's removed from database
- [ ] Change vote and verify database is updated
- [ ] Test with user without username
- [ ] Test across week boundary (Sunday midnight)
- [ ] Verify webhook mode works on Vercel
- [ ] Verify polling mode works locally