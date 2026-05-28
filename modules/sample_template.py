import pandas as pd
import io

def generate_sample_profiles():
    """
    Generates a sample student contact details template.
    Required columns: Name, RollNo, Branch, MobileNumber, Email.
    """
    profiles = [
        {"Name": "Aarav Sharma", "RollNo": "22CS01", "Branch": "CSE", "MobileNumber": "9876543210", "Email": "aarav.sharma.dummy@gmail.com"},
        {"Name": "Ananya Reddy", "RollNo": "22CS02", "Branch": "CSE", "MobileNumber": "9876543211", "Email": "ananya.reddy.dummy@gmail.com"},
        {"Name": "Chaitanya Rao", "RollNo": "22EC01", "Branch": "ECE", "MobileNumber": "9876543212", "Email": "chaitanya.rao.dummy@gmail.com"},
        {"Name": "Diya Nair", "RollNo": "22IT01", "Branch": "IT", "MobileNumber": "9876543213", "Email": "diya.nair.dummy@gmail.com"},
        {"Name": "Gautam Verma", "RollNo": "22EE01", "Branch": "EEE", "MobileNumber": "9876543214", "Email": "gautam.verma.dummy@gmail.com"},
        {"Name": "Ishita Gupta", "RollNo": "22CS03", "Branch": "CSE", "MobileNumber": "9876543215", "Email": "ishita.gupta.dummy@gmail.com"},
        {"Name": "Kabir Das", "RollNo": "22EC02", "Branch": "ECE", "MobileNumber": "9876543216", "Email": "kabir.das.dummy@gmail.com"},
        {"Name": "Meera Joshi", "RollNo": "22IT02", "Branch": "IT", "MobileNumber": "9876543217", "Email": "meera.joshi.dummy@gmail.com"},
        {"Name": "Pranav Patel", "RollNo": "22EE02", "Branch": "EEE", "MobileNumber": "9876543218", "Email": "pranav.patel.dummy@gmail.com"},
        {"Name": "Rohan Deshmukh", "RollNo": "22CS04", "Branch": "CSE", "MobileNumber": "9876543219", "Email": "rohan.deshmukh.dummy@gmail.com"},
        {"Name": "Siddharth Sen", "RollNo": "22EC03", "Branch": "ECE", "MobileNumber": "9876543220", "Email": "siddharth.sen.dummy@gmail.com"}
    ]
    df = pd.DataFrame(profiles)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Students_Contacts")
    buffer.seek(0)
    return buffer

def generate_sample_marks():
    """
    Generates a sample student marks spreadsheet matching the Roll Numbers in the profiles.
    Required columns: RollNo, Mid1, Mid2.
    """
    marks = [
        {"RollNo": "22CS01", "Mid1": 22, "Mid2": 23},
        {"RollNo": "22CS02", "Mid1": 10, "Mid2": 11},  # Overall Slow (<12.5)
        {"RollNo": "22EC01", "Mid1": 18, "Mid2": 19},
        {"RollNo": "22IT01", "Mid1": 24, "Mid2": 21},
        {"RollNo": "22EE01", "Mid1": 8, "Mid2": 18},  # Mid1 Slow (<12.5), overall Medium
        {"RollNo": "22CS03", "Mid1": 21, "Mid2": 9},  # Mid2 Slow (<12.5), overall Medium
        {"RollNo": "22EC02", "Mid1": 7, "Mid2": 8},   # Overall Slow (<12.5)
        {"RollNo": "22IT02", "Mid1": 15, "Mid2": 16},
        {"RollNo": "22EE02", "Mid1": 20, "Mid2": 22},
        {"RollNo": "22CS04", "Mid1": "", "Mid2": 14}, # Missing Mid 1 (becomes 0, overall Slow < 12.5)
        {"RollNo": "22EC03", "Mid1": 13, "Mid2": ""}  # Missing Mid 2 (becomes 0, overall Slow < 12.5)
    ]
    df = pd.DataFrame(marks)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Students_Marks")
    buffer.seek(0)
    return buffer
