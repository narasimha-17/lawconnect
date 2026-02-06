from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask import flash
# ---------------- APP CONFIG ----------------


app = Flask(__name__)
app.secret_key = "lawconnect_secret_key"

# DB config
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Surya7075@localhost/lawconnect_ai"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------- MODEL ----------------
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    role = db.Column(db.String(20))


class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100))


class Module(db.Model):
    __tablename__ = "modules"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))


class StudentProgress(db.Model):
    __tablename__ = "student_progress"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    module_id = db.Column(db.Integer, db.ForeignKey("modules.id"))
    progress = db.Column(db.Integer)


# ---------------- HOME ----------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        print("FORM DATA ->", email, password, role)

        user = User.query.filter_by(email=email, role=role).first()
        print("USER FROM DB ->", user)

        if user and user.password == password:   # ✅ PLAIN TEXT CHECK
            session["user_id"] = user.id
            session["role"] = role

            print("LOGIN SUCCESS")

            if role == "student":
                return redirect(url_for("student_dashboard"))
            elif role == "advocate":
                return redirect(url_for("advocate_dashboard"))
            elif role == "citizen":
                return redirect(url_for("citizen_dashboard"))
            else:
                return redirect(url_for("index"))

        error = "Invalid email, password, or role"
        print("LOGIN FAILED")

    return render_template("login.html", error=error)
def legal_chatbot(query):
    query = query.lower()

    if "divorce" in query:
        return "Divorce laws in India are governed by personal laws such as Hindu Marriage Act, Muslim Personal Law, etc."

    elif "fir" in query:
        return "An FIR can be filed at the nearest police station or online via state police portals."

    elif "cyber crime" in query:
        return "Cyber crimes can be reported at https://cybercrime.gov.in"

    elif "property" in query:
        return "Property disputes are handled under civil law. You may consult a civil lawyer."

    elif "bail" in query:
        return "Bail is a legal right in most cases except serious non-bailable offenses."

    else:
        return "I can help with general legal queries related to divorce, FIR, cyber crime, bail, and property."

# ---------------- CITIZEN DASHBOARD ----------------
@app.route("/citizen/dashboard", methods=["GET", "POST"])
def citizen_dashboard():
    if session.get("role") != "citizen":
        return redirect(url_for("login"))

    chatbot_reply = None

    if request.method == "POST":
        query = request.form.get("query")
        chatbot_reply = legal_chatbot(query)

    # 🔹 Fetch logged-in citizen from DB
    citizen = User.query.get(session.get("user_id"))

    return render_template(
        "citizenDashboard.html",
        citizen=citizen,              # ✅ THIS WAS MISSING
        chatbot_reply=chatbot_reply
    )

# ---------------- DASHBOARDS ----------------
@app.route("/student/dashboard")
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    # Fetch student info
    student = Student.query.filter_by(user_id=user_id).first()

    # Fetch modules with progress
    modules = (
        db.session.query(Module, StudentProgress.progress)
        .join(StudentProgress, Module.id == StudentProgress.module_id)
        .filter(StudentProgress.student_id == student.id)
        .all()
    )

    return render_template(
        "studentDashboard.html",
        student=student,
        modules=modules
    )


@app.route("/advocate/dashboard")
def advocate_dashboard():
    if session.get("role") != "advocate":
        return redirect(url_for("login"))

    user = User.query.get(session.get("user_id"))

    return render_template(
        "advocateDashboard.html",
        advocate=user
    )




# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#-------------register route----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        print("FORM DATA ->", name, email, password, role)

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            error = "Email already registered"
            print("REGISTRATION FAILED: Email exists")
        else:
            new_user = User(name=name, email=email, password=password, role=role)
            db.session.add(new_user)
            db.session.commit()
            print("REGISTRATION SUCCESS")
            return redirect(url_for("login"))

    return render_template("register.html", error=error)
#---------------- CONTACT ----------------

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        # Demo: just log to console (no DB yet)
        print("CONTACT FORM ->", name, email, message)

        flash("Thanks for reaching out! We’ll get back to you soon.", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")

if __name__ == "__main__":
    app.run(debug=True)
