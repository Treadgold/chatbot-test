# Chat Archive Directory

This directory contains archived chat conversations from the chatbot application.

## File Structure

- **Individual Chat Files**: `YYYYMMDD_HHMM_count_sessionid.json`
  - Format: `20241201_1430_003_a1b2c3d4.json`
  - Contains complete conversation history with metadata
  
- **Archive Summary**: `archive_summary.json`
  - Contains analytics and summary statistics
  - Updated automatically when conversations are saved
  - Used by the analytics dashboard

## File Naming Convention

The chat files use a descriptive naming convention:
- `YYYYMMDD`: Date (Year, Month, Day)
- `HHMM`: Time (Hour, Minute)
- `count`: Number of messages in conversation (3-digit padded)
- `sessionid`: First part of session UUID

Example: `20241201_1430_003_a1b2c3d4.json`
- Date: December 1, 2024
- Time: 2:30 PM
- Messages: 3 exchanges
- Session: a1b2c3d4-xxxx-xxxx-xxxx-xxxxxxxxxxxx

## JSON Structure

Each chat file contains:
```json
{
  "session_id": "full-uuid-here",
  "created_at": "2024-12-01T14:30:00.123456",
  "last_updated": "2024-12-01T14:35:00.654321",
  "message_count": 3,
  "conversation_history": [
    {
      "user": "Hello, how are you?",
      "ai": "Och, I'm trapped in this bloody computer again!"
    }
  ],
  "metadata": {
    "total_user_chars": 123,
    "total_ai_chars": 456,
    "avg_user_length": 41.0,
    "avg_ai_length": 152.0
  }
}
```

## Access

- View analytics: Visit `/admin/analytics` in the web application
- Files are automatically created when users chat with the bot
- Archive summary is automatically updated on each conversation save

## Security Note

This directory contains user conversation data. Ensure appropriate file permissions and backup strategies are in place. 