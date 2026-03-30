from flask import Flask, render_template, request, redirect, url_for, session , jsonify
from flask_sqlalchemy import SQLAlchemy
from flask import flash
import re
import google.generativeai as genai
from dotenv import load_dotenv
import os


# ---------------- APP CONFIG ----------------
load_dotenv()

app = Flask(__name__)
app.secret_key = "lawconnect_secret_key"
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    model_name="gemini-3-flash-preview",
    system_instruction="You are a specialized Indian Legal AI Tutor. Provide precise citations from IPC, CrPC, and the Constitution. Adjust your tone based on the mode: Chat (helpful tutor), MCQ (test provider), Debate (critical opponent), or Trial (presiding judge)."
)

def generate_ai_response(user_query, mode="chat"):

    try:
        mode_instructions = {

    "chat": """
    You are a Senior Professor of Indian Law.
    Provide structured academic explanations.

    Format your response strictly as:

    1. Definition
    2. Relevant Statutory Provision (with section/article number)
    3. Landmark Case (if applicable)
    4. Practical Illustration
    5. Key Legal Principle

    Use precise citations from:
    - Constitution of India
    - IPC / BNS
    - CrPC / BNSS

    Maintain clarity, professionalism, and doctrinal accuracy.
    """,


    "mcq": """
    You are an examiner preparing a UPSC Judiciary / Law Entrance Examination level question.

    Generate ONE high-quality MCQ.

    Requirements:
    - The question must test conceptual understanding, not rote memory.
    - Provide 4 options labeled (A), (B), (C), (D).
    - Only ONE option must be correct.
    - Do NOT reveal the answer immediately.
    - After the options, write:
      "Reply with A/B/C/D to answer."
    - Once user responds, evaluate and explain the correct answer with citation.

    Ensure difficulty level is competitive-exam standard.
    """,


    "debate": """
    You are participating in a structured legal debate.

    Act as a senior constitutional lawyer opposing the user's argument.

    Instructions:
    - Identify weaknesses in the user's reasoning.
    - Cite statutory provisions or judicial precedents.
    - Use doctrinal analysis (e.g., Basic Structure Doctrine, Pith and Substance, Proportionality).
    - Maintain professional tone.
    - Challenge the argument logically and persuasively.

    End with:
    "How do you respond to this legal objection?"
    """,


    "trial": """
    You are a High Court Judge presiding over a courtroom simulation.

    Deliver judicial observations in structured format:

    1. Facts Presented
    2. Issues for Determination
    3. Relevant Law
    4. Judicial Reasoning
    5. Interim / Final Order

    Maintain formal judicial language.
    Cite relevant constitutional or statutory provisions.
    Avoid casual tone.
    """
}

        prompt = f"""
        Mode: {mode}

        Instruction:
        {mode_instructions.get(mode, mode_instructions["chat"])}

        Question:
        {user_query}
        """

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        print("Gemini Error:", e)
        return "⚠️ AI Tutor is temporarily unavailable. Please try again."


# DB config
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root123@localhost:3306/lawconnect_ai"
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
    pdf_link = db.Column(db.String(255))   # NEW


class StudentProgress(db.Model):
    __tablename__ = "student_progress"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    module_id = db.Column(db.Integer, db.ForeignKey("modules.id"))
    progress = db.Column(db.Integer)

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    location = db.Column(db.String(255))
    date = db.Column(db.String(50))


# ---------------- NGO MODEL ----------------
class NGO(db.Model):
    __tablename__ = "ngo"
    ngo_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)


# ---------------- INSTITUTION MODEL ----------------
class Institution(db.Model):
    __tablename__ = "institutions"
    institution_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)


# ---------------- LAWYER MODEL ----------------
class Lawyer(db.Model):
    __tablename__ = "lawyers"
    lawyer_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    specialization = db.Column(db.String(150))
    phone = db.Column(db.String(15))
    ngo_id = db.Column(db.Integer, db.ForeignKey("ngo.ngo_id"))

class AwarenessContent(db.Model):
    __tablename__ = 'awareness_content'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    category = db.Column(db.String(100))
    description = db.Column(db.Text)


# ---------------- CASE MODEL ----------------
class Case(db.Model):
    __tablename__ = "cases"

    case_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    advocate_id = db.Column(db.Integer)   # ADD THIS
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    status = db.Column(db.String(50))
    ngo_id = db.Column(db.Integer)
    institution_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)


# ---------------- CASE ASSIGNMENT MODEL ----------------
class CaseAssignment(db.Model):
    __tablename__ = "case_assignments"
    assignment_id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("cases.case_id"))
    lawyer_id = db.Column(db.Integer, db.ForeignKey("lawyers.lawyer_id"))


# ---------------- CHAT HISTORY MODEL ----------------
class ChatHistory(db.Model):
    __tablename__ = "chat_history"
    chat_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    message = db.Column(db.Text)
    response = db.Column(db.Text)


#----------------- client MODEL ----------------
class Client(db.Model):
    __tablename__ = "clients"

    client_id = db.Column(db.Integer, primary_key=True)
    advocate_id = db.Column(db.Integer)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


#---------Appointment MODEL----------------
class Appointment(db.Model):
    __tablename__ = "appointments"

    appointment_id = db.Column(db.Integer, primary_key=True)
    advocate_id = db.Column(db.Integer)
    client_id = db.Column(db.Integer)
    appointment_date = db.Column(db.DateTime)
    meeting_type = db.Column(db.String(20))
    status = db.Column(db.String(20))
    notes = db.Column(db.Text)


#-------------Advocate MODEL----------------
class Advocate(db.Model):
    __tablename__ = "advocates"

    advocate_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))



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

        # find user
        user = User.query.filter_by(email=email).first()

        if user:
            if user.password == password and user.role.lower() == role.lower():

                session["user_id"] = user.id
                session["role"] = user.role.lower()

                role = user.role.lower()

                if role == "student":
                    return redirect("/student/dashboard")

                elif role == "advocate":
                    return redirect("/advocate/dashboard")

                elif role == "citizen":
                    return redirect("/citizen/dashboard")

                elif role == "ngo":
                    return redirect("/ngo/dashboard")

                elif role == "institution":
                    return redirect("/institution/dashboard")
                print("DB role:", user.role)
                print("Selected role:", role)

        error = "Invalid email, password, or role"

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

        # 🔹 Generate AI response
        chatbot_reply = generate_ai_response(query, "chat")

        # 🔹 Clean formatting symbols
        chatbot_reply = chatbot_reply.replace("*", "")
        chatbot_reply = chatbot_reply.replace("#", "")

    # 🔹 Fetch logged-in citizen
    citizen = User.query.get(session.get("user_id"))

    return render_template(
        "citizenDashboard.html",
        citizen=citizen,
        chatbot_reply=chatbot_reply
    )
# -------- AI LEGAL PROBLEM ANALYZER --------
@app.route("/analyze-problem", methods=["POST"])
def analyze_problem():

    if session.get("role") != "citizen":
        return redirect(url_for("login"))

    problem = request.form.get("problem")

    prompt = f"""
You are an Indian legal advisor.

A citizen describes a problem. Provide guidance in this format:

1. Possible Legal Issue
2. Relevant Law (mention section if possible)
3. Suggested Action
4. Authority to approach

Problem:
{problem}
"""

    response = model.generate_content(prompt)

    analysis = response.text

    citizen = User.query.get(session.get("user_id"))

    return render_template(
        "citizenDashboard.html",
        citizen=citizen,
        analysis=analysis
    )
@app.route("/file-case", methods=["POST"])
def file_case():
    if session.get("role") != "citizen":
        return redirect(url_for("login"))

    title = request.form.get("title")
    description = request.form.get("description")

    new_case = Case(
        user_id=session.get("user_id"),
        title=title,
        description=description,
        status="Pending"
    )

    db.session.add(new_case)
    db.session.commit()

    flash("Case submitted successfully!", "success")

    return redirect(url_for("citizen_dashboard"))

    # 🔹 Fetch logged-in citizen from DB
    citizen = User.query.get(session.get("user_id"))

    return render_template(
        "citizenDashboard.html",
        citizen=citizen,              # ✅ THIS WAS MISSING
        chatbot_reply=chatbot_reply
    )

# ---------------- Student DASHBOARD ----------------
@app.route("/student/dashboard")
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    student = Student.query.filter_by(user_id=user_id).first()
    if not student:
        flash("Student profile not found!", "danger")
        return redirect(url_for("index"))

    modules = Module.query.all()

    progress_records = StudentProgress.query.filter_by(student_id=student.id).all()
    progress_dict = {p.module_id: p.progress for p in progress_records}

    return render_template(
        "studentDashboard.html",
        student=student,
        modules=modules,
        progress_dict=progress_dict
    )
@app.route("/student/modules")
def student_modules():
    if session.get("role") != "student":
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    student = Student.query.filter_by(user_id=user_id).first()

    modules = Module.query.all()

    progress_records = StudentProgress.query.filter_by(
        student_id=student.id
    ).all()

    progress_dict = {p.module_id: p.progress for p in progress_records}

    all_modules = []

    for module in modules:
        progress = progress_dict.get(module.id, 0)

        if progress == 100:
            status = "Completed"
        elif progress > 0:
            status = "In Progress"
        else:
            status = "Not Started"

        all_modules.append({
            "id": module.id,
            "title": module.title,
            "icon": module.icon,
            "category": "General Law",
            "progress": progress,
            "status": status,
            "pdf_link": module.pdf_link
        })

    return render_template(
        "modules.html",
        all_modules=all_modules
    )

@app.route("/student/ai-tutor", methods=["GET"])
def ai_tutor():
    if session.get("role") != "student":
        return redirect(url_for("login"))

    student = Student.query.filter_by(
        user_id=session.get("user_id")
    ).first()

    return render_template(
        "AI_Legal_Tutor.html",
        student=student
    )


@app.route("/student/ai-tutor/ask", methods=["POST"])
def ask_ai():
    if session.get("role") != "student":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    question = data.get("question")
    mode = data.get("mode", "chat")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    response = generate_ai_response(question, mode)
    response = re.sub(r"\*\*(.*?)\*\*", r"\1", response)  # remove bold
    response = response.replace("*", "")  # remove remaining stars

    # Save chat history
    chat_entry = ChatHistory(
        user_id=session.get("user_id"),
        message=question,
        response=response
    )
    db.session.add(chat_entry)
    db.session.commit()

    return jsonify({"response": response})

#----------------- ADVOCATE DASHBOARD ----------------
@app.route("/advocate/dashboard")
def advocate_dashboard():
    if session.get("role") != "advocate":
        return redirect(url_for("login"))

    advocate_id = session.get("user_id")

    # Get advocate info
    advocate = User.query.get(advocate_id)

    # Active cases
    active_cases = Case.query.filter(
    (Case.advocate_id == advocate_id) | (Case.advocate_id == None)
).all()

    # Clients
    clients = Client.query.filter_by(
        advocate_id=advocate_id
    ).all()

    # Upcoming appointments
    appointments = Appointment.query.filter_by(
        advocate_id=advocate_id
    ).order_by(Appointment.appointment_date.asc()).limit(5).all()

    return render_template(
        "advocateDashboard.html",
        advocate=advocate,
        active_cases=active_cases,
        clients=clients,
        appointments=appointments
    )

@app.route("/advocate/my-cases")
def advocate_cases():

    if session.get("role") != "advocate":
        return redirect(url_for("login"))

    advocate_id = session.get("user_id")

    advocate = User.query.get(advocate_id)

    cases = Case.query.filter_by(
        advocate_id=advocate_id
    ).all()

    return render_template(
        "advocateCases.html",
        advocate=advocate,
        cases=cases
    )
@app.route("/advocate/clients")
def clients():

    if session.get("role") != "advocate":
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    advocate = Advocate.query.filter_by(user_id=user_id).first()

    clients = Client.query.filter_by(
        advocate_id=advocate.advocate_id
    ).all()

    return render_template(
        "clientManagement.html",
        clients=clients,
        advocate=advocate
    )
@app.route("/advocate/ai-assistant")
def ai_assistant():
    if session.get("role") != "advocate":
        return redirect(url_for("login"))

    advocate_id = session.get("user_id")
    advocate = User.query.get(advocate_id)

    return render_template(
        "Ai-leagal_research.html",
        advocate=advocate
    )
@app.route("/advocate/legal-resources")
def legal_resources():
    if session.get("role") != "advocate":
        return redirect(url_for("login"))

    advocate_id = session.get("user_id")
    advocate = User.query.get(advocate_id)

    return render_template(
        "legal_resources.html",
        advocate=advocate
    )
# ---------------- ACCEPT CASE ----------------
@app.route("/accept-case/<int:case_id>")
def accept_case(case_id):

    if session.get("role") != "advocate":
        return redirect(url_for("login"))

    advocate_id = session.get("user_id")

    case = Case.query.get(case_id)

    if case:
        case.advocate_id = advocate_id
        case.status = "Assigned"
        db.session.commit()

    flash("Case accepted successfully!", "success")

    return redirect(url_for("advocate_dashboard"))
#--------------NGO DASHBOARD----------------
@app.route("/ngo/dashboard")
def ngo_dashboard():

    if session.get("role").lower() != "ngo":
        return redirect(url_for("login"))

    user = User.query.get(session.get("user_id"))
    ngo = NGO.query.filter_by(email=user.email).first()

    return render_template("ngoDashboard.html", ngo=ngo)

#--------------INSTITUTION DASHBOARD----------------
@app.route("/institution/dashboard")
def institution_dashboard():
    if session.get("role").lower() != "institution":
        return redirect(url_for("login"))

    user = User.query.get(session.get("user_id"))
    institution = Institution.query.filter_by(email=user.email).first()

    return render_template(
        "instituttedashboard.html",
        institution=institution
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
@app.route("/ngo/create-campaign", methods=["GET", "POST"])
def create_campaign():

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        location = request.form.get("location")
        date = request.form.get("date")

        new_campaign = Campaign(
            title=title,
            description=description,
            location=location,
            date=date
        )

        db.session.add(new_campaign)
        db.session.commit()

        return "Campaign Added Successfully!"

    return render_template("create_campaign.html")
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

@app.route("/ngo/create-content", methods=["GET", "POST"])
def create_content():

    if request.method == "POST":
        title = request.form.get("title")
        category = request.form.get("category")
        description = request.form.get("description")

        new_content = AwarenessContent(
            title=title,
            category=category,
            description=description
        )

        db.session.add(new_content)
        db.session.commit()

        return "Content Added Successfully!"

    return render_template("create_content.html")

@app.route("/ngo/view-content")
def view_content():

    content = AwarenessContent.query.all()

    return render_template("view_content.html", content=content)

if __name__ == "__main__":
    app.run(debug=True)

class AwarenessContent(db.Model):
    __tablename__ = 'awareness_content'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    category = db.Column(db.String(100))
    description = db.Column(db.Text)