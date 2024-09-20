from pymongo import MongoClient
from os import environ
from icecream import ic
from datetime import datetime
import pytz
from bson import ObjectId
from flask import session,flash




client = MongoClient(environ.get("mongodb"))
db = client["ElyasNotes"]
users_collection = db.Users
subjects_collection = db.Subjects


def time_now():
    saudi_tz = pytz.timezone('Asia/Riyadh')
    current_time = datetime.now(saudi_tz).strftime("%A, %dth of %B, %I:%M %p")
    ic(current_time)
    return current_time




def find_by_id(id):
    user_id = ObjectId(id)
    user = users_collection.find_one({"_id":user_id})
    try:
        return user
    except Exception as e:
        return None


def is_admin(id):
    user = users_collection.find_one({"_id":ObjectId(id)})
    if user:
        ic(f"Checking {user.get('username')} for admin privileges...")
        session['admin'] = user['admin']
        return user['admin'] == "yes" if user else "user was not found."
    else:
        ic(f"Could not find user with Id: {id}")
        session.clear()
        return None
   





def verify(username,email):
    try: 
        existing_user_by_email = users_collection.find_one({"email":email})
        existing_user_by_username = users_collection.find_one({"username":username})
        if existing_user_by_email:
            raise ValueError("Email has already been used.")
        elif existing_user_by_username:
            raise ValueError("Username has already been used.")
        ic("Successfully registered")
        flash("Successfully registered","success")
        return True
    except ValueError as ve:
        ic(str(ve))
        flash(str(ve),"error")
        return False
    except Exception as e:
        ic(f"error while verifying email and username : {e}")
        flash(f"An unexpected error has occured, try again later or contact yassin, {e}","error")
        return False
    
        
    
ic("Successfully loaded everything from utils.py")