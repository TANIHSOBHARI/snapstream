# users.py
# This file stores all registered users using a Python dictionary

users_db = {
    "admin": {
        "password": "admin123",
        "role": "admin"
    }
}

def add_user(username, password, role):
    if username in users_db:
        return False
    users_db[username] = {
        "password": password,
        "role": role
    }
    return True

def validate_user(username, password):
    if username in users_db and users_db[username]["password"] == password:
        return True
    return False

def get_user_role(username):
    return users_db[username]["role"]
