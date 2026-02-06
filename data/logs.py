# logs.py
# Stores unique views and watch history with timestamps

from datetime import datetime

unique_views = []
watch_history = []

def has_user_viewed(username, video_id):
    return any(
        log["user"] == username and log["video_id"] == video_id
        for log in unique_views
    )

def add_unique_view(username, video_id):
    unique_views.append({
        "user": username,
        "video_id": video_id
    })

def add_watch_history(username, video_id):
    watch_history.append({
        "user": username,
        "video_id": video_id,
        "watched_at": datetime.now().strftime("%d %b %Y, %I:%M %p")
    })
