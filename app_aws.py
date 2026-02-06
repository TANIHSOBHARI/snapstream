from flask import Flask, render_template, request, redirect, session
import os, uuid
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "snapstream_secret_key"

# ================= AWS CONFIG =================
REGION = "us-east-1"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

# DynamoDB Tables
users_table = dynamodb.Table("Users")
videos_table = dynamodb.Table("Videos")
subs_table = dynamodb.Table("Subscriptions")
watch_later_table = dynamodb.Table("WatchLater")

# SNS Topic
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:XXXXXXXXXXXX:snapstream-topic"

# ================= FILE UPLOAD =================
UPLOAD_FOLDER = "static/videos"
THUMB_FOLDER = "static/thumbnails"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMB_FOLDER, exist_ok=True)

# ================= HELPERS =================
def send_notification(subject, message):
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    except ClientError as e:
        print("SNS ERROR:", e)

# ================= HOME =================
@app.route("/")
def home():
    response = videos_table.scan()
    videos = response.get("Items", [])
    return render_template("home.html", videos=videos)

# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        res = users_table.get_item(Key={"username": username})
        if "Item" in res:
            return "User already exists"

        users_table.put_item(
            Item={"username": username, "password": password}
        )

        send_notification(
            "New User Registered",
            f"User {username} registered on SnapStream"
        )

        session["user"] = username
        return redirect("/")

    return render_template("register.html")

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        res = users_table.get_item(Key={"username": username})
        if "Item" not in res or res["Item"]["password"] != password:
            return "Invalid credentials"

        session["user"] = username
        send_notification("User Login", f"{username} logged in")
        return redirect("/")

    return render_template("login.html")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    user = session.get("user")
    session.clear()
    if user:
        send_notification("User Logout", f"{user} logged out")
    return redirect("/")

# ================= UPLOAD =================
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        video_id = str(uuid.uuid4())
        video = request.files["video"]
        thumb = request.files["thumbnail"]

        vname = secure_filename(video.filename)
        tname = secure_filename(thumb.filename)

        video.save(os.path.join(UPLOAD_FOLDER, vname))
        thumb.save(os.path.join(THUMB_FOLDER, tname))

        videos_table.put_item(
            Item={
                "video_id": video_id,
                "title": request.form["title"],
                "filename": vname,
                "thumbnail": tname,
                "uploader": session["user"],
                "views": 0,
                "uploaded_at": datetime.now().strftime("%d %b %Y")
            }
        )

        send_notification(
            "New Video Uploaded",
            f"{session['user']} uploaded a video"
        )

        return redirect("/")

    return render_template("upload.html")

# ================= STREAM =================
@app.route("/stream/<video_id>")
def stream(video_id):
    res = videos_table.get_item(Key={"video_id": video_id})
    if "Item" not in res:
        return "Video not found"

    video = res["Item"]
    video["views"] += 1

    videos_table.update_item(
        Key={"video_id": video_id},
        UpdateExpression="SET views = :v",
        ExpressionAttributeValues={":v": video["views"]}
    )

    return render_template("stream.html", video=video)

# ================= SUBSCRIBE =================
@app.route("/subscribe/<channel>")
def subscribe(channel):
    if "user" not in session:
        return redirect("/login")

    subs_table.put_item(
        Item={
            "username": session["user"],
            "channel": channel
        }
    )

    send_notification(
        "New Subscription",
        f"{session['user']} subscribed to {channel}"
    )

    return redirect("/")

# ================= WATCH LATER =================
@app.route("/watch-later/add/<video_id>")
def add_watch_later(video_id):
    if "user" not in session:
        return redirect("/login")

    watch_later_table.put_item(
        Item={
            "username": session["user"],
            "video_id": video_id
        }
    )
    return redirect("/watch-later")

@app.route("/watch-later")
def watch_later():
    if "user" not in session:
        return redirect("/login")

    res = watch_later_table.query(
        KeyConditionExpression=Key("username").eq(session["user"])
    )
    video_ids = [i["video_id"] for i in res.get("Items", [])]

    videos = []
    for vid in video_ids:
        v = videos_table.get_item(Key={"video_id": vid})
        if "Item" in v:
            videos.append(v["Item"])

    return render_template("watch_later.html", videos=videos)

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
