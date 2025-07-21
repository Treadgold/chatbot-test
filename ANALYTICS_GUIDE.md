# Chat Analytics System Guide

This guide explains how to use the new chat logging and analytics features added to the chatbot application.

## Features Overview

### 🔄 Automatic Chat Logging
- **Every conversation is automatically saved** to the `chat_archive/` directory
- **No user action required** - logging happens in the background
- **Files are named with metadata**: `YYYYMMDD_HHMM_count_sessionid.json`
- **Archive summary is updated** automatically with each conversation

### 📊 Analytics Dashboard
- **Live dashboard** available at `/admin/analytics`
- **Real-time charts** showing conversation patterns
- **Conversation browser** to view all past chats
- **Statistics** including total conversations, messages, and character counts

### 📁 File Organization
- **Single archive folder**: All files stored in `chat_archive/`
- **Metadata in filenames**: Easy to sort and identify conversations
- **JSON format**: Human-readable and machine-parseable
- **No cleanup**: Files are kept permanently for analysis

## How to Use

### 1. Access the Analytics Dashboard

Navigate to: `http://your-server:8000/admin/analytics`

You'll see:
- **Statistics cards** with key metrics
- **Daily conversation chart** showing activity over time
- **Hourly activity chart** showing peak usage times
- **Conversation list** on the left side
- **Preview pane** on the right side

### 2. Browse Conversations

1. **Click any conversation** in the left sidebar
2. **View full conversation** in the right preview pane
3. **See metadata** including session ID, timestamps, and character counts
4. **Scroll through** the conversation history

### 3. Refresh Data

- **Manual refresh**: Click the "🔄 Refresh Data" button
- **Auto-refresh**: Dashboard automatically refreshes every 5 minutes
- **Real-time updates**: New conversations appear automatically

### 4. Understanding the Data

#### Statistics Cards
- **Total Conversations**: Number of unique chat sessions
- **Total Messages**: Total user + AI message exchanges
- **Avg Messages/Chat**: Average conversation length
- **Total Characters**: Combined character count across all chats

#### Charts
- **Conversations by Date**: Line chart showing daily activity trends
- **Activity by Hour**: Bar chart showing peak usage hours (0-23)

#### File Structure
```
chat_archive/
├── archive_summary.json           # Analytics data
├── 20241201_1430_003_a1b2c3d4.json # Individual conversations
├── 20241201_1445_007_f5e6d7c8.json
└── README.md                       # Documentation
```

## Configuration

The system is controlled by environment variables in `.env`:

```bash
# Enable/disable logging
CHAT_LOGGING_ENABLED=true

# Archive directory location
CHAT_ARCHIVE_DIR=chat_archive
```

## Data Format

Each conversation file contains:

```json
{
  "session_id": "uuid",
  "created_at": "2024-12-01T14:30:00.123456",
  "last_updated": "2024-12-01T14:35:00.654321",
  "message_count": 3,
  "conversation_history": [
    {
      "user": "Hello!",
      "ai": "Och, what dae ye want?"
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

## API Endpoints

### Analytics Routes
- `GET /admin/analytics` - View dashboard
- `POST /admin/refresh-analytics` - Force refresh data
- `GET /admin/conversation/<filename>` - Get specific conversation
- `GET /admin/analytics-data` - Get raw analytics JSON

## Security Considerations

1. **Archive directory** should not be web-accessible
2. **Admin routes** (`/admin/*`) should be protected in production
3. **User consent** may be required for logging in some jurisdictions
4. **File permissions** should be properly configured
5. **Backup strategy** should include the archive directory

## Troubleshooting

### No Conversations Appearing
- Check `CHAT_LOGGING_ENABLED=true` in `.env`
- Verify `chat_archive/` directory exists and is writable
- Check application logs for errors

### Analytics Not Updating
- Click "Refresh Data" manually
- Check if `archive_summary.json` exists
- Verify file permissions on archive directory

### Charts Not Loading
- Ensure Chart.js can load from CDN
- Check browser console for JavaScript errors
- Verify content security policy allows external scripts

## Performance Notes

- **Archive summary updates** with every conversation (minimal impact)
- **Large conversations** (1000+ messages) may take longer to save
- **Analytics refresh** scans all files (scales with conversation count)
- **Dashboard loading** depends on number of conversations displayed

## Future Enhancements

Potential future features:
- **Date range filtering** in analytics
- **Export functionality** for conversations
- **Search capability** across conversations
- **User-specific analytics** and filtering
- **Automated reporting** and summaries 