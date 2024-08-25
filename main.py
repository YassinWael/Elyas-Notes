from bson import ObjectId
from flask import Flask,render_template,redirect,request,session,flash
from pymongo import MongoClient
from dotenv import load_dotenv
from os import environ
from icecream import ic
load_dotenv()
app = Flask(__name__)
app.secret_key = environ.get("secret_key")

client = MongoClient(environ.get("mongodb"))
db = client["ElyasNotes"]
users_collection = db.Users






def find_by_id(id):
    user_id = ObjectId(id)
    user = users_collection.find({"_id":user_id})
    try:
        return list(user)[0]
    except Exception as e:
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
    
        
    


@app.route("/")
@app.route("/home")
def home():
    

    return render_template("home.html",user_id=session.get('user_id'))


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
                "devices":[request.remote_addr]

            })  

            user_id = users_collection.find_one({"email":email})
            ic(str(user_id['_id']))
            session['user_id'] = str(user_id['_id'])
            flash("Successfully registered, Proceed to log-in below.","success")

            return redirect("/login")
        
       
    if session.get('user_id'):
        flash("User already has an account.","warning")
        return redirect("/")
    return render_template("sign-up.html")


@app.route("/login",methods = ['GET','POST'])
def login():
   
    user = find_by_id(session.get('user_id'))
    ic(user)
  
 
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user_ip = request.remote_addr

        try:
            user = users_collection.find_one({"email":email})
            if user:
                if password == user["password"]:
                    if user['activated'] == 'yes':
                        flash("Logged in successfully :) ","success")
                        session['user_id'] = str(user['_id'])
                        user_logged_in_devices = user['devices']
                        user_logged_in_devices.append(request.remote_addr)
                        ic(user_logged_in_devices)
                        ic(type(user_logged_in_devices))
                        ic(user)
                        updated = users_collection.update_one({"_id":ObjectId(user['_id'])},{"$set":{"devices":user_logged_in_devices}})
                        ic(updated)

                        return redirect("/")
                    else:
                        raise ValueError("Correct credintials, but account has not been approved yet, try again later or contact Yassin")

                else:
                    raise ValueError("Wrong email or password. Please try again or contact Yassin to reset.")
                
            else:
                raise ValueError(f"User with email {email} was not found in the database.")



        except ValueError as ve:
            ic(ve)
            ve = str(ve)
            ic(ve)
            flash(ve,"error")
            ic(ve)
            return redirect(request.referrer)
    return render_template('login.html',username=user['username'] if user else "")
        
@app.route("/logout/<user_id>",methods = ["POST","GET"])     
def logout(user_id):
    session['user_id'] = None
    user = find_by_id(user_id)
    user_logged_in_devices = user['devices']
    user_logged_in_devices.remove(request.remote_addr)
    updated = users_collection.update_one({"_id":ObjectId(user['_id'])},{"$set":{"devices":user_logged_in_devices}})
    ic(updated)



    return render_template('login.html',username=user['username'] if user else "")
if __name__ == "__main__":
    app.run(debug=True,port=8080,host='0.0.0.0')

