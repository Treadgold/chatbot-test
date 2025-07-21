#!/usr/bin/env python3
"""
Script to consolidate duplicate chat archive files for the same session.
This fixes the issue where each message was creating a new file.
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime

CHAT_ARCHIVE_DIR = 'chat_archive'

def consolidate_session_files():
    """Consolidate multiple files for the same session into one file"""
    
    # Group files by session ID
    session_files = defaultdict(list)
    
    for file_path in Path(CHAT_ARCHIVE_DIR).glob("*.json"):
        if file_path.name == 'archive_summary.json':
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session_id = data['session_id']
            session_files[session_id].append((file_path, data))
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    # Process each session
    for session_id, files in session_files.items():
        if len(files) == 1:
            continue  # Only one file, no consolidation needed
            
        print(f"Consolidating {len(files)} files for session {session_id}")
        
        # Sort by creation time to get the earliest file
        files.sort(key=lambda x: x[1]['created_at'])
        
        # Use the first file as the base
        base_file_path, base_data = files[0]
        
        # Find the file with the most messages (should be the latest)
        latest_file_path, latest_data = max(files, key=lambda x: x[1]['message_count'])
        
        # Update the base file with the latest data
        consolidated_data = {
            'session_id': session_id,
            'created_at': base_data['created_at'],  # Keep original creation time
            'last_updated': datetime.now().isoformat(),
            'message_count': latest_data['message_count'],
            'conversation_history': latest_data['conversation_history'],
            'metadata': latest_data['metadata']
        }
        
        # Write consolidated data to base file
        with open(base_file_path, 'w', encoding='utf-8') as f:
            json.dump(consolidated_data, f, indent=2, ensure_ascii=False)
        
        # Delete the other files
        for file_path, _ in files[1:]:
            try:
                os.remove(file_path)
                print(f"  Deleted: {file_path.name}")
            except Exception as e:
                print(f"  Error deleting {file_path}: {e}")
        
        print(f"  Consolidated into: {base_file_path.name}")

if __name__ == "__main__":
    consolidate_session_files()
    print("Consolidation complete!") 