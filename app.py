import os
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv

from db import fetch_one, fetch_all, execute

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")


# -----------------
# Helpers
# -----------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def role_in(*allowed):
    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = session.get("user", {})
            role = (user.get("Role") or "").lower()
            if role not in [a.lower() for a in allowed]:
                flash("Access denied.", "error")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return wrapper
    return deco


# -----------------
# Auth
# -----------------
@app.route("/")
def home():
    return redirect(url_for("dashboard")) if "user" in session else redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Please enter username and password.", "error")
            return render_template("login.html")

        # IMPORTANT: table is useraccounts (lowercase)
        user = fetch_one(
            """
            SELECT User_ID, Username, Role, Student_ID, Lecturer_ID
            FROM useraccounts
            WHERE Username=%s AND Password=%s
            """,
            (username, password),
        )

        if not user:
            flash("Invalid username or password.", "error")
            return render_template("login.html")

        session["user"] = user
        return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -----------------
# Dashboard
# -----------------
@app.route("/dashboard")
@login_required
def dashboard():
    user = session["user"]
    role = (user.get("Role") or "").lower()
    return render_template("dashboard.html", user=user, role=role)


# -----------------
# Admin/Staff: Students CRUD
# -----------------
@app.route("/students", methods=["GET", "POST"])
@login_required
@role_in("admin", "staff")
def students():
    if request.method == "POST":
        action = request.form.get("action")

        # NOTE: these columns must match your students table
        student_id = request.form.get("student_id", "").strip()
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip() or None
        address = request.form.get("address", "").strip() or None
        doa = request.form.get("date_of_admission", "").strip()  # YYYY-MM-DD
        dept_id = request.form.get("department_id", "").strip()

        try:
            if action == "create":
                if not (first_name and last_name and email and doa and dept_id):
                    flash("Missing required fields.", "error")
                else:
                    execute(
                        """
                        INSERT INTO students
                        (First_Name, Last_Name, Email, Phone, Address, Date_of_Admission, Department_ID)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (first_name, last_name, email, phone, address, doa, dept_id),
                    )
                    flash("Student created.", "success")

            elif action == "update":
                if not student_id:
                    flash("Student_ID required for update.", "error")
                else:
                    execute(
                        """
                        UPDATE students
                        SET First_Name=%s, Last_Name=%s, Email=%s, Phone=%s, Address=%s,
                            Date_of_Admission=%s, Department_ID=%s
                        WHERE Student_ID=%s
                        """,
                        (first_name, last_name, email, phone, address, doa, dept_id, student_id),
                    )
                    flash("Student updated.", "success")

            elif action == "delete":
                if not student_id:
                    flash("Student_ID required for delete.", "error")
                else:
                    execute("DELETE FROM students WHERE Student_ID=%s", (student_id,))
                    flash("Student deleted.", "success")

        except Exception as e:
            flash(f"DB error: {e}", "error")

        return redirect(url_for("students"))

    students_rows = fetch_all(
        """
        SELECT Student_ID, First_Name, Last_Name, Email, Phone, Address, Date_of_Admission, Department_ID
        FROM students
        ORDER BY Student_ID DESC
        """
    )
    departments = fetch_all("SELECT Department_ID, Department_Name FROM departments ORDER BY Department_Name")

    return render_template("students.html", students=students_rows, departments=departments)


# -----------------
# Admin/Staff: Enrollment (Procedure OR direct insert)
# -----------------
@app.route("/enrollment", methods=["GET", "POST"])
@login_required
@role_in("admin", "staff")
def enrollment():
    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        course_id = request.form.get("course_id", "").strip()
        semester_id = request.form.get("semester_id", "").strip()

        if not (student_id and course_id and semester_id):
            flash("Student_ID, Course_ID, Semester_ID are required.", "error")
            return redirect(url_for("enrollment"))

        try:
            # If you have a stored procedure named EnrollStudent use this:
            # execute("CALL EnrollStudent(%s,%s,%s)", (student_id, course_id, semester_id))

            # If you DON'T have procedure, use direct insert:
            execute(
                """
                INSERT INTO enrollment (Student_ID, Course_ID, Semester_ID, Enrollment_Date)
                VALUES (%s,%s,%s,CURDATE())
                """,
                (student_id, course_id, semester_id),
            )
            flash("Enrollment added.", "success")
        except Exception as e:
            flash(f"Enrollment failed: {e}", "error")

        return redirect(url_for("enrollment"))

    students_list = fetch_all("SELECT Student_ID, First_Name, Last_Name FROM students ORDER BY Student_ID DESC")
    courses_list = fetch_all("SELECT Course_ID, Course_Code, Course_Name FROM courses ORDER BY Course_Code")
    semester_list = fetch_all("SELECT Semester_ID, Semester_Name FROM semester ORDER BY Semester_ID DESC")

    enrollments = fetch_all(
        """
        SELECT e.Enrollment_ID, e.Student_ID,
               CONCAT(s.First_Name,' ',s.Last_Name) AS Student_Name,
               e.Course_ID, c.Course_Code, c.Course_Name,
               e.Semester_ID, sem.Semester_Name,
               e.Enrollment_Date, e.Grade
        FROM enrollment e
        JOIN students s ON e.Student_ID = s.Student_ID
        JOIN courses c ON e.Course_ID = c.Course_ID
        JOIN semester sem ON e.Semester_ID = sem.Semester_ID
        ORDER BY e.Enrollment_ID DESC
        """
    )

    return render_template(
        "enrollment.html",
        students_list=students_list,
        courses_list=courses_list,
        semester_list=semester_list,
        enrollments=enrollments,
    )


# -----------------
# Admin: User accounts (create + reset password)
# -----------------
@app.route("/user-accounts", methods=["GET", "POST"])
@login_required
@role_in("admin")
def user_accounts():
    if request.method == "POST":
        action = request.form.get("action")

        user_id = request.form.get("user_id", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "").strip()
        student_id = request.form.get("student_id", "").strip() or None
        lecturer_id = request.form.get("lecturer_id", "").strip() or None

        try:
            if action == "create":
                if not (username and password and role):
                    flash("Username, Password, Role required.", "error")
                else:
                    # link rules
                    if role.lower() == "student" and not student_id:
                        flash("Student role requires Student_ID.", "error")
                        return redirect(url_for("user_accounts"))
                    if role.lower() == "lecturer" and not lecturer_id:
                        flash("Lecturer role requires Lecturer_ID.", "error")
                        return redirect(url_for("user_accounts"))

                    if role.lower() != "student":
                        student_id = None
                    if role.lower() != "lecturer":
                        lecturer_id = None

                    execute(
                        """
                        INSERT INTO useraccounts (Username, Password, Role, Student_ID, Lecturer_ID)
                        VALUES (%s,%s,%s,%s,%s)
                        """,
                        (username, password, role, student_id, lecturer_id),
                    )
                    flash("Account created.", "success")

            elif action == "reset":
                if not (user_id and password):
                    flash("Select user + enter new password.", "error")
                else:
                    execute("UPDATE useraccounts SET Password=%s WHERE User_ID=%s", (password, user_id))
                    flash("Password updated.", "success")

            elif action == "delete":
                if not user_id:
                    flash("Select user to delete.", "error")
                else:
                    execute("DELETE FROM useraccounts WHERE User_ID=%s", (user_id,))
                    flash("Account deleted.", "success")

        except Exception as e:
            msg = str(e).lower()
            if "duplicate" in msg or "unique" in msg:
                flash("Username already exists.", "error")
            else:
                flash(f"DB error: {e}", "error")

        return redirect(url_for("user_accounts"))

    accounts = fetch_all("SELECT User_ID, Username, Role, Student_ID, Lecturer_ID FROM useraccounts ORDER BY User_ID DESC")
    students_list = fetch_all("SELECT Student_ID, First_Name, Last_Name FROM students ORDER BY Student_ID DESC")
    lecturers_list = fetch_all("SELECT Lecturer_ID, First_Name, Last_Name FROM lecturers ORDER BY Lecturer_ID DESC")

    return render_template(
        "user_accounts.html",
        accounts=accounts,
        students_list=students_list,
        lecturers_list=lecturers_list,
    )


# -----------------
# Lecturer: Courses + students
# -----------------
@app.route("/lecturer")
@login_required
@role_in("lecturer")
def lecturer_dashboard():
    user = session["user"]
    lecturer_id = user.get("Lecturer_ID")

    if not lecturer_id:
        flash("Your lecturer account is not linked to Lecturer_ID.", "error")
        return redirect(url_for("dashboard"))

    courses = fetch_all(
        "SELECT Course_ID, Course_Code, Course_Name FROM courses WHERE Lecturer_ID=%s ORDER BY Course_Code",
        (lecturer_id,),
    )

    # optionally show enrolled students for a selected course
    course_id = request.args.get("course_id", "").strip()
    enrolled = []
    if course_id:
        enrolled = fetch_all(
            """
            SELECT
                s.Student_ID,
                CONCAT(s.First_Name,' ',s.Last_Name) AS Student_Name,
                sem.Semester_Name,
                e.Enrollment_Date,
                e.Grade
            FROM enrollment e
            JOIN students s ON e.Student_ID = s.Student_ID
            JOIN semester sem ON e.Semester_ID = sem.Semester_ID
            WHERE e.Course_ID = %s
            ORDER BY sem.Semester_ID DESC, s.Student_ID ASC
            """,
            (course_id,),
        )

    return render_template("lecturer_dashboard.html", courses=courses, enrolled=enrolled, selected_course=course_id)


# -----------------
# Student: My Enrollments
# -----------------
@app.route("/my-enrollments")
@login_required
@role_in("student")
def my_enrollments():
    user = session["user"]
    student_id = user.get("Student_ID")

    if not student_id:
        flash("Your student account is not linked to Student_ID.", "error")
        return redirect(url_for("dashboard"))

    rows = fetch_all(
        """
        SELECT
            e.Enrollment_ID,
            c.Course_Code,
            c.Course_Name,
            sem.Semester_Name,
            e.Enrollment_Date,
            e.Grade
        FROM enrollment e
        JOIN courses c ON e.Course_ID = c.Course_ID
        JOIN semester sem ON e.Semester_ID = sem.Semester_ID
        WHERE e.Student_ID=%s
        ORDER BY e.Enrollment_ID DESC
        """,
        (student_id,),
    )
    return render_template("my_enrollments.html", rows=rows)


# -----------------
# Student: My Exam Results
# -----------------
@app.route("/my-results")
@login_required
@role_in("student")
def my_results():
    user = session["user"]
    student_id = user.get("Student_ID")

    if not student_id:
        flash("Your student account is not linked to Student_ID.", "error")
        return redirect(url_for("dashboard"))

    rows = fetch_all(
        """
        SELECT
            er.Result_ID,
            c.Course_Code,
            c.Course_Name,
            ex.Exam_Type,
            ex.Exam_Date,
            er.Marks AS Mark,
            er.Grade
        FROM examresults er
        JOIN exams ex ON er.Exam_ID = ex.Exam_ID
        JOIN courses c ON ex.Course_ID = c.Course_ID
        WHERE er.Student_ID = %s
        ORDER BY ex.Exam_Date DESC
        """,
        (student_id,)
    )

    return render_template("my_results.html", rows=rows)


if __name__ == "__main__":
    app.run(debug=True)
