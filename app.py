from random import randint,choice
from bson import ObjectId
from flask import Flask,render_template,redirect,request,session,flash
from pymongo import MongoClient
from dotenv import load_dotenv
from os import environ
from icecream import ic
import functools
from datetime import datetime
import pytz
load_dotenv()
app = Flask(__name__)

app.secret_key = environ.get("secret_key")

client = MongoClient(environ.get("mongodb"))
db = client["ElyasNotes"]
users_collection = db.Users
subjects_collection = db.Subjects



def login_required(route):
    @functools.wraps(route)
    def protect(*args,**kwargs):
        user_id = session.get('user_id')
        if user_id:
            return route(*args,**kwargs)
        flash("Please Login first","warning")
        return redirect("/login")
    return protect




def admin_only(route):
    @functools.wraps(route)
    def admin_protect(*args,**kwargs):
        user_id = session.get('user_id')
        if user_id: #user is logged in
            if is_admin(user_id):
                return route(*args,**kwargs)
            
        flash("You need to be in a higher position to access this.","error")
        return redirect("/")
    return admin_protect


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
    ic(f"Checking {user.get('username')} for admin privileges...")
    return user['admin'] == "yes" if user else "user was not found."
   





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
    
        
    


@app.route("/")
@app.route("/home")
def home():
    ic(request.remote_addr)
    headers = dict(request.headers)

    ic(headers)
    ic((headers.get('X-Forwarded-For')))

    subjects = list(subjects_collection.find({}))
    

    return render_template("home.html",user_id=session.get('user_id'),subjects=subjects[:3])




@app.route("/sign-up",methods=["POST","GET"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if verify(username,email):
        

            users_collection.insert_one({
                "username":username,
                "email":email,
                "password":password,
                "activated":"no",
                "admin":"no",
                "devices":[],
                "devices_limit":3,
                "date_created":time_now()

            })  

            
            flash("Successfully registered, Proceed to log-in below.","success")

            return redirect("/login")
        
       
    if session.get('user_id'):
        flash("User already has an account.","warning")
        return redirect("/")
    return render_template("sign-up.html")


@app.route("/login",methods = ['GET','POST'])
def login():
    ic(dict(request.form))
    user = find_by_id(session.get('user_id'))
    ic(user)
  
 
    if request.method == "POST":
      
        email = request.form.get("email")
        password = request.form.get("password")
      
        headers = dict(request.headers)

        user_ip = headers['X-Forwarded-For'] if headers['Host'] == "elyas-notes-production.up.railway.app" else request.remote_addr
        user_agent = headers['User-Agent']
        current_time = time_now()
        ic(user_ip,user_agent)


        
        try:
            user = users_collection.find_one({"email":email})
            if user:
                ic("passed user exists check")
                user_logged_in_devices = user['devices']
                user_devices_limit = user['devices_limit']
                ic([device['user_ip'] for device in user_logged_in_devices])
                if password == user["password"]:
                    ic("passed password check")
                    if user['activated'] == 'yes':
                        ic("passed activation check")
                        if user_ip not in [device['user_ip'] for device in user_logged_in_devices]:
                            ic("passed user_ip check")

                            if len(user_logged_in_devices) < int(user_devices_limit):
                                flash("Logged in successfully :) ","success")
                                session['user_id'] = str(user['_id'])
                                session['username'] = user['username']
                                new_device = {
                                    "user_ip":user_ip,
                                    "user_agent":user_agent,
                                    "date_joined":current_time
                                }
                                user_logged_in_devices.append(new_device)
                                ic(user_logged_in_devices)
                                ic(user)
                                updated = users_collection.update_one({"_id":ObjectId(user['_id'])},{"$set":{"devices":user_logged_in_devices}})
                                ic(updated)
                                return redirect("/")
                            else:
                                e = f"You are already logged in from {user_devices_limit} other devices, which is the max limit."
                                raise ValueError(e)
                        else: # user is already logged in from this ip
                            flash("Logged in successfully :) ","success")
                            session['user_id'] = str(user['_id'])
                            session['username'] = user['username']
                            ic(user)
                            return redirect("/")
                            
                    else:
                        raise ValueError("Correct credintials, but account has not been approved yet, try again later or contact Yassin")

                else:
                    ic(f"{email}:{password}, {user['email']}: {user['password']}")
                    raise ValueError("Wrong email or password. Please try again or contact Yassin to reset.")
                
            else:
                raise ValueError(f"User with email {email} was not found in the database.")



        except ValueError as ve:
            ic(ve)
            ve = str(ve)
            ic(ve)
            flash(ve,"error")
            ic(ve)
            ic("error, unexpected")
            return redirect(request.referrer)
    return render_template('login.html',username=user['username'] if user else "")
        
@app.route("/logout",methods = ["POST","GET"])     
def logout():
    if session.get("user_id"):
        headers = dict(request.headers)
        user_ip = headers['X-Forwarded-For'] if headers['Host'] == "elyas-notes-production.up.railway.app" else request.remote_addr
        
        user_id = session['user_id']
        session.clear()
        
        user = find_by_id(user_id)
        user_logged_in_devices = [device for device in user['devices'] if device['user_ip'] != user_ip]
        
        
        updated = users_collection.update_one({"_id":ObjectId(user['_id'])},{"$set":{"devices":user_logged_in_devices}})
        ic(updated)
        return redirect("/")

    else:
        return redirect(request.referrer)




@app.route("/viewall")
def view_all():
    subjects = subjects_collection.find({})
    
    return render_template("view_all.html",subjects=list(subjects))


@app.route("/subject/<subject_name>")
def view_subject(subject_name):
    ic(subject_name)
    subject = subjects_collection.find_one({"name":subject_name})
    ic(subject)
    notes_count = [sum([len(note['lessons']) for note in subject["notes"]])][0]
    ic(notes_count)
    subjects_collection.update_one({"name":subject_name},{"$set":{"notes_count":notes_count}})


    return render_template("view_subject.html",subject=subject)

@app.route("/note/<subject_name>/<chapter_name>/<lesson_name>")
def view_note(subject_name,chapter_name="",lesson_name=""):
    
    if chapter_name == "random": #user wants a random lesson in a random chapter
        ic(subject_name)
        ic("Getting random lesson...")
        subject = subjects_collection.aggregate([
            {"$match":{"name":subject_name}},
            {"$unwind":"$notes"},
            {"$sample":{"size":1}},
            {"$unwind":"$notes.lessons"},
            {"$sample":{"size":1}},
            {"$project":{"_id":0,"notes.lessons":1}}
        ])
        lesson = list(subject)[0]['notes']['lessons']
        ic(lesson)
        ic(type(lesson))
        print(f"Randomly chose {lesson['content']}")
        return render_template("view_note.html",lesson=lesson)

    ic(subject_name,chapter_name,lesson_name)

    subject = subjects_collection.find_one({"name":subject_name,"notes.chapter_name":chapter_name,"notes.lessons.lesson_name":lesson_name},
                                           {"notes.$":1}) 
    ic(subject)
    chapter = subject['notes'][0]
    lessons = chapter['lessons']

   
    lesson = next((lesson for lesson in lessons if lesson["lesson_name"] == lesson_name),None)
    
    
    
    
    
    ic(subject,lesson)
    return render_template("view_note.html",lesson=lesson)





if __name__ == "__main__":
    app.run(debug=True,port=8080,host='0.0.0.0')



# TODO: Add creating notes for admins
# TODO: Create seperate utils.py
# TODO: Write frontend for random note




