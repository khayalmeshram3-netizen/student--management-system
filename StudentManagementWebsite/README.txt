STUDENT MANAGEMENT SYSTEM WEBSITE
================================

REQUIREMENTS
- Python 3.10 or newer
- VS Code (recommended)

INSTALL AND RUN (Windows / VS Code)
1. Extract this ZIP file.
2. In VS Code choose File > Open Folder and select StudentManagementWebsite.
3. Open Terminal > New Terminal.
4. Create a virtual environment:
   py -m venv .venv
5. Activate it in PowerShell:
   .\.venv\Scripts\Activate.ps1
   If activation is blocked, use Command Prompt terminal and run:
   .venv\Scripts\activate.bat
6. Install Flask:
   py -m pip install -r requirements.txt
7. Start the website:
   py app.py
8. Open this address in your browser:
   http://127.0.0.1:5000

DEMO ADMIN LOGIN
Username: admin
Password: ChangeMe123!

FEATURES
- Admin login and logout
- Dashboard statistics
- Add, list, search, edit and delete students
- SQLite database (students.db is created automatically)
- Automatic grade calculation

IMPORTANT
This is a learning/demo project. Before deploying publicly, set a strong
FLASK_SECRET_KEY, ADMIN_USERNAME and ADMIN_PASSWORD as environment variables,
turn debug mode off, and use HTTPS. Do not publish the demo password.
