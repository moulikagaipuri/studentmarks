import builtins
import sys

_original_print = builtins.print
def safe_print(*args, **kwargs):
    try:
        _original_print(*args, **kwargs)
    except OSError:
        pass
builtins.print = safe_print

import streamlit as st
import pandas as pd
import io
import os


# Set page configuration with a premium icon and wide layout
st.set_page_config(
    page_title="EduEvaluation - Student Classification Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import modular components
from modules.auth import initialize_auth_state, login_form
from modules.analyzer import validate_and_clean_profiles, validate_and_clean_marks, generate_db_statistics, DataValidationError
from modules.reporter import generate_styled_excel
from modules.visualizer import plot_performance_distribution, plot_mid_comparison_scatter, plot_branch_wise_averages, plot_slow_learner_metrics
from modules.emailer import send_student_email, send_faculty_report, verify_smtp_connection
from modules.sample_template import generate_sample_profiles, generate_sample_marks
import modules.db_manager as db

# Initialize session states
initialize_auth_state()

# Custom CSS for modern glassmorphism, responsive visual grids, and premium typography
def inject_custom_css():
    st.markdown(
        """
        <style>
        header[data-testid="stHeader"], div[data-testid="stDecoration"] {
            display: none !important;
            height: 0px !important;
        }
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* Premium custom metric cards styling */
        .metric-card {
            background-color: #FFFFFF;
            border-radius: 12px;
            padding: 1.35rem 1.15rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            border: 1px solid #F1F5F9;
            transition: all 0.25s ease-in-out;
            text-align: center;
        }
        .metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 12px -3px rgba(0, 0, 0, 0.06);
        }
        .metric-label {
            font-size: 0.75rem;
            color: #64748B;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .metric-value {
            font-size: 2.1rem;
            font-weight: 800;
            color: #0F172A;
            margin: 5px 0;
            line-height: 1;
        }
        .metric-footer {
            font-size: 0.72rem;
            font-weight: 600;
        }

        /* Sidebar details */
        section[data-testid="stSidebar"] {
            background-color: #0F172A !important;
            color: #F8FAFC !important;
        }
        section[data-testid="stSidebar"] hr {
            border-top: 1px solid #1E293B !important;
        }
        
        /* Portal Navigation Grid Cards */
        .portal-card {
            background-color: var(--background-color, #FFFFFF);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border-color, #E2E8F0);
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
            transition: all 0.25s ease-in-out;
            height: 100%;
        }
        .portal-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
            border-color: #3B82F6;
        }
        .portal-title {
            color: var(--text-color, #1E3A8A);
            font-size: 1.15rem;
            font-weight: 700;
            margin-top: 0;
            margin-bottom: 8px;
        }
        .portal-desc {
            color: var(--text-color, #64748B);
            opacity: 0.85;
            font-size: 0.85rem;
            line-height: 1.4;
            margin-bottom: 15px;
        }
        
        /* Specific overrides for dark mode compatibility */
        @media (prefers-color-scheme: dark) {
            .portal-title {
                color: #38BDF8 !important; /* Elegant light blue for dark mode */
            }
            .portal-desc {
                color: #E2E8F0 !important; /* Off-white for description text */
            }
            .portal-card {
                background-color: #1E293B !important; /* Dark card background */
                border-color: #334155 !important;
            }
        }
        
        /* Interactive grid borders */
        div[data-testid="stDataFrame"] {
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #E2E8F0;
        }
        
        /* Back Button custom look */
        .back-btn-custom {
            display: inline-block;
            margin-bottom: 20px !important;
        }
        
        /* Floating top-right Sign Out button container and custom button styling */
        .st-key-topsignout {
            position: fixed;
            top: 15px;
            right: 20px;
            z-index: 999999;
            width: auto !important;
        }
        .st-key-topsignout button {
            background-color: #EF4444 !important;
            color: #FFFFFF !important;
            border: 1px solid #DC2626 !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            padding: 0.45rem 1.1rem !important;
            font-size: 0.85rem !important;
            box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.3), 0 2px 4px -1px rgba(239, 68, 68, 0.15) !important;
            transition: all 0.2s ease-in-out !important;
        }
        .st-key-topsignout button:hover {
            background-color: #DC2626 !important;
            border-color: #B91C1C !important;
            box-shadow: 0 8px 15px -3px rgba(239, 68, 68, 0.4) !important;
            transform: translateY(-1px) !important;
        }
        .st-key-topsignout button:active {
            transform: translateY(1px) !important;
        }
        </style>

        """,
        unsafe_allow_html=True
    )

inject_custom_css()

# Initialize Navigation Page state
if 'page' not in st.session_state:
    st.session_state.page = "Home"

# Main Application Entry Control
if not st.session_state.authenticated:
    login_form()
else:
    # ------------------ AUTHENTICATED STATE ------------------
    faculty = st.session_state.faculty_user
    role = faculty.get('role', 'faculty')
    
    from modules.firebase_manager import is_firebase_active, get_firebase_error_msg
    fb_active = is_firebase_active()
    fb_badge = '<span style="display: inline-block; background-color: #F59E0B; color: black; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; padding: 2px 8px; border-radius: 4px; margin-top: 8px; margin-left: 5px;">🔥 Firebase Active</span>' if fb_active else '<span style="display: inline-block; background-color: #64748B; color: white; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; padding: 2px 8px; border-radius: 4px; margin-top: 8px; margin-left: 5px;">💾 Local JSON</span>'
    
    # 1. Sidebar Panel - signed in role
    st.sidebar.markdown(
        f"""
        <div style="background-color: #1E293B; padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 20px;">
            <p style="margin: 0; font-size: 0.7rem; color: #38BDF8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">Authorized Account</p>
            <h4 style="margin: 4px 0 2px 0; font-size: 1.05rem; color: #FFFFFF; font-weight: 700;">{faculty['name']}</h4>
            <p style="margin: 0; font-size: 0.75rem; color: #94A3B8;">{faculty['department']}</p>
            <div style="display: flex; flex-wrap: wrap;">
                <span style="display: inline-block; background-color: {'#4F46E5' if role == 'admin' else '#059669'}; color: white; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; padding: 2px 8px; border-radius: 4px; margin-top: 8px;">
                    🔑 {role}
                </span>
                {fb_badge}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not fb_active:
        st.sidebar.warning(f"⚠️ Firebase connection state:\n{get_firebase_error_msg()}")

    # Preload local SMTP configuration states
    if 'smtp_config' not in st.session_state:
        st.session_state.smtp_config = {
            'server': 'smtp.gmail.com',
            'port': 587,
            'email': '',
            'password': ''
        }



    # Sign Out Button
    st.sidebar.markdown("<br><hr>", unsafe_allow_html=True)
    if st.sidebar.button("🔒 Portal Sign Out", use_container_width=True, type="secondary"):
        st.session_state.authenticated = False
        st.session_state.faculty_user = None
        st.session_state.page = "Home"
        st.toast("Signed out successfully.")
        st.rerun()

    # Load database records & calculate stats
    student_records = db.load_student_db()
    faculty_username = faculty.get('username', 'faculty')
    
    # Identify the admin owner of the current session for strict data boundaries
    admin_owner = faculty_username if role == 'admin' else faculty.get('CreatedByAdmin', 'admin')
    from modules.auth import load_faculty_registry
    registry = load_faculty_registry()
    
    # Construct allowed creators set (admin itself + faculty accounts they registered)
    allowed_creators = {admin_owner}
    for u, details in registry.items():
        if details.get('CreatedByAdmin', 'admin') == admin_owner:
            allowed_creators.add(u)
            
    if role == 'faculty':
        student_records = [s for s in student_records if s.get('CreatedBy', 'admin') == faculty_username]
    elif role == 'admin':
        student_records = [s for s in student_records if s.get('CreatedBy', 'admin') in allowed_creators]
        
    df_db = pd.DataFrame(student_records)
    # Ensure marks and average columns are numeric to prevent PyArrow mixed-type failures
    for col in ['Mid1', 'Mid2', 'Average']:
        if col in df_db.columns:
            df_db[col] = pd.to_numeric(df_db[col], errors='coerce')
    stats = generate_db_statistics(df_db)

    # ------------------ TOP NAVIGATION AND LOGOUT BAR ------------------
    with st.container(key="topsignout"):
        if st.button("🔒 Sign Out", key="top_portal_sign_out", type="primary"):
            st.session_state.authenticated = False
            st.session_state.faculty_user = None
            st.session_state.page = "Home"
            st.toast("Signed out successfully.")
            st.rerun()

    # ----------------------------------------------------
    #                  DASHBOARD HOME VIEW
    # ----------------------------------------------------
    if st.session_state.page == "Home":
        if role == 'admin':
            # ------------------ ADMIN ROLE CENTRAL PORTAL ------------------
            st.markdown(
                """
                <div style="
                  background: linear-gradient(135deg, #0F172A 0%, #1E293B 60%, #334155 100%);
                  padding: 2.2rem;
                  border-radius: 16px;
                  color: white;
                  text-align: center;
                  box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.2);
                  margin-bottom: 2rem;
                  font-family: 'Segoe UI', sans-serif;
                ">
                  <h1 style="margin: 0; font-size: 2.2rem; font-weight: 800; letter-spacing: -0.05em; text-shadow: 0 2px 4px rgba(0,0,0,0.15);">
                     🛠️ ADMINISTRATIVE CENTRAL PORTAL
                  </h1>
                  <p style="margin: 8px 0 0 0; font-size: 1rem; opacity: 0.9; font-weight: 400;">
                    Manage academic faculty registries, oversee global student databases, and maintain system persistence.
                  </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Load registry stats
            from modules.auth import load_faculty_registry
            registry = load_faculty_registry()
            # Only count faculty members created by this admin
            admin_username = faculty.get('username', 'admin')
            my_faculty = {u: details for u, details in registry.items() if details.get('CreatedByAdmin', 'admin') == admin_username}
            total_faculty = len(my_faculty)
            total_depts = len(set(details.get('department', '') for details in my_faculty.values()))

            # Admin metrics cards
            col_a1, col_a2, col_a3 = st.columns(3)
            with col_a1:
                st.markdown(f'<div class="metric-card" style="border-left: 5px solid #3B82F6;"><div class="metric-label">Registered Faculty</div><div class="metric-value">{total_faculty}</div><div class="metric-footer" style="color:#3B82F6;">Active Class Instructors</div></div>', unsafe_allow_html=True)
            with col_a2:
                st.markdown(f'<div class="metric-card" style="border-left: 5px solid #10B981;"><div class="metric-label">Academic Departments</div><div class="metric-value">{total_depts}</div><div class="metric-footer" style="color:#10B981;">Course Disciplines</div></div>', unsafe_allow_html=True)
            with col_a3:
                st.markdown(f'<div class="metric-card" style="border-left: 5px solid #6366F1;"><div class="metric-label">Total Global Students</div><div class="metric-value">{stats.get("total_students", 0)}</div><div class="metric-footer" style="color:#6366F1;">System-Wide Directory</div></div>', unsafe_allow_html=True)

            st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
            st.caption("Select an administrative utility below to manage accounts or oversee global student data.")
            col_grid_1, col_grid_2, col_grid_3 = st.columns(3)

            with col_grid_1:
                st.markdown(
                    """
                    <div class="portal-card">
                        <h4 class="portal-title">👥 Faculty Registry</h4>
                        <p class="portal-desc">Manage existing coordinator credentials, and register new faculty login accounts dynamically.</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                if st.button("Manage Faculty Registry ➔", key="btn_go_fac_reg", use_container_width=True, type="primary"):
                    st.session_state.page = "Faculty Registry"
                    st.rerun()

            with col_grid_2:
                st.markdown(
                    """
                    <div class="portal-card">
                        <h4 class="portal-title">📂 Global Student Directory</h4>
                        <p class="portal-desc">View all student records across all faculty classes in a single, read-only system-wide table.</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                if st.button("Open Global Directory ➔", key="btn_go_global_dir", use_container_width=True, type="secondary"):
                    st.session_state.page = "Global Student Directory"
                    st.rerun()

            with col_grid_3:
                st.markdown(
                    """
                    <div class="portal-card" style="border-color:#FEE2E2;">
                        <h4 class="portal-title" style="color:#B91C1C;">🚨 Database Maintenance</h4>
                        <p class="portal-desc">Erase persistent JSON records and perform emergency registry hard-resets.</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                if st.button("Open System Reset Console ➔", key="btn_go_sys_reset", use_container_width=True, type="secondary"):
                    st.session_state.page = "System Reset Console"
                    st.rerun()

            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            col_grid_4, col_grid_5, col_grid_6 = st.columns(3)
            with col_grid_4:
                st.markdown(
                    """
                    <div class="portal-card">
                        <h4 class="portal-title">📚 Global Student Ledger</h4>
                        <p class="portal-desc">Inspect all student scores, classifications, and teaching faculty across all subjects system-wide.</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                if st.button("Open Global Student Ledger ➔", key="btn_go_global_ledger_admin", use_container_width=True, type="secondary"):
                    st.session_state.page = "Global Student Ledger"
                    st.rerun()
        else:
            # ------------------ FACULTY ROLE PORTAL ------------------
            st.markdown(
                """
                <div style="
                  background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 60%, #06B6D4 100%);
                  padding: 2.2rem;
                  border-radius: 16px;
                  color: white;
                  text-align: center;
                  box-shadow: 0 10px 15px -3px rgba(30, 58, 138, 0.2), 0 4px 6px -4px rgba(30, 58, 138, 0.2);
                  margin-bottom: 2rem;
                  font-family: 'Segoe UI', sans-serif;
                ">
                  <h1 style="margin: 0; font-size: 2.2rem; font-weight: 800; letter-spacing: -0.05em; text-shadow: 0 2px 4px rgba(0,0,0,0.15);">
                     🎓 STUDENT ACADEMIC CLASSIFICATION PORTAL
                  </h1>
                  <p style="margin: 8px 0 0 0; font-size: 1rem; opacity: 0.9; font-weight: 400;">
                    Manage persistent student directories, calculate 80/20 weighted mid-marks, and dispatch tailored email report checklists.
                  </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Metrics Dashboard Overview row
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.markdown(f'<div class="metric-card" style="border-left: 5px solid #6366F1;"><div class="metric-label">Registered Students</div><div class="metric-value">{stats.get("total_students", 0)}</div><div class="metric-footer" style="color:#6366F1;">Persistent Directory</div></div>', unsafe_allow_html=True)
            with col_m2:
                st.markdown(f'<div class="metric-card" style="border-left: 5px solid #10B981;"><div class="metric-label">Fast Learners (>20)</div><div class="metric-value">{stats.get("high_performance_count", 0)}</div><div class="metric-footer" style="color:#10B981;">🏆 {stats.get("high_performance_pct", 0.0)}% Class Ratio</div></div>', unsafe_allow_html=True)
            with col_m3:
                st.markdown(f'<div class="metric-card" style="border-left: 5px solid #F59E0B;"><div class="metric-label">Average Learners (12.5-20)</div><div class="metric-value">{stats.get("medium_performance_count", 0)}</div><div class="metric-footer" style="color:#F59E0B;">👍 {stats.get("medium_performance_pct", 0.0)}% Class Ratio</div></div>', unsafe_allow_html=True)
            with col_m4:
                st.markdown(f'<div class="metric-card" style="border-left: 5px solid #EF4444;"><div class="metric-label">Slow Learners (<12.5)</div><div class="metric-value">{stats.get("low_performance_count", 0)}</div><div class="metric-footer" style="color:#EF4444;">⚠️ {stats.get("low_performance_pct", 0.0)}% Class Ratio</div></div>', unsafe_allow_html=True)

            st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
            
            # Grid layout for navigation tiles
            st.markdown("### 🛠️ Portal Services Navigation Hub")
            st.caption("Select a workspace module below to inspect records, calculate grades, or dispatch notifications.")
            
            col_grid_1, col_grid_2, col_grid_3 = st.columns(3)
            
            with col_grid_1:
                st.markdown(
                    """
                    <div class="portal-card">
                        <h4 class="portal-title">👤 Student Directory</h4>
                        <p class="portal-desc">View existing profiles, and add or append new student profiles (Excel/CSV) matched by Roll Number.</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                if st.button("Open Directory Workspace ➔", key="btn_go_dir", use_container_width=True, type="secondary"):
                    st.session_state.page = "Student Directory"
                    st.rerun()
                    
            with col_grid_2:
                st.markdown(
                    """
                    <div class="portal-card">
                        <h4 class="portal-title">✍️ Marks & Calculations</h4>
                        <p class="portal-desc">Upload Mid-1/Mid-2 grades and automatically calculate 80% Best + 20% Least averages.</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                if st.button("Open Evaluation Workspace ➔", key="btn_go_marks", use_container_width=True, type="secondary"):
                    st.session_state.page = "Marks Calculation"
                    st.rerun()
                    
            with col_grid_3:
                st.markdown(
                    """
                    <div class="portal-card">
                        <h4 class="portal-title">📉 Analytics Insights</h4>
                        <p class="portal-desc">Inspect circular performance donut graphs, branch score summaries, and progress diagrams.</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                if st.button("Open Analytics Dashboard ➔", key="btn_go_charts", use_container_width=True, type="secondary"):
                    st.session_state.page = "Visual Analytics"
                    st.rerun()

            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            col_grid_4, col_grid_5, col_grid_6 = st.columns(3)
            
            with col_grid_4:
                st.markdown(
                    """
                    <div class="portal-card">
                        <h4 class="portal-title">📧 Dispatch Email Center</h4>
                        <p class="portal-desc">Select report marks scope, check custom checkbox lists, and email report cards to students.</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                if st.button("Open Dispatch Mailing Portal ➔", key="btn_go_email", use_container_width=True, type="secondary"):
                    st.session_state.page = "Email Dispatch"
                    st.rerun()
                    
            with col_grid_5:
                st.markdown(
                    """
                    <div class="portal-card">
                        <h4 class="portal-title">⚙️ SMTP Server Settings</h4>
                        <p class="portal-desc">Establish socket connections and verify SMTP credential authentication for safe emailing.</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                if st.button("Configure Mail Servers ➔", key="btn_go_smtp", use_container_width=True, type="secondary"):
                    st.session_state.page = "SMTP Settings"
                    st.rerun()
                    
            with col_grid_6:
                st.markdown(
                    """
                    <div class="portal-card">
                        <h4 class="portal-title">📚 Subject Manager</h4>
                        <p class="portal-desc">Add, view, or rename student subject courses dynamically mapped under your instructor credentials.</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                if st.button("Open Subject Manager ➔", key="btn_go_subj", use_container_width=True, type="secondary"):
                    st.session_state.page = "Subject Manager"
                    st.rerun()

            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            col_grid_7, col_grid_8, col_grid_9 = st.columns(3)
            with col_grid_7:
                st.markdown(
                    """
                    <div class="portal-card">
                        <h4 class="portal-title">📂 Global Student Ledger</h4>
                        <p class="portal-desc">Inspect all student scores, classifications, and teaching faculty across all subjects system-wide.</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                if st.button("Open Global Student Ledger ➔", key="btn_go_global_ledger", use_container_width=True, type="secondary"):
                    st.session_state.page = "Global Student Ledger"
                    st.rerun()

    # ----------------------------------------------------
    #           SUB-PAGE NAVIGATION STANDARD HEADER
    # ----------------------------------------------------
    else:
        # Floating top navigation bar with backing button
        col_nav_1, col_nav_2 = st.columns([1, 4])
        with col_nav_1:
            if st.button("⬅️ Back to Dashboard Home", use_container_width=True, type="secondary"):
                st.session_state.page = "Home"
                st.rerun()
        with col_nav_2:
            st.markdown(
                f"""
                <h2 style="margin-top:0; color:#1E3A8A; font-family:'Segoe UI', sans-serif; font-weight:800; letter-spacing:-0.03em;">
                    💼 Portal Workspace: {st.session_state.page}
                </h2>
                """,
                unsafe_allow_html=True
            )
        st.markdown("<hr style='border-top:2px solid #3B82F6; margin: 15px 0 25px 0;'>", unsafe_allow_html=True)

        # ------------------ SUB-PAGE: STUDENT DIRECTORY ------------------
        if st.session_state.page == "Student Directory":
            if 'student_success' in st.session_state and st.session_state.student_success:
                st.success(st.session_state.student_success)
                del st.session_state.student_success
            st.caption("View and manage contact profile information stored inside the persistent database.")
            
            if df_db.empty:
                st.info("ℹ️ No students are registered in the portal yet. Please upload a student contacts profiles sheet below to begin.")
            else:
                col_filt_1, col_filt_2, col_filt_3 = st.columns([1, 1, 2])
                with col_filt_1:
                    branches = ["All Branches"] + sorted(df_db['Branch'].unique().tolist())
                    selected_branch = st.selectbox("Filter Directory by Branch", options=branches, key="dir_branch_filt")
                with col_filt_2:
                    # Get subjects taught by this faculty
                    subjects = ["All Subjects"] + sorted(list(set(df_db['Subject'].unique().tolist()) if 'Subject' in df_db.columns else []))
                    selected_subj = st.selectbox("Filter Directory by Subject", options=subjects, key="dir_subj_filt")
                
                # Slice dataframe
                display_df = df_db.copy()
                if 'Subject' not in display_df.columns:
                    display_df['Subject'] = 'General'
                else:
                    display_df['Subject'] = display_df['Subject'].fillna('General').replace({"": "General"})
                
                if selected_branch != "All Branches":
                    display_df = display_df[display_df['Branch'] == selected_branch]
                if selected_subj != "All Subjects":
                    display_df = display_df[display_df['Subject'] == selected_subj]
                
                cols_to_show = ['RollNo', 'Name', 'Branch', 'MobileNumber', 'Email', 'Subject']
                # Safeguard all columns
                for col in cols_to_show:
                    if col not in display_df.columns:
                        display_df[col] = ""
                    else:
                        display_df[col] = display_df[col].fillna("")
                    
                st.dataframe(
                    display_df[cols_to_show], 
                    use_container_width=True,
                    hide_index=True
                )
                
            st.markdown("<br><hr style='border-top:1px solid #E2E8F0; margin: 15px 0;'>", unsafe_allow_html=True)
            
            # Profile Uploader Area
            col_up1, col_up2 = st.columns(2)
            
            with col_up1:
                st.markdown("##### ➕ Upload / Add Student Profiles (Sheet)")
                st.caption("Upload a spreadsheet (.xlsx/.xls/.csv) to register new students or update details. Optional column: 'Subject' (defaults to text field below).")
                
                default_subj_input = st.text_input("Default Subject for Uploaded Sheet (if Subject column missing)", value="General").strip()
                
                profile_file = st.file_uploader(
                    "Select contact profiles file (columns required: Name, RollNo, Branch, MobileNumber, Email, optional: Subject)",
                    type=["xlsx", "xls", "csv"],
                    key="profile_uploader"
                )
                
                if profile_file is not None:
                    with st.spinner("Parsing profile spreadsheet columns and saving records..."):
                        try:
                            df_profiles = validate_and_clean_profiles(profile_file)
                            # If 'Subject' not in uploaded sheet, add default
                            if 'Subject' not in df_profiles.columns:
                                df_profiles['Subject'] = default_subj_input
                            else:
                                df_profiles['Subject'] = df_profiles['Subject'].replace({"": default_subj_input, None: default_subj_input})
                                
                            updated_db_df, skipped_duplicates = db.add_or_update_students(df_profiles, faculty_username, default_subj_input)
                            if skipped_duplicates:
                                dup_list_str = "\n".join([f"- **{roll}** under subject *'{subj}'* (Registered by faculty: *{fac}*)" for roll, subj, fac in skipped_duplicates])
                                st.error(f"❌ **Duplicate Registration Skipped:**\n\nThe following student profile(s) were skipped as they are already registered for this subject by another faculty member:\n\n{dup_list_str}")
                                st.info("💡 Other non-duplicate profiles from the sheet were successfully processed and registered/updated.")
                            else:
                                st.session_state.student_success = f"🎉 Success! Processed and registered/updated {len(df_profiles)} student profiles."
                                st.toast(f"Uploaded {len(df_profiles)} profiles", icon="✅")
                                st.rerun()
                        except DataValidationError as ve:
                            st.error(f"❌ Columns Validation Failed: {str(ve)}")
                        except Exception as ex:
                            st.error(f"❌ Parsing Error: {str(ex)}")
                            
            with col_up2:
                st.markdown("##### ➕ Manually Add Student Profile")
                st.caption("Fill in individual student details below to manually register them into the database.")
                
                with st.form("manual_student_form", clear_on_submit=True):
                    m_roll = st.text_input("Roll Number", placeholder="e.g. 22CS05").strip().upper()
                    m_name = st.text_input("Student Name", placeholder="e.g. Rahul Verma").strip()
                    m_branch = st.text_input("Branch", placeholder="e.g. CSE").strip().upper()
                    m_mobile = st.text_input("Mobile Number", placeholder="e.g. 9876543221").strip()
                    m_email = st.text_input("Email Address", placeholder="e.g. rahul@example.com").strip()
                    m_subj = st.text_input("Subject Course", value="General").strip()
                    
                    submit_manual = st.form_submit_button("💾 Save Profile", use_container_width=True)
                    
                    if submit_manual:
                        if not m_roll or not m_name or not m_branch or not m_email or not m_subj:
                            st.error("⚠️ Roll Number, Name, Branch, Email, and Subject are required fields.")
                        else:
                            # Build single row dataframe to leverage existing helper logic
                            manual_df = pd.DataFrame([{
                                "RollNo": m_roll,
                                "Name": m_name,
                                "Branch": m_branch,
                                "MobileNumber": m_mobile,
                                "Email": m_email,
                                "Subject": m_subj
                            }])
                            _, skipped_duplicates = db.add_or_update_students(manual_df, faculty_username, m_subj)
                            if skipped_duplicates:
                                roll, subj, fac = skipped_duplicates[0]
                                st.error(f"❌ **Already Present:** Student **{roll}** is already registered for subject *'{subj}'* by faculty member *'{fac}'*!")
                            else:
                                st.session_state.student_success = f"🎉 Registered {m_name} ({m_roll}) under subject '{m_subj}' successfully!"
                                st.toast(f"Registered {m_name}", icon="✅")
                                st.rerun()


        # ------------------ SUB-PAGE: MARKS CALCULATION ------------------
        elif st.session_state.page == "Marks Calculation":
            st.markdown(
                """
                <div style="background-color:#EFF6FF; border-left: 4px solid #3B82F6; padding:15px; border-radius:8px; font-size:0.85rem; color:#1E3A8A; margin-bottom:20px;">
                    💡 <b>Academic Average Formula:</b> <code>Average = 80% * Best Midterm Score + 20% * Least Midterm Score</code>.<br>
                    Blanks or missing values are automatically defaulted to <code>0.00</code>.
                </div>
                """,
                unsafe_allow_html=True
            )
            
            if df_db.empty:
                st.warning("⚠️ No students registered. Please register profiles in the 'Student Directory' page before adding midterm marks.")
            else:
                # Filters
                col_mfilt_1, col_mfilt_2, col_mfilt_3 = st.columns([1, 1, 2])
                with col_mfilt_1:
                    m_branches = ["All Branches"] + sorted(df_db['Branch'].unique().tolist())
                    selected_m_branch = st.selectbox("Filter Branch", options=m_branches, key="marks_branch_filt")
                with col_mfilt_2:
                    m_subjects = ["All Subjects"] + sorted(df_db['Subject'].unique().tolist())
                    selected_m_subj = st.selectbox("Filter Subject", options=m_subjects, key="marks_subj_filt")
                with col_mfilt_3:
                    learner_filter = st.selectbox(
                        "Slow Learners View",
                        options=["All Students", "Mid-1 Slow (<12.5)", "Mid-2 Slow (<12.5)", "Average Slow (<12.5)"]
                    )
                    
                # Filter logic
                display_marks_df = df_db.copy()
                if selected_m_branch != "All Branches":
                    display_marks_df = display_marks_df[display_marks_df['Branch'] == selected_m_branch]
                if selected_m_subj != "All Subjects":
                    display_marks_df = display_marks_df[display_marks_df['Subject'] == selected_m_subj]
                    
                # Filter by slow learners
                if not display_marks_df.empty:
                    display_marks_df_graded = display_marks_df[display_marks_df['Average'].notna() & (~display_marks_df['Average'].astype(str).str.strip().isin(["", "nan", "None"]))]
                    
                    if learner_filter == "Mid-1 Slow (<12.5)":
                        display_marks_df = display_marks_df_graded[display_marks_df_graded['Mid1'] < 12.5]
                    elif learner_filter == "Mid-2 Slow (<12.5)":
                        display_marks_df = display_marks_df_graded[display_marks_df_graded['Mid2'] < 12.5]
                    elif learner_filter == "Average Slow (<12.5)":
                        display_marks_df = display_marks_df_graded[display_marks_df_graded['Average'] < 12.5]

                # Render Editable Table
                if display_marks_df.empty:
                    st.info("🔍 No student records matched your filters.")
                else:
                    st.markdown("##### 📝 Edit Student Midterm Marks Inline")
                    st.caption("You can directly edit the **Mid1** or **Mid2** cells in the table below. The average and classification category will instantly compute and save to disk.")
                    
                    # Create an editable view
                    edited_marks_df = st.data_editor(
                        display_marks_df[['RollNo', 'Name', 'Subject', 'Branch', 'Mid1', 'Mid2', 'Average', 'Performance_Category']],
                        column_config={
                            "RollNo": st.column_config.TextColumn("Roll No", disabled=True),
                            "Name": st.column_config.TextColumn("Student Name", disabled=True),
                            "Subject": st.column_config.TextColumn("Subject", disabled=True),
                            "Branch": st.column_config.TextColumn("Branch", disabled=True),
                            "Mid1": st.column_config.NumberColumn("Mid 1 Score", min_value=0.0, max_value=25.0, format="%.2f"),
                            "Mid2": st.column_config.NumberColumn("Mid 2 Score", min_value=0.0, max_value=25.0, format="%.2f"),
                            "Average": st.column_config.NumberColumn("Weighted Average (80/20)", disabled=True, format="%.2f"),
                            "Performance_Category": st.column_config.TextColumn("Category", disabled=True)
                        },
                        use_container_width=True,
                        hide_index=True,
                        key="marks_editor"
                    )
                    
                    # Check for updates and sync back to database using a (RollNo, Subject) map to avoid index mismatch
                    edited_map = {(r['RollNo'], r['Subject']): r for _, r in edited_marks_df.iterrows()}
                    has_changes = False
                    
                    # Load actual student record dictionary from DB once before checking
                    db_records = db.load_student_db()
                    
                    for _, orig_row in display_marks_df.iterrows():
                        roll_no = orig_row['RollNo']
                        subject = orig_row['Subject']
                        key = (roll_no, subject)
                        if key in edited_map:
                            edited_row = edited_map[key]
                            new_m1 = edited_row['Mid1']
                            new_m2 = edited_row['Mid2']
                            orig_m1 = orig_row['Mid1']
                            orig_m2 = orig_row['Mid2']

                            # Safe comparison helper
                            def get_clean_float(val):
                                if val == "" or val is None or pd.isna(val):
                                    return None
                                try:
                                    return float(val)
                                except ValueError:
                                    return None

                            m1_changed = get_clean_float(new_m1) != get_clean_float(orig_m1)
                            m2_changed = get_clean_float(new_m2) != get_clean_float(orig_m2)
                            
                            if m1_changed or m2_changed:
                                for s in db_records:
                                    if s['RollNo'] == roll_no and s.get('Subject', 'General') == subject and s.get('CreatedBy', 'admin') == faculty_username:
                                        s['Mid1'] = "" if new_m1 is None or pd.isna(new_m1) else float(new_m1)
                                        s['Mid2'] = "" if new_m2 is None or pd.isna(new_m2) else float(new_m2)
                                        db.recompute_average_and_category(s)
                                        has_changes = True
                                        break
                                        
                    if has_changes:
                        db.save_student_db(db_records)
                        st.toast("⚡ Student midterm scores and average weights recalculated & saved successfully!", icon="💾")
                        st.rerun()
                    
                    # Excel Exporter
                    styled_excel_buffer = generate_styled_excel(df_db)
                    st.download_button(
                        label="📥 Download Color-Coded Excel Performance Report",
                        data=styled_excel_buffer,
                        file_name="Student_Grading_Consolidated_Report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )


                st.markdown("<br><hr style='border-top:1px solid #E2E8F0; margin: 15px 0;'>", unsafe_allow_html=True)
                
                # Marks spreadsheet uploader
                st.markdown("##### ➕ Upload Midterm Assessment Marks")
                st.caption("Upload a midterm marks file (columns: RollNo, Mid1, Mid2, optional: Subject) to compute averages automatically.")
                
                default_marks_subj_input = st.text_input("Default Subject for Uploaded Marks (if Subject column missing)", value="General").strip()
                
                marks_file = st.file_uploader(
                    "Select marks sheet file (.xlsx/.xls/.csv)",
                    type=["xlsx", "xls", "csv"],
                    key="marks_uploader"
                )
                
                if marks_file is not None:
                    with st.spinner("Processing grading averages and compiling slow learners..."):
                        try:
                            df_marks_raw, had_missing = validate_and_clean_marks(marks_file)
                            if 'Subject' not in df_marks_raw.columns:
                                df_marks_raw['Subject'] = default_marks_subj_input
                            else:
                                df_marks_raw['Subject'] = df_marks_raw['Subject'].replace({"": default_marks_subj_input, None: default_marks_subj_input})
                                
                            updated_db, success_count, missing_rolls = db.upload_mid_marks_db(df_marks_raw, faculty_username, default_marks_subj_input)
                            
                            st.success(f"🎉 Successfully calculated averages for {success_count} students!")
                            if missing_rolls:
                                st.warning(
                                    f"⚠️ The following {len(missing_rolls)} Roll Numbers/Subjects from the marks sheet "
                                    f"were skipped as they are not registered in the directory: {', '.join(missing_rolls)}"
                                )
                            if had_missing:
                                st.info("💡 Some blank cells were detected and defaulted to 0.00 marks.")
                            
                            st.rerun()
                        except DataValidationError as ve:
                            st.error(f"❌ Marks Validation Failed: {str(ve)}")
                        except Exception as ex:
                            st.error(f"❌ Calculations Error: {str(ex)}")

        # ------------------ SUB-PAGE: VISUAL ANALYTICS ------------------
        elif st.session_state.page == "Visual Analytics":
            st.caption("Dynamic data dashboard visualizing performance segments, branch ratios, and progression trends.")
            
            graded_count = stats.get('total_evaluated', 0)
            if graded_count == 0:
                st.info("ℹ&nbsp; Analytics dashboard will unlock once student marks are uploaded and calculated.")
            else:
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    donut_fig = plot_performance_distribution(df_db)
                    st.pyplot(donut_fig, clear_figure=True)
                    
                    slow_fig = plot_slow_learner_metrics(df_db)
                    st.pyplot(slow_fig, clear_figure=True)
                    
                with col_a2:
                    scatter_fig = plot_mid_comparison_scatter(df_db)
                    st.pyplot(scatter_fig, clear_figure=True)
                    
                    branch_fig = plot_branch_wise_averages(df_db)
                    st.pyplot(branch_fig, clear_figure=True)

        # ------------------ SUB-PAGE: EMAIL DISPATCH ------------------
        elif st.session_state.page == "Email Dispatch":
            st.caption("Select dynamic email contents, customize exclusion checkmarks, and dispatch emails.")
            
            cfg = st.session_state.smtp_config
            if not cfg['email'] or not cfg['password']:
                st.warning(
                    "⚠️ SMTP Configurations are incomplete. Please complete your email credentials "
                    "under the 'SMTP Settings' page first to unlock mailing portals."
                )
            elif df_db.empty:
                st.warning("⚠️ Student database is empty. Register students under the 'Student Directory' page first.")
            else:
                st.success(f"🔌 SMTP Server active under sender: <b>{cfg['email']}</b>", icon="✅")
                
                # Setup configurations options
                col_e1, col_e2, col_e3 = st.columns(3)
                with col_e1:
                    email_mode = st.selectbox(
                        "Select Email Marks Scope",
                        options=["All Marks (Full Report Card)", "Mid 1 Marks Only", "Mid 2 Only", "Average Only"]
                    )
                with col_e2:
                    e_branch = st.selectbox("Select Branch to Email", options=["All Branches"] + sorted(df_db['Branch'].unique().tolist()))
                with col_e3:
                    e_slow_only = st.checkbox("Toggle: Filter Only Slow Learners (Avg < 12.5)")

                # Create base dataframe to mail
                mail_list_df = df_db.copy()
                if e_branch != "All Branches":
                    mail_list_df = mail_list_df[mail_list_df['Branch'] == e_branch]
                if e_slow_only:
                    mail_list_df = mail_list_df[mail_list_df['Performance_Category'] == 'Low Performance']

                if mail_list_df.empty:
                    st.info("🔍 No student records matched current filters.")
                else:
                    # Add checkmark boolean column in session state to handle persistencies
                    if 'email_selections' not in st.session_state:
                        st.session_state.email_selections = {}
                    
                    for _, row in df_db.iterrows():
                        key = f"{row['RollNo']}_{row.get('Subject', 'General')}"
                        if key not in st.session_state.email_selections:
                            is_graded = pd.notna(row['Average']) and str(row['Average']).strip() not in ["", "nan", "None"]
                            st.session_state.email_selections[key] = is_graded
                    
                    # Check for "Select All" or "De-select All" controls
                    col_ctrl_1, col_ctrl_2 = st.columns(2)
                    with col_ctrl_1:
                        if st.button("✅ Include/Select All Filtered Students", use_container_width=True):
                            for _, r in mail_list_df.iterrows():
                                st.session_state.email_selections[f"{r['RollNo']}_{r.get('Subject', 'General')}"] = True
                            st.rerun()
                    with col_ctrl_2:
                        if st.button("❌ Exclude/Cancel All Filtered Students", use_container_width=True):
                            for _, r in mail_list_df.iterrows():
                                st.session_state.email_selections[f"{r['RollNo']}_{r.get('Subject', 'General')}"] = False
                            st.rerun()

                    # Add a temporary checkbox column based on session state selections
                    mail_list_df['Send Email'] = mail_list_df.apply(
                        lambda r: st.session_state.email_selections.get(f"{r['RollNo']}_{r.get('Subject', 'General')}", True),
                        axis=1
                    )
                    
                    # Format visual dataframe
                    col_columns = ['Send Email', 'RollNo', 'Name', 'Subject', 'Branch', 'Mid1', 'Mid2', 'Average', 'Email']
                    
                    # RENDER DATA EDITOR FOR CHECKBOX SELECTION
                    st.markdown("##### 📝 Student Email Check-List Selection")
                    st.caption("Check or uncheck the 'Send Email' column to customize exactly who receives the report. Unchecked rows are cancelled.")
                    
                    edited_mail_df = st.data_editor(
                        mail_list_df[col_columns],
                        column_config={
                            "Send Email": st.column_config.CheckboxColumn("Send Email", default=True, help="Toggle to include or cancel sending"),
                            "RollNo": st.column_config.TextColumn("Roll No", disabled=True),
                            "Name": st.column_config.TextColumn("Student Name", disabled=True),
                            "Subject": st.column_config.TextColumn("Subject", disabled=True),
                            "Branch": st.column_config.TextColumn("Branch", disabled=True),
                            "Mid1": st.column_config.NumberColumn("Mid 1", disabled=True),
                            "Mid2": st.column_config.NumberColumn("Mid 2", disabled=True),
                            "Average": st.column_config.NumberColumn("Average", disabled=True),
                            "Email": st.column_config.TextColumn("Student Email", disabled=True)
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Sync edits back to session state selections
                    for _, r in edited_mail_df.iterrows():
                        st.session_state.email_selections[f"{r['RollNo']}_{r.get('Subject', 'General')}"] = bool(r['Send Email'])

                    # Filter target dispatch lists
                    dispatch_list = edited_mail_df[edited_mail_df['Send Email'] == True]
                    cancelled_count = len(edited_mail_df) - len(dispatch_list)
                    
                    # Metrics indicators
                    col_det_1, col_det_2 = st.columns(2)
                    with col_det_1:
                        st.info(f"📧 **Total Dispatch Queue size:** {len(dispatch_list)} student emails.")
                    with col_det_2:
                        st.warning(f"🚫 **Total Excluded / Cancelled:** {cancelled_count} student emails.")

                    # Big glowing trigger buttons
                    trigger_label = f"📤 Dispatch {len(dispatch_list)} Emails ({email_mode})"
                    if st.button(trigger_label, use_container_width=True, type="primary", disabled=(len(dispatch_list) == 0)):
                        success_count = 0
                        failed_count = 0
                        progress_bar = st.progress(0)
                        
                        for idx, (_, row) in enumerate(dispatch_list.iterrows()):
                            student_roll = row['RollNo']
                            student_subj = row.get('Subject', 'General')
                            # Match both RollNo and Subject to extract details
                            matching_rows = df_db[(df_db['RollNo'] == student_roll) & (df_db['Subject'] == student_subj)]
                            if not matching_rows.empty:
                                orig_row = matching_rows.iloc[0].to_dict()
                            else:
                                orig_row = df_db[df_db['RollNo'] == student_roll].iloc[0].to_dict()
                            
                            with st.spinner(f"Iterating Email ({idx+1}/{len(dispatch_list)}) to {orig_row['Name']}..."):
                                success, _ = send_student_email(cfg, orig_row, mode=email_mode)
                                if success:
                                    success_count += 1
                                else:
                                    failed_count += 1
                            progress_bar.progress((idx + 1) / len(dispatch_list))
                            
                        st.success(f"🎉 Dispatch completed! Sent {success_count} emails successfully. Failed: {failed_count}.")

        # ------------------ SUB-PAGE: SMTP SETTINGS ------------------
        elif st.session_state.page == "SMTP Settings":
            st.caption("Establish socket connections and verify SMTP credential authentication for safe emailing.")
            
            cfg = st.session_state.smtp_config
            with st.form("smtp_config_form"):
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    smtp_server = st.text_input("SMTP Server Host", value=cfg['server'], placeholder="smtp.gmail.com")
                    smtp_port = st.number_input("SMTP Port (TLS is standard)", value=cfg['port'], step=1)
                with col_s2:
                    sender_email = st.text_input("Sender Email Address", value=cfg['email'], placeholder="your_email@gmail.com")
                    sender_password = st.text_input("Sender App Password / Password", type="password", value=cfg['password'], placeholder="Google App Password (16-char)")
                
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                test_col, save_col = st.columns([1, 1])
                
                with save_col:
                    save_config = st.form_submit_button("💾 Save Configurations", use_container_width=True)
                with test_col:
                    test_config = st.form_submit_button("🔌 Test Connection Auth", use_container_width=True)
                
            # Perform configuration processing outside form scope
            if save_config:
                st.session_state.smtp_config = {
                    'server': smtp_server,
                    'port': int(smtp_port),
                    'email': sender_email,
                    'password': sender_password
                }
                st.success("✅ SMTP settings saved locally in active session!")
                st.rerun()
                
            if test_config:
                test_cfg = {
                    'server': smtp_server,
                    'port': int(smtp_port),
                    'email': sender_email,
                    'password': sender_password
                }
                with st.spinner("Initiating socket connection and testing auth credentials..."):
                    success, message = verify_smtp_connection(test_cfg)
                    if success:
                        st.success(f"🎉 Connection Successful! {message}")
                        st.session_state.smtp_config = test_cfg
                    else:
                        st.error(f"❌ Connection Failed: {message}")
                            
            st.markdown(
                """
                <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 20px; border-radius: 10px; font-size: 0.85rem; color: #475569; margin-top: 15px;">
                    <h5>💡 SMTP Configuration Guidelines:</h5>
                    <ol style="margin-left: 15px; margin-bottom: 0;">
                        <li><b>Gmail Users:</b> Google does not allow sending emails with your core password. You must enable <b>2-Step Verification</b> in your Google Account and generate a 16-character <b>App Password</b> to enter here.</li>
                        <li><b>Port 587</b> is standard for SMTP TLS connections.</li>
                        <li>Credentials are saved only in the current in-memory web session for privacy and safety. They are never logged or stored persistently.</li>
                    </ol>
                </div>
                """,
                unsafe_allow_html=True
            )

        # ------------------ SUB-PAGE: FACULTY REGISTRY ------------------
        elif st.session_state.page == "Faculty Registry" and role == 'admin':
            if 'registry_success' in st.session_state and st.session_state.registry_success:
                st.success(st.session_state.registry_success)
                del st.session_state.registry_success
            st.caption("Manage existing faculty credentials and register new instructors.")
            
            st.markdown("##### 👥 System Faculty Registry")
            st.caption("Active accounts loaded from the registry database:")
            
            # Load dynamic registry
            from modules.auth import load_faculty_registry, register_new_faculty
            registry = load_faculty_registry()
            
            # Render styled dynamic table of users
            table_rows = ""
            admin_username = faculty.get('username', 'admin')
            for username, details in registry.items():
                is_admin = details.get('role') == 'admin'
                badge_style = "background-color:#F0FDF4; color:#166534; font-weight:700;" if is_admin else "background-color:#E0F2FE; color:#0369A1; font-weight:700;"
                
                # Hierarchical filter: Admins can only see faculty they created
                created_by = details.get('CreatedByAdmin', 'admin')
                if created_by != admin_username:
                    continue
                    
                table_rows += f"""
                <tr style="border-bottom:1px solid #E2E8F0;">
                    <td style="padding:10px 15px;"><b>{details.get('name')}</b> (<code>{username}</code>)</td>
                    <td style="padding:10px 15px;">{details.get('department')}</td>
                    <td style="padding:10px 15px;"><code>{details.get('password', 'password123')}</code></td>
                    <td style="padding:10px 15px;"><span style="{badge_style} padding:2px 8px; border-radius:4px; font-size:0.75rem;">{details.get('role').upper()}</span></td>
                </tr>
                """
                
            st.markdown(
                f"""
                <table style="width:100%; border-collapse:collapse; font-size:0.85rem; text-align:left; border:1px solid #E2E8F0; border-radius:6px; overflow:hidden;">
                    <tr style="background-color:#F1F5F9; color:#475569; font-weight:bold;">
                        <th style="padding:10px 15px;">Faculty Member / Username</th>
                        <th style="padding:10px 15px;">Department</th>
                        <th style="padding:10px 15px;">Password</th>
                        <th style="padding:10px 15px;">Role Privilege</th>
                    </tr>
                    {table_rows}
                </table>
                """,
                unsafe_allow_html=True
            )
            
            # Form to register new faculty/admin accounts
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### ➕ Create New Account (Faculty / Admin)")
            st.caption("Register a new coordinator to grant them login access under your administrative boundary.")
            
            with st.form("admin_create_faculty_form", clear_on_submit=True):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    new_user = st.text_input("New Username", placeholder="e.g. ramakrishna").strip().lower()
                    new_name = st.text_input("Full Name", placeholder="e.g. Prof. Ramakrishna")
                with col_c2:
                    new_dept = st.text_input("Academic Department", placeholder="e.g. Electronics & Communication")
                    new_pass = st.text_input("Portal Password", type="password", placeholder="Choose password")
                    
                col_role1, col_role2 = st.columns(2)
                with col_role1:
                    new_role = st.selectbox("Role Privilege", options=["faculty"], disabled=True)
                    
                submit_c = st.form_submit_button("💾 Save User Credentials", use_container_width=True)
                
                if submit_c:
                    if not new_user or not new_name or not new_dept or not new_pass:
                        st.error("⚠️ All account registration fields are required.")
                    else:
                        success, message = register_new_faculty(new_user, new_name, new_dept, new_pass, created_by_admin=admin_username, role=new_role)
                        if success:
                            st.session_state.registry_success = f"🎉 Success! {message}"
                            st.toast(message, icon="✅")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed: {message}")

        # ------------------ SUB-PAGE: GLOBAL STUDENT DIRECTORY ------------------
        elif st.session_state.page == "Global Student Directory" and role == 'admin':
            st.caption("Read-only system-wide student records registry.")
            
            if df_db.empty:
                st.info("ℹ️ No students are registered in the system yet.")
            else:
                col_filt_1, col_filt_2 = st.columns([1, 3])
                with col_filt_1:
                    branches = ["All Branches"] + sorted(df_db['Branch'].unique().tolist())
                    selected_branch = st.selectbox("Filter Directory by Branch", options=branches, key="admin_branch_filt")
                
                # Slice dataframe
                display_df = df_db.copy()
                if selected_branch != "All Branches":
                    display_df = display_df[display_df['Branch'] == selected_branch]
                    
                st.dataframe(
                    display_df[['RollNo', 'Name', 'Branch', 'MobileNumber', 'Email', 'Average', 'Performance_Category', 'CreatedBy']], 
                    column_config={
                        "CreatedBy": st.column_config.TextColumn("Registered By (Faculty)")
                    },
                    use_container_width=True,
                    hide_index=True
                )

        # ------------------ SUB-PAGE: SYSTEM RESET CONSOLE ------------------
        elif st.session_state.page == "System Reset Console" and role == 'admin':
            st.caption("WARNING: The actions below directly modify persistent disk files. Deleted student records cannot be recovered.")
            
            col_admin_act1, col_admin_act2 = st.columns([2, 1])
            with col_admin_act1:
                st.write(
                    "Clicking the button on the right will erase the persistent JSON database (`data/student_db.json`) "
                    "completely. All student profiles, contact coordinates, and midterm marks will be reset to an empty state."
                )
            with col_admin_act2:
                if st.button("🚨 Reset Persistent Database", use_container_width=True, type="primary"):
                    # Selective reset for this admin organization to preserve other admins' data
                    all_records = db.load_student_db()
                    remaining_records = [s for s in all_records if s.get('CreatedBy', 'admin') not in allowed_creators]
                    
                    from modules.firebase_manager import is_firebase_active, get_firestore_client
                    if is_firebase_active():
                        try:
                            firestore_db = get_firestore_client()
                            batch = firestore_db.batch()
                            docs_to_del = [s for s in all_records if s.get('CreatedBy', 'admin') in allowed_creators]
                            for student in docs_to_del:
                                doc_id = f"{student['RollNo']}_{student.get('Subject', 'General')}_{student.get('CreatedBy', 'admin')}".replace('/', '_').replace('.', '_')
                                doc_ref = firestore_db.collection("students").document(doc_id)
                                batch.delete(doc_ref)
                            batch.commit()
                        except Exception as e:
                            print(f"Firebase selective clear failed: {e}")
                            
                    db.save_student_db(remaining_records)
                    st.toast("Organization database cleared", icon="✅")
                    st.session_state.student_success = "✅ Your organization's student database has been successfully cleared!"
                    st.session_state.page = "Home"
                    st.rerun()

        # ------------------ SUB-PAGE: SUBJECT MANAGER ------------------
        elif st.session_state.page == "Subject Manager" and role == 'faculty':
            if 'subject_success' in st.session_state and st.session_state.subject_success:
                st.success(st.session_state.subject_success)
                del st.session_state.subject_success
            st.caption("Manage, view, and rename subjects registered under your account.")
            
            # Load full database records specifically managed by this faculty member
            faculty_students = [s for s in db.load_student_db() if s.get('CreatedBy', 'admin') == faculty_username]
            subjects_taught = list(set(s.get('Subject', 'General') for s in faculty_students))
            
            if not subjects_taught:
                st.info("ℹ️ You have not registered any student records or subjects yet. Register students to create subjects.")
            else:
                st.markdown("##### 📚 Subjects Active under your Instructor Portal")
                for sub in sorted(subjects_taught):
                    st.markdown(f"• **{sub}** ({len([s for s in faculty_students if s.get('Subject') == sub])} Students)")
                    
                st.markdown("<br><hr>", unsafe_allow_html=True)
                st.markdown("##### ✏️ Rename Subject Course")
                st.caption("Renaming a subject course will cascade changes to update all registered student marks records matching it.")
                
                with st.form("rename_subject_form", clear_on_submit=True):
                    old_sub_sel = st.selectbox("Select Subject to Rename", options=sorted(subjects_taught))
                    new_sub_name = st.text_input("Enter New Subject Name", placeholder="e.g. Mathematics II").strip()
                    submit_rename = st.form_submit_button("📝 Rename Subject Course", use_container_width=True)
                    
                    if submit_rename:
                        if not new_sub_name:
                            st.error("⚠️ New Subject Name cannot be empty.")
                        elif new_sub_name == old_sub_sel:
                            st.error("⚠️ New subject name must be different from current name.")
                        else:
                            updated_count = db.rename_subject(faculty_username, old_sub_sel, new_sub_name)
                            st.session_state.subject_success = f"🎉 Successfully renamed '{old_sub_sel}' to '{new_sub_name}' across {updated_count} student records!"
                            st.toast("Subject renamed", icon="✅")
                            st.rerun()

        # ------------------ SUB-PAGE: GLOBAL STUDENT LEDGER ------------------
        elif st.session_state.page == "Global Student Ledger":
            st.caption("Unified system-wide student records ledger. Visible to all faculty members and administrators.")
            
            all_records = [s for s in db.load_student_db() if s.get('CreatedBy', 'admin') in allowed_creators]
            if not all_records:
                st.info("ℹ️ No student records are registered in the global ledger.")
            else:
                # Load faculty names map
                from modules.auth import load_faculty_registry
                fac_registry = load_faculty_registry()
                faculty_names_map = {username: details.get('name', username) for username, details in fac_registry.items()}
                
                # Convert to df
                df_global = pd.DataFrame(all_records)
                # Ensure numeric columns are consistently typed to prevent PyArrow serialization issues
                for col in ['Mid1', 'Mid2', 'Average']:
                    if col in df_global.columns:
                        df_global[col] = pd.to_numeric(df_global[col], errors='coerce')
                df_global['Faculty Name'] = df_global['CreatedBy'].map(faculty_names_map).fillna(df_global['CreatedBy'])
                
                # Filters
                col_lf1, col_lf2, col_lf3 = st.columns([1, 1, 2])
                with col_lf1:
                    l_branches = ["All Branches"] + sorted(df_global['Branch'].unique().tolist())
                    selected_l_branch = st.selectbox("Filter Branch", options=l_branches, key="ledger_branch_filt")
                with col_lf2:
                    l_subjects = ["All Subjects"] + sorted(df_global['Subject'].unique().tolist() if 'Subject' in df_global.columns else [])
                    selected_l_subj = st.selectbox("Filter Subject", options=l_subjects, key="ledger_subj_filt")
                with col_lf3:
                    search_query = st.text_input("🔎 Search Student Name or Roll Number", placeholder="Type name or roll number...").strip().upper()
                
                # Filter dataframe
                display_ledger_df = df_global.copy()
                if selected_l_branch != "All Branches":
                    display_ledger_df = display_ledger_df[display_ledger_df['Branch'] == selected_l_branch]
                if selected_l_subj != "All Subjects":
                    display_ledger_df = display_ledger_df[display_ledger_df['Subject'] == selected_l_subj]
                if search_query:
                    display_ledger_df = display_ledger_df[
                        display_ledger_df['Name'].str.upper().str.contains(search_query) | 
                        display_ledger_df['RollNo'].str.upper().str.contains(search_query)
                    ]
                
                # Columns order
                disp_cols = ['RollNo', 'Name', 'Subject', 'Branch', 'Mid1', 'Mid2', 'Average', 'Performance_Category', 'Faculty Name']
                # Make sure we only select columns that exist
                existing_disp_cols = [c for c in disp_cols if c in display_ledger_df.columns]
                
                st.dataframe(
                    display_ledger_df[existing_disp_cols],
                    column_config={
                        "RollNo": st.column_config.TextColumn("Roll No"),
                        "Mid1": st.column_config.NumberColumn("Mid 1", format="%.2f"),
                        "Mid2": st.column_config.NumberColumn("Mid 2", format="%.2f"),
                        "Average": st.column_config.NumberColumn("Weighted Average (80/20)", format="%.2f"),
                        "Performance_Category": st.column_config.TextColumn("Performance"),
                        "Faculty Name": st.column_config.TextColumn("Instructor")
                    },
                    use_container_width=True,
                    hide_index=True
                )
