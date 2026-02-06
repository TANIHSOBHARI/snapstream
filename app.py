import os, json, uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "snapstream_secret_key"

# ---------------- PATHS ----------------
UPLOAD_FOLDER = "static/videos"
THUMB_FOLDER = "static/thumbnails"
SUB_FILE = "subscriptions.json"
WL_FILE = "watch_later.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMB_FOLDER, exist_ok=True)

# ---------------- INIT JSON FILES ----------------
for f in [SUB_FILE, WL_FILE]:
    if not os.path.exists(f):
        with open(f, "w") as fp:
            json.dump({}, fp)

# ---------------- IN-MEMORY STORAGE ----------------
users = {}
videos = {}

# ---------------- DEMO / FAKE VIDEOS ----------------
DEMO_VIDEOS = {
    "demo1": {
        "title": "Welcome to SnapStream",
        "description": "Demo video shown when no uploads exist",
        "filename": None,
        "thumbnail": None,
        "uploader": "snapstream",
        "views": 1200,
        "uploaded_at": "01 Feb 2026"
    },
    "demo2": {
        "title": "How SnapStream Works",
        "description": "Platform overview demo",
        "filename": None,
        "thumbnail": None,
        "uploader": "snapstream",
        "views": 860,
        "uploaded_at": "02 Feb 2026"
    }
}

# ---------------- HELPERS ----------------
def load_json(path):
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def send_notification(message):
    # Local demo (SNS-ready)
    print("NOTIFICATION:", message)
    # AWS SNS hook later

# ---------------- HOME ----------------
@app.route("/")
def home():
    data = videos if videos else DEMO_VIDEOS
    return render_template("home.html", videos=data)

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users:
            return "User already exists"

        users[username] = {
            "password": password,
            "role": "creator"
        }

        session["user"] = username
        session.setdefault("watch_history", [])
        return redirect("/")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = users.get(username)
        if not user or user["password"] != password:
            return "Invalid credentials"

        session["user"] = username
        session.setdefault("watch_history", [])
        return redirect("/")

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    my_uploads = {
        vid_id: vid
        for vid_id, vid in videos.items()
        if vid["uploader"] == session["user"]
    }

    my_history = session.get("watch_history", [])

    return render_template(
        "dashboard.html",
        my_uploads=my_uploads,
        my_history=my_history
    )

# ---------------- ABOUT ----------------
@app.route("/about")
def about():
    return render_template("about.html")

# ---------------- UPLOAD ----------------
@app.route("/upload", methods=["GET","POST"])
def upload():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        vid = str(uuid.uuid4())

        vfile = request.files["video"]
        tfile = request.files["thumbnail"]

        vname = vid + "_" + vfile.filename
        tname = vid + "_" + tfile.filename

        vfile.save(os.path.join(UPLOAD_FOLDER, vname))
        tfile.save(os.path.join(THUMB_FOLDER, tname))

        videos[vid] = {
            "title": request.form["title"],
            "description": request.form.get("description",""),
            "filename": vname,
            "thumbnail": tname,
            "uploader": session["user"],
            "views": 0,
            "uploaded_at": datetime.now().strftime("%d %b %Y")
        }

        send_notification(f"{session['user']} uploaded a video")
        return redirect("/")

    return render_template("upload.html")

# ---------------- STREAM ----------------
@app.route("/stream/<vid>")
def stream(vid):
    v = videos.get(vid)
    if not v:
        return "Video not found"

    v["views"] += 1
    session["watch_history"].insert(0, {
        "id": vid,
        "title": v["title"],
        "thumbnail": v["thumbnail"],
        "uploader": v["uploader"]
    })

    return render_template("stream.html", video=v)

# ---------------- CHANNEL + SUBSCRIBE ----------------
@app.route("/channel/<user>")
def channel(user):
    channel_videos = {
        k:v for k,v in videos.items()
        if v["uploader"] == user
    }

    subs = load_json(SUB_FILE)
    me = session.get("user")
    subscribed = me in subs and user in subs[me]

    return render_template(
        "channel.html",
        channel=user,
        videos=channel_videos,
        subscribed=subscribed
    )

@app.route("/subscribe/<user>")
def subscribe(user):
    if "user" not in session:
        return redirect("/login")

    subs = load_json(SUB_FILE)
    subs.setdefault(session["user"], [])

    if user not in subs[session["user"]]:
        subs[session["user"]].append(user)
        send_notification(f"You subscribed to {user}")

    save_json(SUB_FILE, subs)
    return redirect(f"/channel/{user}")

# ---------------- SUBSCRIPTIONS ----------------
@app.route("/subscriptions")
def subscriptions():
    if "user" not in session:
        return redirect("/login")

    subs = load_json(SUB_FILE).get(session["user"], [])
    feed = {k:v for k,v in videos.items() if v["uploader"] in subs}

    return render_template("subscriptions.html", videos=feed)

# ---------------- WATCH LATER ----------------
@app.route("/watch-later/add/<vid>")
def add_watch_later(vid):
    if "user" not in session:
        return redirect("/login")

    wl = load_json(WL_FILE)
    wl.setdefault(session["user"], [])

    if vid not in wl[session["user"]]:
        wl[session["user"]].append(vid)

    save_json(WL_FILE, wl)
    return redirect("/watch-later")

@app.route("/watch-later")
def watch_later():
    if "user" not in session:
        return redirect("/login")

    wl_ids = load_json(WL_FILE).get(session["user"], [])
    wl_videos = [(vid, videos[vid]) for vid in wl_ids if vid in videos]

    return render_template("watch_later.html", videos=wl_videos)

# ---------------- SETTINGS ----------------
@app.route("/settings")
def settings():
    if "user" not in session:
        return redirect("/login")
    return render_template("settings.html")

# ---------------- NOTIFICATIONS ----------------
@app.route("/notifications")
def notifications():
    return render_template("notifications.html")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
