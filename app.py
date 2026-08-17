from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "college-enquiry-secret-key"


# =========================
# DATABASE CONNECTION
# =========================

def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row

    connection.execute("""
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    connection.commit()

    return connection


# ==================================================
# SMART CHATBOT FUNCTIONS
# ==================================================

def clean_text(text):

    text = text.lower()

    # b.tech -> b tech
    text = text.replace("b.tech", "b tech")
    text = text.replace("btech", "b tech")

    text = re.sub(r"[^a-z0-9\s]", " ", text)

    text = re.sub(r"\s+", " ", text).strip()

    return text


def get_keywords(text):

    stop_words = {
        "what", "is", "are", "the", "a", "an",
        "of", "to", "for", "in", "on", "at",
        "and", "or", "does", "do", "can",
        "could", "would", "tell", "me", "about",
        "please", "i", "want", "know", "which",
        "how", "much", "many", "your",
        "college", "university", "there",
        "available", "tell", "give",
        "please", "course", "courses"
    }

    words = clean_text(text).split()

    keywords = []

    for word in words:

        if word not in stop_words and len(word) > 2:

            keywords.append(word)

    return keywords


def find_chatbot_answer(user_question):

    connection = get_db_connection()

    # ==================================================
    # 1. CHECK NORMAL CHATBOT DATA
    # ==================================================

    chatbot_data = connection.execute(
        """
        SELECT id, question, answer
        FROM chatbot_data
        """
    ).fetchall()


    # ==================================================
    # 2. GET COURSES FROM DATABASE
    # ==================================================

    courses = connection.execute(
        """
        SELECT *
        FROM courses
        ORDER BY id DESC
        """
    ).fetchall()


    connection.close()


    cleaned_user_question = clean_text(user_question)

    user_keywords = get_keywords(user_question)


    # ==================================================
    # 3. EXACT CHATBOT QUESTION MATCH
    # ==================================================

    for item in chatbot_data:

        database_question = clean_text(item["question"])

        if cleaned_user_question == database_question:

            return item["answer"]


    # ==================================================
    # 4. PARTIAL CHATBOT QUESTION MATCH
    # ==================================================

    for item in chatbot_data:

        database_question = clean_text(item["question"])

        if (
            cleaned_user_question in database_question
            or database_question in cleaned_user_question
        ):

            return item["answer"]


    # ==================================================
    # 5. COURSE DATABASE CHATBOT
    # ==================================================

    if courses:

        # ----------------------------------------------
        # COURSE AVAILABILITY
        # ----------------------------------------------

        availability_words = [
            "course",
            "courses",
            "program",
            "programs",
            "degree",
            "degrees",
            "offer",
            "available"
        ]

        if any(word in cleaned_user_question for word in availability_words):

            if not any(
                word in cleaned_user_question
                for word in [
                    "duration",
                    "fee",
                    "fees",
                    "price",
                    "cost",
                    "year",
                    "years"
                ]
            ):

                course_names = []

                for course in courses:

                    course_names.append(
                        f"🎓 {course['course_name']}"
                    )

                return (
                    "Here are the courses currently available:\n\n"
                    + "\n".join(course_names)
                )


        # ----------------------------------------------
        # FIND COURSE MENTIONED BY USER
        # ----------------------------------------------

        matching_courses = []

        for course in courses:

            course_name = clean_text(course["course_name"])

            course_words = [
                word
                for word in course_name.split()
                if len(word) > 2
            ]

            match_count = 0

            for word in user_keywords:

                if word in course_words:

                    match_count += 1

                else:

                    for course_word in course_words:

                        if (
                            len(word) >= 4
                            and len(course_word) >= 4
                            and (
                                word in course_word
                                or course_word in word
                            )
                        ):

                            match_count += 0.5

                            break

            if match_count > 0:

                matching_courses.append(
                    (course, match_count)
                )


        # Sort best matching courses first

        matching_courses.sort(
            key=lambda x: x[1],
            reverse=True
        )


        # ----------------------------------------------
        # DURATION QUESTION
        # ----------------------------------------------

        if any(
            word in cleaned_user_question
            for word in [
                "duration",
                "how long",
                "years",
                "year",
                "time"
            ]
        ):

            if matching_courses:

                best_score = matching_courses[0][1]

                best_courses = [
                    course
                    for course, score in matching_courses
                    if score >= best_score
                ]

                answers = []

                for course in best_courses:

                    answers.append(
                        f"🎓 {course['course_name']}: "
                        f"{course['duration']}"
                    )

                return (
                    "The course duration is:\n\n"
                    + "\n".join(answers)
                )

            else:

                answers = []

                for course in courses:

                    answers.append(
                        f"🎓 {course['course_name']}: "
                        f"{course['duration']}"
                    )

                return (
                    "Here are the course durations:\n\n"
                    + "\n".join(answers)
                )


        # ----------------------------------------------
        # FEES QUESTION
        # ----------------------------------------------

        if any(
            word in cleaned_user_question
            for word in [
                "fee",
                "fees",
                "price",
                "cost",
                "money",
                "tuition"
            ]
        ):

            if matching_courses:

                best_score = matching_courses[0][1]

                best_courses = [
                    course
                    for course, score in matching_courses
                    if score >= best_score
                ]

                answers = []

                for course in best_courses:

                    answers.append(
                        f"🎓 {course['course_name']}: "
                        f"{course['fees']}"
                    )

                return (
                    "The course fees are:\n\n"
                    + "\n".join(answers)
                )

            else:

                answers = []

                for course in courses:

                    answers.append(
                        f"🎓 {course['course_name']}: "
                        f"{course['fees']}"
                    )

                return (
                    "Here are the course fees:\n\n"
                    + "\n".join(answers)
                )


        # ----------------------------------------------
        # COURSE DETAILS
        # ----------------------------------------------

        if matching_courses:

            best_course = matching_courses[0][0]

            return (
                f"🎓 {best_course['course_name']}\n\n"
                f"⏱️ Duration: {best_course['duration']}\n"
                f"💰 Fees: {best_course['fees']}\n\n"
                f"📝 {best_course['description']}"
            )


    # ==================================================
    # 6. NORMAL KEYWORD MATCHING
    # ==================================================

    best_answer = None
    best_score = 0


    for item in chatbot_data:

        database_keywords = get_keywords(
            item["question"]
        )

        score = 0


        for keyword in user_keywords:

            if keyword in database_keywords:

                score += 1

            else:

                for db_keyword in database_keywords:

                    if (
                        len(keyword) >= 4
                        and len(db_keyword) >= 4
                        and (
                            keyword in db_keyword
                            or db_keyword in keyword
                        )
                    ):

                        score += 0.5

                        break


        if score > best_score:

            best_score = score

            best_answer = item["answer"]


    if best_score >= 1:

        return best_answer


    # ==================================================
    # 7. NO ANSWER
    # ==================================================

    return None




# ==================================================
# PASSWORD SECURITY HELPERS
# ==================================================

def verify_password(stored_password, entered_password):

    # New accounts use Werkzeug password hashes.
    if stored_password.startswith("pbkdf2:") or stored_password.startswith("scrypt:"):
        return check_password_hash(stored_password, entered_password)

    # Existing old accounts may still contain plain-text passwords.
    # Verify them once, then upgrade the stored value to a secure hash.
    return stored_password == entered_password


def upgrade_password_if_needed(connection, table_name, record_id, stored_password, entered_password):

    if stored_password.startswith("pbkdf2:") or stored_password.startswith("scrypt:"):
        return

    hashed_password = generate_password_hash(entered_password)

    connection.execute(
        f"UPDATE {table_name} SET password = ? WHERE id = ?",
        (hashed_password, record_id)
    )

    connection.commit()


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():

    user = None

    if "user_id" in session:
        user = session["user_name"]

    return render_template(
        "index.html",
        user=user
    )


# ==================================================
# REGISTER
# ==================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match!"

        connection = get_db_connection()

        try:

            hashed_password = generate_password_hash(password)

            connection.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, hashed_password)
            )

            connection.commit()

        except sqlite3.IntegrityError:

            connection.close()

            return "This email is already registered!"

        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# ==================================================
# USER LOGIN
# ==================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if user and verify_password(user["password"], password):

            upgrade_password_if_needed(
                connection,
                "users",
                user["id"],
                user["password"],
                password
            )

            connection.close()


            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            return redirect(url_for("home"))

        return "Invalid email or password!"

    return render_template("login.html")


# ==================================================
# USER LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# ==================================================
# STUDENT COURSES
# ==================================================

@app.route("/courses")
def public_courses():

    connection = get_db_connection()

    courses = connection.execute(
        """
        SELECT *
        FROM courses
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "courses_public.html",
        courses=courses,
        user=session.get("user_name")
    )



# ==================================================
# ABOUT PAGE
# ==================================================

@app.route("/about")
def about():

    return render_template(
        "about.html",
        user=session.get("user_name")
    )



# ==================================================
# CONTACT PAGE
# ==================================================

@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        message = request.form["message"].strip()

        if not name or not email or not message:
            return "All fields are required!"

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO contact_messages
            (name, email, message)
            VALUES (?, ?, ?)
            """,
            (name, email, message)
        )

        connection.commit()
        connection.close()

        return render_template(
            "contact.html",
            user=session.get("user_name"),
            success=True,
            name=name,
            email=email
        )

    return render_template(
        "contact.html",
        user=session.get("user_name"),
        success=False
    )


# ==================================================
# STUDENT CHATBOT
# ==================================================

@app.route("/chat", methods=["GET", "POST"])
def chat():

    if "user_id" not in session:
        return redirect(url_for("login"))

    question = None
    answer = None

    if request.method == "POST":

        question = request.form["question"].strip()

        if question:

            answer = find_chatbot_answer(question)

            if not answer:

                answer = (
                    "Sorry, I couldn't understand your question yet. 🤔\n\n"
                    "Please try asking about courses, fees, admissions, "
                    "departments, facilities or other college information."
                )

    return render_template(
        "chat.html",
        user=session.get("user_name"),
        question=question,
        answer=answer
    )


# ==================================================
# STUDENT SUGGESTION PAGE
# ==================================================

@app.route("/suggestion", methods=["GET"])
def suggestion():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "suggestion_form.html",
        user=session.get("user_name")
    )


# ==================================================
# SUBMIT SUGGESTION
# ==================================================

@app.route("/suggestion", methods=["POST"])
def submit_suggestion():

    if "user_id" not in session:
        return redirect(url_for("login"))

    message = request.form["message"].strip()

    if not message:
        return "Suggestion cannot be empty!"

    user_name = session["user_name"]
    user_email = session["user_email"]

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO suggestions
        (
            user_name,
            user_email,
            message
        )
        VALUES (?, ?, ?)
        """,
        (
            user_name,
            user_email,
            message
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("home"))


# ==================================================
# ADMIN LOGIN
# ==================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_db_connection()

        admin = connection.execute(
            """
            SELECT *
            FROM admins
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        if admin and verify_password(admin["password"], password):

            upgrade_password_if_needed(
                connection,
                "admins",
                admin["id"],
                admin["password"],
                password
            )

            connection.close()


            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]

            return redirect(url_for("admin_dashboard"))

        return "Invalid admin username or password!"

    return render_template("admin_login.html")


# ==================================================
# ADMIN DASHBOARD
# ==================================================

@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    total_users = connection.execute(
        "SELECT COUNT(*) AS count FROM users"
    ).fetchone()["count"]

    total_courses = connection.execute(
        "SELECT COUNT(*) AS count FROM courses"
    ).fetchone()["count"]

    total_questions = connection.execute(
        "SELECT COUNT(*) AS count FROM chatbot_data"
    ).fetchone()["count"]

    total_suggestions = connection.execute(
        "SELECT COUNT(*) AS count FROM suggestions"
    ).fetchone()["count"]

    total_messages = connection.execute(
        "SELECT COUNT(*) AS count FROM contact_messages"
    ).fetchone()["count"]

    connection.close()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_courses=total_courses,
        total_questions=total_questions,
        total_suggestions=total_suggestions,
        total_messages=total_messages
    )


# ==================================================
# MANAGE STUDENTS
# ==================================================

@app.route("/admin/students")
def admin_students():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    students = connection.execute(
        """
        SELECT id, name, email
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "students.html",
        students=students
    )


@app.route(
    "/admin/students/delete/<int:user_id>",
    methods=["POST"]
)
def delete_student(user_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    connection.execute(
        "DELETE FROM users WHERE id = ?",
        (user_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("admin_students"))


# ==================================================
# MANAGE COURSES
# ==================================================

@app.route("/admin/courses")
def admin_courses():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    courses = connection.execute(
        """
        SELECT *
        FROM courses
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "courses.html",
        courses=courses
    )


@app.route(
    "/admin/courses/add",
    methods=["POST"]
)
def add_course():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    course_name = request.form["course_name"]
    duration = request.form["duration"]
    fees = request.form["fees"]
    description = request.form["description"]

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO courses
        (
            course_name,
            duration,
            fees,
            description
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            course_name,
            duration,
            fees,
            description
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("admin_courses"))


@app.route(
    "/admin/courses/delete/<int:course_id>",
    methods=["POST"]
)
def delete_course(course_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    connection.execute(
        "DELETE FROM courses WHERE id = ?",
        (course_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("admin_courses"))


# ==================================================
# MANAGE CHATBOT
# ==================================================

@app.route("/admin/chatbot")
def admin_chatbot():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    chatbot_data = connection.execute(
        """
        SELECT *
        FROM chatbot_data
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "chatbot.html",
        chatbot_data=chatbot_data
    )


@app.route(
    "/admin/chatbot/add",
    methods=["POST"]
)
def add_chatbot_data():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    question = request.form["question"]
    answer = request.form["answer"]

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO chatbot_data
        (question, answer)
        VALUES (?, ?)
        """,
        (question, answer)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("admin_chatbot"))


@app.route(
    "/admin/chatbot/edit/<int:chatbot_id>",
    methods=["GET", "POST"]
)
def edit_chatbot(chatbot_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    if request.method == "GET":

        chatbot = connection.execute(
            """
            SELECT *
            FROM chatbot_data
            WHERE id = ?
            """,
            (chatbot_id,)
        ).fetchone()

        connection.close()

        if not chatbot:
            return "Chatbot question not found!"

        return render_template(
            "edit_chatbot.html",
            chatbot=chatbot
        )

    question = request.form["question"]
    answer = request.form["answer"]

    connection.execute(
        """
        UPDATE chatbot_data
        SET question = ?,
            answer = ?
        WHERE id = ?
        """,
        (
            question,
            answer,
            chatbot_id
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("admin_chatbot"))


@app.route(
    "/admin/chatbot/delete/<int:chatbot_id>",
    methods=["POST"]
)
def delete_chatbot_data(chatbot_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    connection.execute(
        "DELETE FROM chatbot_data WHERE id = ?",
        (chatbot_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("admin_chatbot"))


# ==================================================
# ADMIN SUGGESTIONS
# ==================================================

@app.route("/admin/suggestions")
def admin_suggestions():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    suggestions = connection.execute(
        """
        SELECT *
        FROM suggestions
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "suggestions.html",
        suggestions=suggestions
    )


@app.route(
    "/admin/suggestions/delete/<int:suggestion_id>",
    methods=["POST"]
)
def delete_suggestion(suggestion_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    connection.execute(
        "DELETE FROM suggestions WHERE id = ?",
        (suggestion_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("admin_suggestions"))


# ==================================================
# ADMIN CONTACT MESSAGES
# ==================================================

@app.route("/admin/messages")
def admin_messages():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    messages = connection.execute(
        """
        SELECT *
        FROM contact_messages
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "messages.html",
        messages=messages
    )


@app.route("/admin/messages/delete/<int:message_id>", methods=["POST"])
def delete_message(message_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    connection.execute(
        "DELETE FROM contact_messages WHERE id = ?",
        (message_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("admin_messages"))


# ==================================================
# ADMIN LOGOUT
# ==================================================

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin_id", None)
    session.pop("admin_username", None)

    return redirect(url_for("admin_login"))


# ==================================================
# ERROR HANDLERS
# ==================================================

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template("500.html"), 500


# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == "__main__":

    app.run(debug=True)