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
        ic(request.user_agent)
        ic(request.remote_addr)
        if verify(username,email):
            ic("here")
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
    flash("You can only login on the device you registered on.", "warning")
    user = find_by_id(session.get('user_id'))
    ic(user)
    # TODO: use the same try-value error thing used in sign-up to fix this so that it queries the database directly.
    if user:
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            if email == user['email'] and password == user['password']:
                if user['activated'] == 'yes':
                    flash("Logged in Successfully","success")
                else:
                    flash("Correct Credintials, but please contact Yassin to activate your account.","error")
                    
                
                return redirect("/")
            else:
                flash("Wrong email or password. Please try again or contact Yassin to reset.", "error")
                ic(email,user['email'])
                ic(password,user['password'])
                return render_template('login.html',username=user['username'])

            
    else:
        flash("Please register before attempting to login","error")
        return redirect("/sign-up")








    return render_template('login.html',username=user['username'])
if __name__ == "__main__":
    app.run(debug=True,port=8080,host='0.0.0.0')

