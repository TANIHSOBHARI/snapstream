# videos.py
# Stores video metadata

from datetime import datetime

videos_db = {}

def add_video(video_id, title, description, filename, uploader, category):
    videos_db[video_id] = {
        "title": title,
        "description": description,
        "filename": filename,
        "uploader": uploader,
        "category": category,
        "views": 0,
        "uploaded_at": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }

def increment_views(video_id):
    if video_id in videos_db:
        videos_db[video_id]["views"] += 1
