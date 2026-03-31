from flask import Flask, render_template, request, redirect, url_for, session , jsonify
from flask_sqlalchemy import SQLAlchemy
from flask import flash
import re
import google.generativeai as genai
from dotenv import load_dotenv
import os
from sqlalchemy import and_, or_


# ---------------- APP CONFIG ----------------
load_dotenv()

app = Flask(__name__)
app.secret_key = "lawconnect_secret_key"
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    model_name="gemini-3-flash-preview",
    system_instruction="You are a specialized Indian Legal AI Tutor. Provide precise citations from IPC, CrPC, and the Constitution. Adjust your tone based on the mode: Chat (helpful tutor), MCQ (test provider), Debate (critical opponent), or Trial (presiding judge)."
)

def is_legal_query(query):
    legal_keywords = [
        "law", "legal", "ipc", "crpc", "bns", "bnss", "constitution",
        "court", "judge", "fir", "police", "bail", "section",
        "article", "case", "rights", "advocate", "crime",
        "punishment", "contract", "agreement", "cybercrime",
        "harassment", "divorce", "property", "legal notice"
    ]

    query = query.lower()
    return any(word in query for word in legal_keywords)


def generate_ai_response(user_query, mode="chat"):

    try:
        # 🔴 HARD BLOCK (MOST IMPORTANT)
        if not is_legal_query(user_query):
            return "⚠️ I can only assist with legal-related queries under Indian law."

        mode_instructions = {

            "chat": """
You are a STRICT Indian Legal AI Assistant.

Answer ONLY legal queries.

Follow STRICT format:

1. Definition
2. Relevant Statutory Provision (with section/article number)
3. Landmark Case
4. Practical Illustration
5. Key Legal Principle

Use:
- Constitution of India
- IPC / BNS
- CrPC / BNSS

Maintain professional academic tone.
""",

            "mcq": """
Generate ONE UPSC Judiciary level MCQ.

Rules:
- 4 options (A, B, C, D)
- Only ONE correct
- Do NOT reveal answer
- End with: "Reply with A/B/C/D to answer."
""",

            "debate": """
Act as a senior constitutional lawyer opposing the user.

- Identify flaws
- Use legal doctrines
- Cite statutes/cases

End with:
"How do you respond to this legal objection?"
""",

            "trial": """
Act as a High Court Judge.

Structure:

1. Facts Presented
2. Issues for Determination
3. Relevant Law
4. Judicial Reasoning
5. Final Order

Use formal judicial tone.
"""
        }

        # 🔹 Build prompt
        prompt = f"""
STRICT INSTRUCTION:
- Answer ONLY legal queries.
- If not legal → reply EXACTLY:
"⚠️ I can only assist with legal-related queries under Indian law."

Mode: {mode}

Instruction:
{mode_instructions.get(mode, mode_instructions["chat"])}

User Query:
{user_query}
"""

        response = model.generate_content(prompt)

        return response.text.strip()

    except Exception as e:
        print("Gemini Error:", e)
        return "⚠️ AI system temporarily unavailable. Please try again."
# DB config
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Surya%407075@localhost:3306/lawconnect_ai"
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
    case_pdf = db.Column(db.Text)
    next_hearing = db.Column(db.Date) 

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
# 🔹 System Prompt (Legal-only restriction)
LEGAL_SYSTEM_PROMPT = """
You are a legal assistant chatbot specialized ONLY in legal topics.

Rules:
- Answer ONLY legal-related questions (laws, rights, FIR, police, courts, IPC, cybercrime, etc.)
- If the question is NOT legal, politely refuse.
- Do NOT answer general, technical, casual, or unrelated questions.

If the query is not legal, respond with:
"⚠️ I can only assist with legal-related queries. Please ask a legal question."

Keep answers simple, clear, and helpful for common people.
"""


# 🔹 AI Response Function
def generate_ai_response(query, system_prompt=None):
    model = genai.GenerativeModel("gemini-3-flash-preview")

    if system_prompt:
        full_prompt = f"{system_prompt}\n\nUser: {query}"
    else:
        full_prompt = query

    response = model.generate_content(full_prompt)

    return response.text



# 🔹 Route
@app.route("/citizen/dashboard", methods=["GET", "POST"])
def citizen_dashboard():
    if session.get("role") != "citizen":
        return redirect(url_for("login"))

    chatbot_reply = None

    if request.method == "POST":
        query = request.form.get("query")

        if query:
            chatbot_reply = generate_ai_response(
                query,
                system_prompt=LEGAL_SYSTEM_PROMPT
            )

            # 🔹 Clean unwanted formatting
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

    # 🔴 HARD BLOCK (ADD THIS)
    if not is_legal_query(question):
        return jsonify({
            "response": "⚠️ I can only assist with legal-related queries under Indian law."
        })

    # ✅ Only legal queries reach AI
    response = generate_ai_response(question, mode)

    # Clean formatting
    response = re.sub(r"\*\*(.*?)\*\*", r"\1", response)
    response = response.replace("*", "")

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
from sqlalchemy import and_, or_
from datetime import datetime

@app.route("/advocate/dashboard")
def advocate_dashboard():
    if session.get("role") != "advocate":
        return redirect(url_for("login"))

    advocate_id = session.get("user_id")

    # ✅ Advocate info
    advocate = User.query.get(advocate_id)

    # ✅ Active cases (exclude rejected + sort by hearing date)
    active_cases = Case.query.filter(
        and_(
            or_(Case.advocate_id == advocate_id, Case.advocate_id == None),
            Case.status != "Rejected"
        )
    ).order_by(
        Case.next_hearing.is_(None),   # 🔥 NULLs last
        Case.next_hearing.asc()        # 🔥 earliest first
    ).all()

    # ✅ Clients (from cases)
    clients = User.query.join(
        Case, User.id == Case.user_id
    ).filter(
        Case.advocate_id == advocate_id,
        Case.status != "Rejected"
    ).distinct().all()

    # ✅ Upcoming appointments
    appointments = Appointment.query.filter_by(
        advocate_id=advocate_id
    ).order_by(Appointment.appointment_date.asc()).limit(5).all()

    # ✅ Today's hearings (NEW 🔥)
    today = datetime.now().date()

    todays_hearings = Case.query.filter(
        Case.advocate_id == advocate_id,
        Case.next_hearing != None
    ).all()

    todays_hearings = [
        c for c in todays_hearings 
        if c.next_hearing == today   # ✅ FIX
    ]

    return render_template(
        "advocateDashboard.html",
        advocate=advocate,
        active_cases=active_cases,
        clients=clients,
        appointments=appointments,
        todays_hearings=todays_hearings,   # 🔥 pass this
        now=datetime.now()                 # 🔥 for template use
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

@app.route("/advocate/reject-case/<int:case_id>")
def reject_case(case_id):

    if session.get("role") != "advocate":
        return redirect(url_for("login"))

    advocate_id = session.get("user_id")

    case = Case.query.get(case_id)

    if case and case.advocate_id == advocate_id:
        case.advocate_id = None   # 🔥 unassign advocate
        case.status = "Rejected"  # optional
        db.session.commit()

        flash("Case rejected successfully!", "success")

    else:
        flash("Error occurred.", "danger")

    return redirect(url_for("advocate_cases"))

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
# 🔹 System Prompt (Strict Legal Assistant)
LEGAL_SYSTEM_PROMPT = """
You are a STRICT legal research assistant for advocates.

- Answer ONLY legal-related queries (case law, IPC, CrPC, contracts, legal drafting, etc.)
- Provide structured, professional answers
- If NOT legal → respond EXACTLY:
"⚠️ I can only assist with legal-related queries."

Keep responses precise and useful for legal professionals.
"""




def generate_ai_response(query, system_prompt=None):
    model = genai.GenerativeModel("gemini-2.5-flash")

    if system_prompt:
        full_prompt = f"{system_prompt}\n\nUser Query:\n{query}"
    else:
        full_prompt = query

    response = model.generate_content(full_prompt)
    return response.text


# 🔹 Updated Route
@app.route("/advocate/ai-assistant", methods=["GET", "POST"])
def ai_assistant():
    if session.get("role") != "advocate":
        return redirect(url_for("login"))

    advocate_id = session.get("user_id")
    advocate = User.query.get(advocate_id)

    ai_reply = None

    if request.method == "POST":
        query = request.form.get("query")

        if query:
            ai_reply = generate_ai_response(
                query,
                system_prompt=LEGAL_SYSTEM_PROMPT
            )

            # Clean formatting
            ai_reply = ai_reply.replace("*", "")
            ai_reply = ai_reply.replace("#", "")

    return render_template(
        "Ai-leagal_research.html",
        advocate=advocate,
        ai_reply=ai_reply
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



@app.route("/institution/dashboard", methods=["GET", "POST"])
def institution_dashboard():
    if session.get("role") != "institution":
        return redirect(url_for("login"))

    user = User.query.get(session.get("user_id"))
    institution = Institution.query.first()

    # ✅ HANDLE FORM SUBMISSION
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        pdf_link = request.form.get("pdf_link")
        file = request.files.get("module_file")

        final_link = None

        # 🔥 OPTION 1: FILE UPLOAD
        if file and file.filename != "":
            upload_folder = "static/uploads"

            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            filepath = os.path.join(upload_folder, file.filename)
            file.save(filepath)

            # store relative path (BEST PRACTICE)
            final_link = f"uploads/{file.filename}"

        # 🔥 OPTION 2: LINK INPUT
        elif pdf_link:
            final_link = pdf_link

        # ✅ SAVE TO DATABASE
        if title and final_link:
            new_module = Module(
                title=title,
                description=description,
                pdf_link=final_link
            )

            db.session.add(new_module)
            db.session.commit()

    # ✅ GET STUDENTS
    students = User.query.filter_by(role="student").all()

    # ✅ GET MODULES
    modules = Module.query.all()

    return render_template(
        "instituttedashboard.html",
        institution=institution,
        students=students,
        modules=modules
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