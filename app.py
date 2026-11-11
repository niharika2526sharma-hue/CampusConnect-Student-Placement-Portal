import sqlite3
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st
import re
import streamlit_authenticator as stauth

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "placement_portal.db"

st.set_page_config(
    page_title="CampusConnect | Student Placement Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Database ----------
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                location TEXT NOT NULL,
                package_lpa REAL NOT NULL,
                min_cgpa REAL NOT NULL,
                eligible_branches TEXT NOT NULL,
                job_type TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                student_email TEXT NOT NULL,
                student_branch TEXT NOT NULL,
                student_cgpa REAL NOT NULL,
                job_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Applied',
                applied_at TEXT NOT NULL,
                UNIQUE(student_email, job_id),
                FOREIGN KEY(job_id) REFERENCES jobs(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student'
            )
        """)

        admin = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            ("admin@campusconnect.com",)
        ).fetchone()

        if admin is None:
            conn.execute(
                """
                INSERT INTO users (name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                (
                    "Admin",
                    "admin@campusconnect.com",
                    hash_password("Admin@123"),
                    "admin"
                )
            )
    
        count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        if count == 0:
            seed_jobs = [
                ("TechNova", "Python Developer Intern", "Bengaluru / Remote", 6.0, 6.0, "CSE, AIML, IT", "Internship", "Build Python features, write tests, and work with APIs."),
                ("DataBridge", "Junior Data Analyst", "Chandigarh", 5.5, 6.5, "CSE, AIML, IT, Data Science", "Full-time", "Clean datasets, create reports, and communicate insights."),
                ("CloudSprint", "Software Engineer Trainee", "Mohali", 7.0, 7.0, "CSE, AIML, IT, ECE", "Full-time", "Work with a team to develop and test software modules."),
                ("AIWorks", "Machine Learning Intern", "Remote", 8.0, 6.0, "CSE, AIML, Data Science", "Internship", "Prepare data, evaluate ML models, and document experiments."),
                ("WebNest", "Frontend Developer Intern", "Remote", 4.5, 6.0, "CSE, AIML, IT", "Internship", "Build accessible web interfaces and collaborate on UI improvements."),
            ]
            conn.executemany("""
                INSERT INTO jobs
                (company, role, location, package_lpa, min_cgpa, eligible_branches, job_type, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [(*job, datetime.now().strftime("%Y-%m-%d %H:%M")) for job in seed_jobs])
        conn.commit()

def load_jobs():
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM jobs ORDER BY id DESC", conn)

def load_applications(email=None):
    with get_connection() as conn:
        query = """
            SELECT a.id, a.student_name, a.student_email, a.student_branch,
                   a.student_cgpa, j.company, j.role, j.location, j.package_lpa,
                   a.status, a.applied_at
            FROM applications a JOIN jobs j ON a.job_id = j.id
        """
        if email:
            return pd.read_sql_query(
                query + " WHERE LOWER(a.student_email)=LOWER(?) ORDER BY a.id DESC",
                conn,
                params=(email,)
            )
        return pd.read_sql_query(query + " ORDER BY a.id DESC", conn)


def is_valid_email(email):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return re.match(pattern, email.strip()) is not None


def hash_password(password):
    return stauth.Hasher.hash(password)


def verify_password(password, hashed_password):
    return stauth.Hasher.check_pw(password, hashed_password)

def register_user(name, email, password):
    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (name, email, password_hash, role)
                VALUES (?, ?, ?, 'student')
                """,
                (name.strip(), email.strip().lower(), hash_password(password))
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(email, password):
    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT name, email, password_hash, role
            FROM users
            WHERE LOWER(email) = LOWER(?)
            """,
            (email.strip(),)
        ).fetchone()

    if user and verify_password(password, user[2]):
        return {
            "name": user[0],
            "email": user[1],
            "role": user[3]
        }

    return None

init_db()


# ---------- Styling ----------
if "user" not in st.session_state:
    st.session_state.user = None
st.markdown("""
<style>
    .block-container {padding-top: 1.7rem; padding-bottom: 2rem;}
    .hero {
        padding: 1.35rem 1.5rem; border-radius: 18px;
        background: linear-gradient(115deg, #13294b 0%, #22577a 60%, #38a3a5 100%);
        color: white; margin-bottom: 1rem;
    }
    .hero h1 {color: white; margin: 0; font-size: 2rem;}
    .hero p {color: #e6f4f1; margin: .45rem 0 0 0;}
    .job-card {
        padding: 1rem 1.1rem; border: 1px solid rgba(128,128,128,.3);
        border-radius: 14px; margin-bottom: .8rem;
    }
    .muted {opacity: .75; font-size: .9rem;}
</style>
""", unsafe_allow_html=True)

if st.session_state.user is None:
    page = "Login"
else:
    st.sidebar.title("🎓 CampusConnect")
    st.sidebar.caption("Student Placement Portal")

    if st.session_state.user["role"] == "admin":
        pages = [
            "Dashboard",
            "Student Dashboard",
            "Browse Jobs",
            "My Applications",
            "Admin: Manage Jobs",
        ]
    else:
        pages = [
            "Dashboard",
            "Student Dashboard",
            "Browse Jobs",
            "My Applications",
        ]

    page = st.sidebar.radio("Navigate", pages)

    st.sidebar.divider()
    st.sidebar.write(f"Welcome, {st.session_state.user['name']}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    st.sidebar.caption("Demo project • Streamlit + SQLite")

jobs = load_jobs()

# ---------- Dashboard ----------
if page == "Dashboard":
    st.markdown("""
    <div class="hero">
      <h1>CampusConnect</h1>
      <p>Your campus placement journey, organised in one place.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Active Opportunities", len(jobs))
    c2.metric("Companies", int(jobs["company"].nunique()) if not jobs.empty else 0)
    apps = load_applications()
    c3.metric("Applications Submitted", len(apps))

    st.subheader("Featured opportunities")
    if jobs.empty:
        st.info("No jobs added yet. Open Admin: Manage Jobs to add an opportunity.")
    else:
        featured = jobs.sort_values("package_lpa", ascending=False).head(3)
        cols = st.columns(3)
        for col, (_, job) in zip(cols, featured.iterrows()):
            with col:
                st.markdown('<div class="job-card">', unsafe_allow_html=True)
                st.markdown(f"**{job['role']}**")
                st.write(f"🏢 {job['company']}")
                st.write(f"📍 {job['location']}")
                st.write(f"💰 {job['package_lpa']:.1f} LPA")
                st.caption(f"Minimum CGPA: {job['min_cgpa']:.1f}")
                st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("How it works")
    a, b, c = st.columns(3)
    a.write("**1. Create your profile**\n\nEnter your details when applying.")
    b.write("**2. Check eligibility**\n\nCompare your branch and CGPA with job criteria.")
    c.write("**3. Track applications**\n\nSee submitted applications and their status.")

if page == "Login":
    st.title("🎓 CampusConnect")
    st.subheader("Welcome! Please login or register.")

    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")

            if login_button:
                user = login_user(email, password)

                if user:
                    st.session_state.user = user
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

    with register_tab:
        with st.form("register_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            password = st.text_input("Create Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register_button = st.form_submit_button("Create Account")

            if register_button:
                if not name.strip():
                    st.error("Please enter your name.")
                elif not is_valid_email(email):
                    st.error("Please enter a valid email.")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                elif register_user(name, email, password):
                    st.success("Registration successful! Please login.")
                else:
                    st.error("This email is already registered.")

    st.stop()
# ---------- Student Dashboard ----------
elif page == "Student Dashboard":
    st.title("🎓 Student Dashboard")
    st.caption("Your personal placement activity at a glance.")

    email = st.session_state.user["email"]
    st.info(f"Logged in as: {email}")
    if email:
            mine = load_applications(email.strip())

            if mine.empty:
                st.info("No applications found for this email yet.")
            else:

                
                # Student Profile Card
                student = mine.iloc[0]

                with st.container(border=True):
                    st.subheader("👤 Student Profile")

                    p1, p2, p3 = st.columns(3)

                    with p1:
                        st.markdown("**Student Name**")
                        st.write(student["student_name"])

                    with p2:
                        st.markdown("**Branch**")
                        st.write(student["student_branch"])

                    with p3:
                        st.markdown("**CGPA**")
                        st.write(f"{student['student_cgpa']:.2f} / 10")

                    st.markdown("**Email Address**")
                    st.write(student["student_email"])

                st.divider()

                
                total = len(mine)
                shortlisted = int((mine["status"] == "Shortlisted").sum())
                selected = int((mine["status"] == "Selected").sum())
                pending = int((mine["status"].isin(["Applied", "Under Review"])).sum())

                st.subheader("Application Summary")

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Applications", total)
                c2.metric("Shortlisted", shortlisted)
                c3.metric("Selected", selected)
                c4.metric("Pending", pending)

                
                st.subheader("Application Progress Tracker")

                for _, app in mine.iterrows():
                    st.write(f"**{app['company']} — {app['role']}**")

                    stages = [
                        "Applied",
                        "Under Review",
                        "Shortlisted",
                        "Interview Scheduled",
                        "Selected"
                    ]

                    current_status = app["status"]

                    if current_status in stages:
                        current_index = stages.index(current_status)
                        st.progress((current_index + 1) / len(stages))
                        st.caption(f"Current stage: {current_status}")
                    elif current_status == "Rejected":
                        st.warning("Application status: Rejected")

                    st.divider()


                st.subheader("My Application Status")
                st.dataframe(
                    mine[["company", "role", "location", "package_lpa", "status", "applied_at"]].rename(columns={
                        "company": "Company",
                        "role": "Role",
                        "location": "Location",
                        "package_lpa": "Package (LPA)",
                        "status": "Status",
                        "applied_at": "Applied At"
                    }),
                    use_container_width=True,
                    hide_index=True,
                )

                st.caption("Application status is updated by the placement administrator.")

# ---------- Browse Jobs ----------
elif page == "Browse Jobs":
    st.title("Browse opportunities")
    st.caption("Filter roles and check eligibility before applying.")

    student_name = st.session_state.user["name"]
    student_email = st.session_state.user["email"]

    with st.expander("Your student profile", expanded=True):
        st.info(f"Logged in as: {student_name} ({student_email})")

        p1, p2 = st.columns(2)

        with p1:
            branch = st.selectbox(
                "Branch",
                ["CSE", "AIML", "IT", "Data Science", "ECE", "Other"],
                key="browse_branch"
            )

        with p2:
            cgpa = st.number_input(
                "Current CGPA (out of 10)",
                min_value=0.0,
                max_value=10.0,
                value=6.76,
                step=0.01,
                key="browse_cgpa"
            )

            job_type_filter = st.selectbox(
                "Job type",
                ["All", "Internship", "Full-time"],
                key="job_type_filter"
            )

            max_package = st.slider(
                "Minimum package (LPA)", 0.0, 20.0, 0.0, 0.5
            )

    filtered = jobs.copy()
    search_query = st.text_input(
        "Search by company, role or location",
        placeholder="e.g. Google, Python Developer, Chandigarh"
    )

    if search_query:
        search_query = search_query.strip().lower()

        filtered = filtered[
            filtered["company"].str.lower().str.contains(search_query, na=False) |
            filtered["role"].str.lower().str.contains(search_query, na=False) |
            filtered["location"].str.lower().str.contains(search_query, na=False)
        ]
    if job_type_filter != "All":
        filtered = filtered[filtered["job_type"] == job_type_filter]
    filtered = filtered[filtered["package_lpa"] >= max_package]

    if filtered.empty:
        st.warning("No opportunities match these filters. Try changing the filters.")
    else:
        for _, job in filtered.iterrows():
            eligible_branches = [b.strip() for b in str(job["eligible_branches"]).split(",")]
            is_branch_ok = branch in eligible_branches or "All" in eligible_branches
            is_cgpa_ok = cgpa >= float(job["min_cgpa"])
            eligible = is_branch_ok and is_cgpa_ok
            with st.container(border=True):
                    left, right = st.columns([3, 1])

                    with left:
                        st.subheader(f"{job['role']} · {job['company']}")
                        st.write(f"📍 {job['location']}  |  **{job['job_type']}**  |  **{job['package_lpa']:.1f} LPA**")

                        with st.expander("View Full Job Details"):
                            st.write("**Company:**", job["company"])
                            st.write("**Job Role:**", job["role"])
                            st.write("**Location:**", job["location"])
                            st.write("**Job Type:**", job["job_type"])
                            st.write("**Package:**", f"{job['package_lpa']:.1f} LPA")
                            st.write("**Minimum CGPA:**", f"{job['min_cgpa']:.1f}")
                            st.write("**Eligible Branches:**", job["eligible_branches"])
                            st.write("**Job Description:**")
                            st.write(job["description"])

                        st.caption(f"Eligible branches: {job['eligible_branches']} · Minimum CGPA: {job['min_cgpa']:.1f}")

                    with right:
                        if eligible:
                            st.success("Eligible based on listed criteria")
                        else:
                            st.warning("Criteria not met")

                        with get_connection() as conn:
                            existing_application = conn.execute(
                                """
                                SELECT status FROM applications
                                WHERE LOWER(TRIM(student_email)) = LOWER(TRIM(?))
                                AND job_id = ?
                                """,
                                (student_email.strip(), int(job["id"]))
                            ).fetchone()

                        if existing_application:
                            st.info(
                                f"Already applied · Status: {existing_application[0]}"
                            )
                        else:
                            apply_disabled = (
                                not eligible
                                or not student_name.strip()
                                or not is_valid_email(student_email)
                            )

                            if st.button(
                                "Apply now",
                                key=f"apply_{job['id']}",
                                disabled=apply_disabled,
                                use_container_width=True
                            ):
                                try:
                                    with get_connection() as conn:
                                        conn.execute(
                                            """
                                            INSERT INTO applications
                                            (student_name, student_email, student_branch,
                                             student_cgpa, job_id, status, applied_at)
                                            VALUES (?, ?, ?, ?, ?, 'Applied', ?)
                                            """,
                                            (
                                                student_name.strip(),
                                                student_email.strip(),
                                                branch,
                                                float(cgpa),
                                                int(job["id"]),
                                                datetime.now().strftime("%Y-%m-%d %H:%M")
                                            )
                                        )
                                        conn.commit()

                                    st.success(
                                        f"Application submitted for {job['role']} at {job['company']}!"
                                    )
                                    st.rerun()

                                except sqlite3.IntegrityError:
                                    st.info(
                                        "You have already applied to this job using this email address."
                                    )
# ---------- My Applications ----------
# ---------- My Applications ----------
elif page == "My Applications":
    st.title("My applications")

    email = st.session_state.user["email"]
    st.info(f"Showing applications for: {email}")

    mine = load_applications(email.strip())

    if mine.empty:
        st.info("No applications found for this email yet.")
    else:
        st.metric("Applications found", len(mine))
        st.dataframe(
            mine[["company", "role", "location", "package_lpa", "status", "applied_at"]].rename(columns={
                "company": "Company", "role": "Role", "location": "Location",
                "package_lpa": "Package (LPA)", "status": "Status", "applied_at": "Applied at"
            }),
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Statuses in this demo are managed from the Admin page.")

# ---------- Admin ----------
elif page == "Admin: Manage Jobs":
    if st.session_state.user is None or st.session_state.user["role"] != "admin":
        st.error("Access denied! Admin privileges required.")
        st.stop()

    st.title("Admin · Manage jobs")
    
    jobs = load_jobs()
    all_apps = load_applications()

    total_jobs = len(jobs)
    total_apps = len(all_apps)

    shortlisted = (
        int((all_apps["status"] == "Shortlisted").sum())
        if not all_apps.empty else 0
    )

    selected = (
        int((all_apps["status"] == "Selected").sum())
        if not all_apps.empty else 0
    )

    st.subheader("Placement Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Jobs", total_jobs)
    c2.metric("Total Applications", total_apps)
    c3.metric("Shortlisted", shortlisted)
    c4.metric("Selected", selected)

    
    success_rate = (selected / total_apps * 100) if total_apps > 0 else 0

    st.metric("Placement Success Rate", f"{success_rate:.1f}%")

    st.subheader("📊 Placement Analytics")

    if not all_apps.empty:
        chart1, chart2 = st.columns(2)

        with chart1:
            st.write("**Applications by Status**")
            status_data = all_apps["status"].value_counts()
            st.bar_chart(status_data)

        with chart2:
            st.write("**Applications by Company**")
            company_data = all_apps["company"].value_counts()
            st.bar_chart(company_data)
    else:
        st.info("Analytics will appear when students apply for jobs.")

        st.subheader("Manage Applications")

    if not all_apps.empty:
        st.dataframe(
            all_apps,
            use_container_width=True,
            hide_index=True
        )

        application_options = {
            f"#{row['id']} - {row['student_name']} - {row['company']} ({row['status']})": int(row['id'])
            for _, row in all_apps.iterrows()
        }

        selected_application_label = st.selectbox(
            "Select application",
            list(application_options.keys())
        )

        selected_application_id = application_options[selected_application_label]

        new_status = st.selectbox(
            "Update application status",
            ["Applied", "Under Review", "Shortlisted",
             "Interview Scheduled", "Rejected", "Selected"]
        )

        if st.button("Update Status"):
            with get_connection() as conn:
                conn.execute(
                    "UPDATE applications SET status = ? WHERE id = ?",
                    (new_status, selected_application_id)
                )
                conn.commit()

            st.success("Application status updated successfully!")
            st.rerun()
    else:
        st.info("No applications available.")


    st.subheader("Edit an existing job")

    jobs = load_jobs()

    if not jobs.empty:
        job_options = {
            f"{row['company']} - {row['role']} (ID: {row['id']})": int(row['id'])
            for _, row in jobs.iterrows()
        }

        selected_job_label = st.selectbox(
            "Select job to edit",
            list(job_options.keys())
        )

        selected_job_id = job_options[selected_job_label]
        selected_job = jobs[jobs["id"] == selected_job_id].iloc[0]

        with st.form("edit_job_form"):
            edit_company = st.text_input("Company", value=str(selected_job["company"]))
            edit_role = st.text_input("Role", value=str(selected_job["role"]))
            edit_location = st.text_input("Location", value=str(selected_job["location"]))
        
            edit_min_cgpa = st.number_input(
                "Minimum CGPA",
                min_value=0.0,
                max_value=10.0,
                value=float(selected_job["min_cgpa"]),
                step=0.1
            )
            edit_branches = st.text_input(
                "Eligible branches (comma separated)",
                value=str(selected_job["eligible_branches"])
            )
            edit_description = st.text_area(
                "Description",
                value=str(selected_job["description"])
            )

            update_job = st.form_submit_button("Save Changes")
            if update_job:
                with get_connection() as conn:
                    conn.execute("""
                        UPDATE jobs
                        SET company = ?, role = ?, location = ?,
                            min_cgpa = ?, eligible_branches = ?, description = ?
                        WHERE id = ?
                    """, (
                        edit_company, edit_role, edit_location,
                        edit_min_cgpa, edit_branches, edit_description,
                        selected_job_id
                    ))
                    conn.commit()

                st.success("Job updated successfully!")
                st.rerun()
    with st.expander("Add a job opportunity", expanded=True):
        with st.form("add_job_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                company = st.text_input("Company name")
                role = st.text_input("Job role")
                location = st.text_input("Location", value="Chandigarh")
                package = st.number_input("Package (LPA)", min_value=0.0, max_value=100.0, value=5.0, step=0.5)
            with c2:
                min_cgpa = st.number_input("Minimum CGPA", min_value=0.0, max_value=10.0, value=6.0, step=0.1)
                branches = st.text_input("Eligible branches (comma-separated)", value="CSE, AIML, IT")
                job_type = st.selectbox("Job type", ["Internship", "Full-time"])
                description = st.text_area("Job description")
            submitted = st.form_submit_button("Add opportunity", type="primary")
            if submitted:
                if not company.strip() or not role.strip() or not description.strip():
                    st.error("Please enter company, role, and job description.")
                else:
                    with get_connection() as conn:
                        conn.execute("""
                            INSERT INTO jobs
                            (company, role, location, package_lpa, min_cgpa, eligible_branches, job_type, description, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (company.strip(), role.strip(), location.strip(), float(package), float(min_cgpa), branches.strip(), job_type, description.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")))
                        conn.commit()
                    st.success("Job opportunity added.")
                    st.rerun()

    st.subheader("Current job listings")
    jobs = load_jobs()
    if not jobs.empty:
        st.dataframe(
            jobs[["id", "company", "role", "location", "package_lpa", "min_cgpa", "eligible_branches", "job_type"]],
            use_container_width=True,
            hide_index=True,
        )
        job_ids = jobs["id"].tolist()
        selected_job = st.selectbox("Select job to delete", job_ids, format_func=lambda x: f"#{x} · {jobs.loc[jobs['id'] == x, 'company'].iloc[0]} — {jobs.loc[jobs['id'] == x, 'role'].iloc[0]}")
    if st.button("Delete selected job", type="secondary"):
            st.session_state["confirm_delete_job"] = True

    if st.session_state.get("confirm_delete_job", False):
            st.warning("Are you sure you want to delete this job and its applications?")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Yes, Delete Job", type="primary"):
                    with get_connection() as conn:
                        conn.execute(
                            "DELETE FROM applications WHERE job_id = ?",
                            (int(selected_job),)
                        )
                        conn.execute(
                            "DELETE FROM jobs WHERE id = ?",
                            (int(selected_job),)
                        )
                        conn.commit()

                    st.session_state["confirm_delete_job"] = False
                    st.success("Job and its demo applications deleted.")
                    st.rerun()

            with col2:
                if st.button("Cancel"):
                    st.session_state["confirm_delete_job"] = False
                    st.rerun()

st.sidebar.divider()
st.sidebar.caption("Built with Python, Streamlit, Pandas & SQLite")
