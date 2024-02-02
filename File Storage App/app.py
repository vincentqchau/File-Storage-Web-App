from flask import Flask, redirect, url_for, render_template, request, session, flash, send_file
from werkzeug.utils import secure_filename
from datetime import timedelta
from app_db import Database
from io import BytesIO

app = Flask(__name__)
app.secret_key = "NgiTjdjkmla292KJv29cvj2G51"
app.permanent_session_lifetime = timedelta(minutes=10)

mimetypes = {"txt": "text/plain", "gif": "image/gif", "jpeg": "image/jpeg", "jpg": "image/jpeg", "png": "image/png", "pdf": "application/pdf", "mp4": "video/mp4"}

db = Database()

#basic home page
@app.route("/")
def home():
    if "uuid" in session:
        user = db.userByUUID(session["uuid"])
        msg = f"Welcome {user[3]}"
        return render_template("index.html", welcome = msg)
    else:
        return render_template("index.html", welcome="Register to get started")

@app.route("/login", methods=["POST", "GET"])
def login():
    if "uuid" in session:
        return redirect(url_for("home"))
    # user logged in
    if request.method == "POST":
        email, password = request.form["email"], request.form["password"]
        #fields are correctly filled
        if email != "" and password != "":
            user = db.userByEmail(email)
            #matching password
            if user != None and user[2] == password:
                session.permanent = True
                session.modified = True
                session["uuid"] = user[0]
                return redirect(url_for("home"))
            else:
                flash("Unrecognized Email or Inncorrect Password", "error")
        else:
            flash("Missing login credentials", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    #removes data from user session
    session.pop("uuid", None)
    return redirect(url_for("home"))

#registration form
@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        firstName, lastName, email, password = request.form["first-name"], request.form["last-name"], request.form["email"], request.form["password"]
        if firstName != "" and lastName != "" and email != "" and password != "":
            #can register user
            if db.addUser(email, password, firstName, lastName):
                return redirect(url_for("login"))
            else:
                flash("Email already used", "error")
        else:
            flash("Missing fields", "error")

    return render_template("register.html")

#view files associated with user
@app.route("/storage/<uuid>/<id>/<filename>")
def viewFile(uuid, id, filename):
    if "uuid" in session and session["uuid"] == uuid:
        data = db.getFile(id)
        return send_file(BytesIO(data[3]), attachment_filename=data[2], mimetype=data[4])
    return redirect(url_for("home"))

#file storage
@app.route("/storage/<uuid>/<folder>", methods=["POST", "GET"])
def storage(uuid, folder):
    if "uuid" in session and session["uuid"] == uuid:
        if request.method == "POST":
            if "upload" in request.files and request.files["upload"]:
                file = request.files["upload"]
                filename = file.filename
                db.addFile(session["uuid"], filename, file, mimetypes[filename.rsplit('.', 1)[1].lower()], folder)
            elif "make-folder" in request.form and request.form["make-folder"] != "":
                db.addFolder(session["uuid"], request.form["make-folder"], folder)
            elif "delete-file" in request.form and request.form["delete-file"] != "":
                db.deleteFile(uuid, int(request.form["delete-file"]))
            elif "delete-folder" in request.form and request.form["delete-folder"] != "":
                db.deleteFolder(uuid, request.form["delete-folder"])
            return redirect(url_for("storage", uuid=uuid, folder=folder))
        return render_template(
                               "userStorage.html",
                               name=db.userByUUID(session["uuid"])[3],
                               path=db.getPath(uuid, folder), 
                               files=db.getFilesByFolder(session["uuid"], folder), 
                               folders=db.getFoldersByParent(session["uuid"], folder)
                               )
    return redirect(url_for("home"))

#authenticates users access to storage
@app.route("/storage/authenticate")
def authenticate():
    if "uuid" in session:
        return redirect(url_for("storage", uuid=session["uuid"], folder=db.getRoot(session["uuid"])[2]))
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug = True)