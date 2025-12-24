# University Data Management System (UDMS)

## 📌 Project Overview
The University Data Management System (UDMS) is a cloud-based web application designed to manage academic data such as students, courses, enrollments, lecturers, and examination results. The system provides a secure graphical user interface with role-based access control for different types of users.

---

## 🛠 Technologies Used
- **Backend:** Python (Flask)
- **Frontend:** HTML, CSS (Jinja2 Templates)
- **Database:** MySQL (hosted on Railway)
- **Web Server:** Gunicorn
- **Cloud Deployment:** Render
- **Version Control:** Git & GitHub

---

## ☁️ Cloud Architecture
- **Render:** Hosts and runs the Flask web application as a cloud service
- **Railway:** Hosts the MySQL cloud database
- **GitHub:** Stores the source code and enables collaborative development

Architecture flow:
GitHub → Render (Web App) → Railway (MySQL Database)


---

## 🔐 Security
Sensitive information such as database credentials and secret keys are stored securely using environment variables on Render. No confidential data is hard-coded in the source code.

---

## 👥 User Roles
- **Admin:** Manage users, assign lecturers, approve enrollments
- **Staff:** Manage students and enrollments
- **Lecturer:** View assigned courses, enrolled students, and classrooms
- **Student:** View enrollments, exam results, and request course enrollment

---

## 🚀 Live Deployment
The application is deployed online and accessible at:

🔗 https://udms-web.onrender.com

---

## 📂 Installation (Local Development)
To run the project locally:

```bash
pip install -r requirements.txt
python app.py
