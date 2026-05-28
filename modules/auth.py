import json
import os
import hashlib
import streamlit as st

FACULTY_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'faculty_db.json')

# Default hardcoded registry as fallback if file doesn't exist
DEFAULT_REGISTRY = {
    "faculty": {
        "name": "Dr. Ramesh Kumar",
        "department": "Computer Science & Engineering",
        "role": "faculty",
        "pass_hash": "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f", # "password123"
        "password": "password123"
    },
    "admin": {
        "name": "System Administrator",
        "department": "Academic Registry Office",
        "role": "admin",
        "pass_hash": "6051fc84a7a0d74c225fb18a496b09952da5642e60723ecae543298edd7d82d6", # "admin2026"
        "password": "admin2026"
    }
}

from modules.firebase_manager import get_firestore_client, is_firebase_active

def load_faculty_registry():
    """
    Loads all faculty user credentials. Pulls from Firestore if active,
    otherwise falls back to local JSON.
    """
    if is_firebase_active():
        try:
            firestore_db = get_firestore_client()
            docs = firestore_db.collection("faculty").stream()
            registry = {}
            for doc in docs:
                registry[doc.id] = doc.to_dict()
            if registry:
                return registry
            else:
                # If empty, upload default registry to Firestore
                save_faculty_registry(DEFAULT_REGISTRY)
                return DEFAULT_REGISTRY
        except Exception as e:
            print(f"Firebase load faculty failed, falling back to JSON: {e}")
            import modules.firebase_manager as fbm
            fbm.disable_firebase() # Force dynamic fallback mode

    if not os.path.exists(FACULTY_DB_PATH):
        os.makedirs(os.path.dirname(FACULTY_DB_PATH), exist_ok=True)
        with open(FACULTY_DB_PATH, 'w') as f:
            json.dump(DEFAULT_REGISTRY, f, indent=4)
        return DEFAULT_REGISTRY
        
    try:
        with open(FACULTY_DB_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return DEFAULT_REGISTRY

def save_faculty_registry(registry):
    """
    Saves the faculty registry. Saves to Firestore if active, and JSON backup.
    """
    if is_firebase_active():
        try:
            firestore_db = get_firestore_client()
            batch = firestore_db.batch()
            for username, data in registry.items():
                doc_ref = firestore_db.collection("faculty").document(username)
                batch.set(doc_ref, data)
            batch.commit()
        except Exception as e:
            print(f"Firebase save faculty failed: {e}")
            import modules.firebase_manager as fbm
            fbm.disable_firebase()

    os.makedirs(os.path.dirname(FACULTY_DB_PATH), exist_ok=True)
    with open(FACULTY_DB_PATH, 'w') as f:
        json.dump(registry, f, indent=4)

def hash_password(password):
    """Generates standard SHA256 hash of a string password."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_new_faculty(username, name, department, password, created_by_admin="admin", role="faculty"):
    """
    Registers a new faculty or admin account.
    Returns (True, message) on success, or (False, error) on failure.
    """
    registry = load_faculty_registry()
    username = username.strip().lower()
    
    if not username or not name or not department or not password:
        return False, "All fields are required to create a faculty account."
        
    if username in registry:
        return False, f"Username '{username}' is already taken."
        
    registry[username] = {
        "name": name,
        "department": department,
        "role": role,
        "pass_hash": hash_password(password),
        "password": password,
        "CreatedByAdmin": created_by_admin
    }
    
    save_faculty_registry(registry)
    return True, f"Account profile for {name} ({role}) created successfully!"

def authenticate_faculty(username, password):
    """
    Verifies user credentials.
    Returns (authenticated_status, faculty_metadata_dict)
    """
    registry = load_faculty_registry()
    username = username.strip().lower()
    if username in registry:
        hashed_input = hash_password(password)
        if registry[username]["pass_hash"] == hashed_input:
            return True, registry[username]
    return False, None

def initialize_auth_state():
    """Initializes the session state variables for authentication."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'faculty_user' not in st.session_state:
        st.session_state.faculty_user = None

def login_form():
    """Renders a beautiful Faculty Portal Login screen."""
    initialize_auth_state()
    
    if st.session_state.authenticated:
        return True
        
    st.markdown(
        """
        <div style="text-align: center; margin-top: 30px; margin-bottom: 20px;">
            <h1 style="color: #1E3A8A; font-family: 'Segoe UI', sans-serif; font-weight: 800; font-size: 2.2rem; letter-spacing: -0.05em; margin-bottom: 5px;">
                🔑 Academic Portal Login
            </h1>
            <p style="color: #64748B; font-size: 0.95rem; font-family: 'Segoe UI', sans-serif;">
                Access the Student Performance Classification and Report Generation System.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Sleek login card using column padding
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form", clear_on_submit=False):
            st.markdown(
                """
                <div style="font-family: 'Segoe UI', sans-serif; margin-bottom: 10px;">
                    <label style="font-weight: 600; color: #475569; font-size: 0.85rem;">Portal Username</label>
                </div>
                """, 
                unsafe_allow_html=True
            )
            username = st.text_input("Username", label_visibility="collapsed", placeholder="e.g. faculty").strip()
            
            st.markdown(
                """
                <div style="font-family: 'Segoe UI', sans-serif; margin-top: 15px; margin-bottom: 10px;">
                    <label style="font-weight: 600; color: #475569; font-size: 0.85rem;">Portal Password</label>
                </div>
                """, 
                unsafe_allow_html=True
            )
            password = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter password")
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            submit = st.form_submit_button("Authenticate & Enter Dashboard", use_container_width=True)
            
            if submit:
                success, faculty_info = authenticate_faculty(username, password)
                if success:
                    st.session_state.authenticated = True
                    # Store username directly inside the user metadata dictionary
                    faculty_info['username'] = username
                    st.session_state.faculty_user = faculty_info
                    st.toast(f"Welcome back, {faculty_info['name']}!", icon="🔑")
                    st.rerun()
                else:
                    st.error("🔒 Invalid username or password. Please try again.")

        # Toggle section to allow ADMIN self-registration/sign up (faculty accounts are created by Admin inside)
        st.markdown("<hr style='border-top:1px dashed #CBD5E1; margin: 20px 0;'>", unsafe_allow_html=True)
        
        # We use a session state toggle for sign-up view
        if 'show_signup' not in st.session_state:
            st.session_state.show_signup = False
            
        if not st.session_state.show_signup:
            if st.button("➕ Create Admin Account (Sign Up)", use_container_width=True):
                st.session_state.show_signup = True
                st.rerun()
        else:
            st.markdown(
                """
                <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 15px; border-radius: 8px; font-family: 'Segoe UI', sans-serif;">
                    <h5 style="color: #0F172A; font-weight: 700; margin-top: 0;">🛠️ Admin Registration</h5>
                    <p style="color: #64748B; font-size: 0.8rem; margin-bottom: 12px;">Create a new administrator account. Note: Faculty accounts can only be created by an Administrator inside the dashboard portal.</p>
                </div>
                """, unsafe_allow_html=True
            )
            with st.form("admin_signup_form", clear_on_submit=True):
                s_user = st.text_input("New Admin Username", placeholder="e.g. principal_office").strip().lower()
                s_name = st.text_input("Admin Full Name", placeholder="e.g. Dr. Satish Chandra")
                s_dept = st.text_input("Academic Branch / Office", placeholder="e.g. Principal Registry Office")
                s_pass = st.text_input("Admin Password", type="password", placeholder="Choose password")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submit_signup = st.form_submit_button("💾 Register Admin", use_container_width=True)
                with col_btn2:
                    cancel_signup = st.form_submit_button("Cancel", use_container_width=True)
                    
                if submit_signup:
                    if not s_user or not s_name or not s_dept or not s_pass:
                        st.error("⚠️ All sign up fields are required.")
                    else:
                        success, message = register_new_faculty(s_user, s_name, s_dept, s_pass, created_by_admin="Self-Registered", role="admin")
                        if success:
                            st.success(f"🎉 Admin Account Created! {message}")
                            st.session_state.show_signup = False
                        else:
                            st.error(f"❌ Registration Failed: {message}")
                            
                if cancel_signup:
                    st.session_state.show_signup = False
                    st.rerun()
        
        # Info Box explaining credentials for project evaluations
        st.markdown(
            """
            <div style="background-color: #EFF6FF; border-left: 4px solid #3B82F6; padding: 15px; border-radius: 8px; font-family: 'Segoe UI', sans-serif; font-size: 0.85rem; color: #1E3A8A; margin-top: 20px; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);">
                <b>📌 Evaluation Credentials (College Project Demo):</b><br>
                • <b>Faculty login:</b> <code>faculty</code> & password: <code>password123</code><br>
                • <b>Admin login:</b> <code>admin</code> & password: <code>admin2026</code>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    return False
