import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import json

# Path to the firebase service account credentials key
KEY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'firebase-key.json')

db = None
firebase_initialized = False
firebase_disabled = False
firebase_error_msg = None

def get_firebase_error_msg():
    global firebase_error_msg
    return firebase_error_msg

import streamlit as st

def sanitize_credentials(cred_dict):
    """Sanitizes credentials dict by converting literal escape strings '\\n' in private_key to real newlines."""
    if isinstance(cred_dict, dict) and "private_key" in cred_dict:
        if isinstance(cred_dict["private_key"], str):
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
    return cred_dict

def initialize_firebase():
    """Initializes Firebase Admin SDK using credentials from secrets, environment variables, or local file."""
    global db, firebase_initialized, firebase_disabled, firebase_error_msg
    if firebase_disabled:
        return False
    if firebase_initialized:
        return True
        
    cred = None
    
    # 1. Try loading from local credential key file first (best for local execution)
    if os.path.exists(KEY_PATH):
        try:
            # Local keys are already correctly formatted JSON files, but sanitize anyway for safety
            with open(KEY_PATH, 'r') as f:
                cred_dict = sanitize_credentials(json.load(f))
            cred = credentials.Certificate(cred_dict)
        except Exception as e:
            firebase_error_msg = f"Local file failed: {e}"
            print(f"Error loading Firebase local key file: {e}")

    # 2. Try loading from Streamlit secrets (Production Cloud)
    if not cred:
        try:
            if hasattr(st, "secrets"):
                if "firebase" in st.secrets:
                    cred_dict = sanitize_credentials(dict(st.secrets["firebase"]))
                    cred = credentials.Certificate(cred_dict)
                elif "FIREBASE_KEY" in st.secrets:
                    val = st.secrets["FIREBASE_KEY"]
                    try:
                        cred_dict = json.loads(val)
                    except Exception:
                        cred_dict = dict(val)
                    cred_dict = sanitize_credentials(cred_dict)
                    cred = credentials.Certificate(cred_dict)
                else:
                    # Scan all secret keys to see if any value is a dictionary or JSON string with "type": "service_account"
                    for key in st.secrets.keys():
                        try:
                            val = st.secrets[key]
                            if isinstance(val, str):
                                try:
                                    parsed = json.loads(val)
                                    if isinstance(parsed, dict) and parsed.get("type") == "service_account":
                                        parsed = sanitize_credentials(parsed)
                                        cred = credentials.Certificate(parsed)
                                        break
                                except Exception:
                                    pass
                            elif hasattr(val, "get") or isinstance(val, dict):
                                val_dict = sanitize_credentials(dict(val))
                                if val_dict.get("type") == "service_account":
                                    cred = credentials.Certificate(val_dict)
                                    break
                        except Exception:
                            pass
        except Exception as e:
            firebase_error_msg = f"Secrets load failed: {e}"
            print(f"Could not load Firebase from Streamlit secrets: {e}")
            
    # 3. Try loading from environment variable
    if not cred:
        try:
            env_key = os.environ.get("FIREBASE_KEY")
            if env_key:
                cred_dict = sanitize_credentials(json.loads(env_key))
                cred = credentials.Certificate(cred_dict)
        except Exception as e:
            firebase_error_msg = f"Environment load failed: {e}"
            print(f"Could not load Firebase from environment variable: {e}")

    if not cred and not firebase_error_msg:
        # Check if secrets.toml exists but has no keys
        if hasattr(st, "secrets") and len(st.secrets) > 0:
            firebase_error_msg = f"Secrets found but none contain 'type' = 'service_account'. Keys: {list(st.secrets.keys())}"
        else:
            firebase_error_msg = "No Firebase secrets or key file found. Operating in Local JSON mode."

    if cred:
        try:
            # Check if app is already initialized
            try:
                firebase_admin.get_app()
            except ValueError:
                firebase_admin.initialize_app(cred)
            db = firestore.client()
            firebase_initialized = True
            firebase_error_msg = None
            return True
        except Exception as e:
            firebase_error_msg = f"Firebase initialization failed: {e}"
            print(f"Error initializing Firebase SDK: {e}")
            return False
            
    return False

def disable_firebase():
    """Permanently disables Firebase operations for the rest of this execution session."""
    global db, firebase_initialized, firebase_disabled
    firebase_initialized = False
    firebase_disabled = True
    db = None

def get_firestore_client():
    """Returns Firestore client if initialized, otherwise None."""
    if initialize_firebase():
        return db
    return None

def is_firebase_active():
    """Returns True if Firebase is successfully configured and active."""
    return initialize_firebase()
