# CampusConnect — Student Placement Portal

A student placement management web application built using Python, Streamlit, Pandas, and SQLite. It helps students explore job opportunities, check eligibility, apply for jobs, and track application status.

## Features

- Student registration and login
- Secure password hashing
- Role-based access for students and administrators
- Placement dashboard and analytics
- Browse and filter jobs by job type and package
- Eligibility checking based on branch and CGPA
- Apply for jobs with duplicate-application prevention
- View personal applications and track their status
- Admin dashboard to add, edit, and delete job listings
- Admin can update application statuses
- SQLite database created automatically on first run

## Technologies Used

- Python
- Streamlit
- Pandas
- SQLite
- streamlit-authenticator

## Project Setup (Windows)

1. Install Python 3.10+ and VS Code.
2. Open the project folder in VS Code.
3. Open Terminal → New Terminal.
4. Create a virtual environment:

```bash
py -m venv .venv
```

5. Activate the environment:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```bat
.venv\Scripts\activate.bat
```

6. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

7. Run the application:

```bash
python -m streamlit run app.py
```

The application will open in your browser. The `placement_portal.db` database is created automatically.

## Demo Admin Login

- Email: `admin@campusconnect.com`
- Password: `Admin@123`

**Note:** These are demo credentials. Change them and use stronger secret management before any public deployment.

## Limitations

CampusConnect is a portfolio/demo MVP and is not intended for production use. Before public deployment, additional security testing, stronger credential management, database protection, automated testing, and verified job data should be implemented.

## Author

Developed as a student portfolio project.