import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

# Base HTML wrapper for emails
EMAIL_HTML_WRAPPER = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #334155;
            background-color: #F8FAFC;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 30px auto;
            background: #FFFFFF;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border: 1px solid #E2E8F0;
        }}
        .header {{
            background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
            padding: 30px 20px;
            text-align: center;
            color: #FFFFFF;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: -0.025em;
        }}
        .content {{
            padding: 30px 25px;
        }}
        .greeting {{
            font-size: 18px;
            font-weight: 600;
            margin-top: 0;
            color: #1E293B;
        }}
        .intro {{
            font-size: 15px;
            line-height: 1.6;
            margin-bottom: 25px;
            color: #475569;
        }}
        .report-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: #F8FAFC;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #E2E8F0;
        }}
        .report-table th, .report-table td {{
            padding: 14px 18px;
            text-align: left;
            border-bottom: 1px solid #E2E8F0;
        }}
        .report-table th {{
            background-color: #F1F5F9;
            color: #475569;
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .report-table td {{
            font-size: 14px;
            color: #1E293B;
        }}
        .badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .badge-high {{
            background-color: #DCFCE7;
            color: #15803D;
        }}
        .badge-medium {{
            background-color: #FEF9C3;
            color: #A16207;
        }}
        .badge-low {{
            background-color: #FEE2E2;
            color: #B91C1C;
        }}
        .remarks-box {{
            padding: 16px 20px;
            border-radius: 8px;
            font-size: 14px;
            line-height: 1.5;
            margin-top: 25px;
            font-style: italic;
        }}
        .remarks-high {{
            background-color: #ECFDF5;
            border-left: 4px solid #10B981;
            color: #065F46;
        }}
        .remarks-medium {{
            background-color: #FFFBEB;
            border-left: 4px solid #F59E0B;
            color: #92400E;
        }}
        .remarks-low {{
            background-color: #FEF2F2;
            border-left: 4px solid #EF4444;
            color: #991B1B;
        }}
        .footer {{
            background-color: #F8FAFC;
            padding: 20px;
            text-align: center;
            border-top: 1px solid #E2E8F0;
            font-size: 12px;
            color: #94A3B8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Academic Performance Statement</h1>
        </div>
        <div class="content">
            <p class="greeting">Dear {name},</p>
            <p class="intro">Your mid-term examination performance details for Roll Number: <b>{roll_no}</b> (Branch: <b>{branch}</b>) have been processed. Below are your grades:</p>
            
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Assessment Heading</th>
                        <th>Marks Obtained / Details</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            
            {remarks_section}
        </div>
        <div class="footer">
            This is an automated system-generated academic notification. Please do not reply directly to this email.<br>
            <b>Department of Academics & Student Welfare</b>
        </div>
    </div>
</body>
</html>
"""

FACULTY_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #334155;
            background-color: #F8FAFC;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 650px;
            margin: 30px auto;
            background: #FFFFFF;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border: 1px solid #E2E8F0;
        }}
        .header {{
            background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
            padding: 30px 20px;
            text-align: center;
            color: #FFFFFF;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 700;
        }}
        .content {{
            padding: 30px 25px;
        }}
        .greeting {{
            font-size: 18px;
            font-weight: 600;
            margin-top: 0;
            color: #1E293B;
        }}
        .summary-box {{
            background-color: #F1F5F9;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 25px;
            border: 1px solid #E2E8F0;
        }}
        .summary-title {{
            font-weight: bold;
            font-size: 15px;
            margin-bottom: 12px;
            color: #1E293B;
        }}
        .footer {{
            background-color: #F8FAFC;
            padding: 20px;
            text-align: center;
            border-top: 1px solid #E2E8F0;
            font-size: 12px;
            color: #94A3B8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Academic Performance Consolidated Report</h1>
        </div>
        <div class="content">
            <p class="greeting">Dear Professor/Faculty Coordinator,</p>
            <p>We have successfully processed the student academic reports for the current batch. The analyzed records are attached to this email in a styled Excel format.</p>
            
            <div class="summary-box">
                <div class="summary-title">Performance Snapshot Summary</div>
                <div style="font-size: 14px; margin-bottom: 15px;">
                    Total Students Registered: <b>{total_students}</b><br>
                    Total Graded / Evaluated: <b>{total_evaluated}</b><br>
                    Overall Class Average: <b>{avg_marks}/20</b>
                </div>
                <hr style="border: 0; border-top: 1px solid #CBD5E1; margin: 15px 0;">
                <table style="width: 100%; text-align: center; font-size: 13px;">
                    <tr>
                        <td style="color: #10B981; font-weight: bold;">High: {high_count} ({high_pct}%)</td>
                        <td style="color: #F59E0B; font-weight: bold;">Medium: {med_count} ({med_pct}%)</td>
                        <td style="color: #EF4444; font-weight: bold;">Low: {low_count} ({low_pct}%)</td>
                    </tr>
                </table>
            </div>
            
            <div style="background-color: #FEF2F2; border-left: 4px solid #EF4444; padding: 15px; border-radius: 6px; font-size: 14px; color: #991B1B;">
                <b>Remedial Alert:</b> There are <b>{low_count}</b> Slow Learners (80/20 Average Marks < 12.5) who require structured academic guidance. Additionally, <b>{mid1_slow}</b> students had low scores in Mid-1, and <b>{mid2_slow}</b> students had low scores in Mid-2.
            </div>
        </div>
        <div class="footer">
            Student Performance Evaluation & Automated Notification Portal
        </div>
    </div>
</body>
</html>
"""

def get_remarks_and_badge(category):
    """
    Returns specific dynamic remarks and badge design configurations for student emails
    """
    if category == 'High Performance':
        return (
            "high",
            "Outstanding performance! Keep up the brilliant academic consistency and continue aiming high in your future endeavors. Your diligence is highly appreciated!"
        )
    elif category == 'Medium Performance':
        return (
            "medium",
            "Good effort! Your foundation is strong, but there is clear room for improvement. With more focused practice and target learning, you can easily transition to High Performance!"
        )
    else: # Low Performance or Unassigned
        return (
            "low",
            "We noticed that you are struggling with some concepts. Please do not worry. This is an invitation to work closely with your faculty mentors, attend remedial doubts sessions, and improve your scores in upcoming evaluations. We are here to support your success!"
        )

def send_student_email(smtp_config, student_row, mode="All Marks"):
    """
    Sends an individual beautifully-styled report card email to a single student.
    Supports mode customization: "Mid 1 Only", "Mid 2 Only", "Average Only", "All Marks".
    """
    smtp_server = smtp_config.get('server', 'smtp.gmail.com')
    smtp_port = int(smtp_config.get('port', 587))
    sender_email = smtp_config.get('email')
    sender_password = smtp_config.get('password')
    
    if not sender_email or not sender_password:
        raise ValueError("SMTP Credentials are not configured. Please enter them in settings.")

    # Extract student details
    name = student_row.get('Name', 'Student')
    roll_no = student_row.get('RollNo', 'N/A')
    branch = student_row.get('Branch', 'N/A')
    to_email = student_row.get('Email')
    mid1 = student_row.get('Mid1', 0.0)
    mid2 = student_row.get('Mid2', 0.0)
    average = student_row.get('Average', 0.0)
    category = student_row.get('Performance_Category', 'Low Performance')

    if not to_email or '@' not in str(to_email):
        return False, f"Invalid Email address: '{to_email}' for {name}"

    # Build dynamic rows based on sending mode
    table_rows = ""
    badge_type, remarks = get_remarks_and_badge(category)
    remarks_section = ""
    
    # Custom format strings
    m1_str = f"{float(mid1):.2f}" if mid1 != "" and mid1 is not None else "Not Graded"
    m2_str = f"{float(mid2):.2f}" if mid2 != "" and mid2 is not None else "Not Graded"
    avg_str = f"{float(average):.2f}" if average != "" and average is not None else "Not Graded"

    if mode == "Mid 1 Only":
        table_rows += f"<tr><td><b>Midterm 1 Score</b></td><td>{m1_str}</td></tr>"
    elif mode == "Mid 2 Only":
        table_rows += f"<tr><td><b>Midterm 2 Score</b></td><td>{m2_str}</td></tr>"
    elif mode == "Average Only":
        table_rows += f"<tr><td><b>80/20 Weighted Average Score</b></td><td>{avg_str}</td></tr>"
        if average != "":
            table_rows += f"<tr><td><b>Performance Category</b></td><td><span class='badge badge-{badge_type}'>{category}</span></td></tr>"
            remarks_section = f'<div class="remarks-box remarks-{badge_type}"><b>Remarks:</b> {remarks}</div>'
    else: # All Marks
        table_rows += f"<tr><td><b>Midterm 1 Score</b></td><td>{m1_str}</td></tr>"
        table_rows += f"<tr><td><b>Midterm 2 Score</b></td><td>{m2_str}</td></tr>"
        table_rows += f"<tr style='border-top: 2px solid #E2E8F0; background-color: #F1F5F9;'><td><b>80/20 Weighted Average</b></td><td><b>{avg_str}</b></td></tr>"
        if average != "":
            table_rows += f"<tr><td><b>Performance Category</b></td><td><span class='badge badge-{badge_type}'>{category}</span></td></tr>"
            remarks_section = f'<div class="remarks-box remarks-{badge_type}"><b>Remarks:</b> {remarks}</div>'

    # Compile dynamic HTML
    html_content = EMAIL_HTML_WRAPPER.format(
        name=name,
        roll_no=roll_no,
        branch=branch,
        table_rows=table_rows,
        remarks_section=remarks_section
    )

    # Build Email Message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Academic Performance Statement - {name} ({roll_no})"
    msg['From'] = sender_email
    msg['To'] = to_email
    msg.attach(MIMEText(html_content, 'html'))

    try:
        # Check for Demo / Mock mode
        if sender_email.strip().lower().endswith('@example.com') or sender_password.strip() == 'demo':
            return True, "Email successfully simulated (Demo Mode)."
            
        # Establish connection
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        return True, "Email successfully dispatched."
    except Exception as e:
        return False, f"Failed to send email. Details: {str(e)}"

def send_faculty_report(smtp_config, faculty_email, stats, excel_buffer):
    """
    Sends a consolidated email summary report directly to a faculty member's inbox,
    attaching the styled Excel sheet as a file artifact.
    """
    smtp_server = smtp_config.get('server', 'smtp.gmail.com')
    smtp_port = int(smtp_config.get('port', 587))
    sender_email = smtp_config.get('email')
    sender_password = smtp_config.get('password')
    
    if not sender_email or not sender_password:
        raise ValueError("SMTP Credentials are not configured. Please enter them in settings.")
        
    if sender_email.strip().lower().endswith('@example.com') or sender_password.strip() == 'demo':
        return True, "Consolidated faculty email successfully simulated (Demo Mode)."

    # Compile HTML Template
    html_content = FACULTY_EMAIL_TEMPLATE.format(
        total_students=stats.get('total_students', 0),
        total_evaluated=stats.get('total_evaluated', 0),
        avg_marks=f"{stats.get('avg_overall', 0.0):.2f}",
        high_count=stats.get('high_performance_count', 0),
        high_pct=stats.get('high_performance_pct', 0.0),
        med_count=stats.get('medium_performance_count', 0),
        med_pct=stats.get('medium_performance_pct', 0.0),
        low_count=stats.get('low_performance_count', 0),
        low_pct=stats.get('low_performance_pct', 0.0),
        mid1_slow=stats.get('mid1_slow_learners', 0),
        mid2_slow=stats.get('mid2_slow_learners', 0)
    )

    # Build Multipart Email
    msg = MIMEMultipart()
    msg['Subject'] = f"Consolidated Student Performance Analysis & Remedial Alert Report"
    msg['From'] = sender_email
    msg['To'] = faculty_email
    
    # Attach HTML body
    msg.attach(MIMEText(html_content, 'html'))
    
    # Attach Excel file
    excel_attachment = MIMEBase('application', 'octet-stream')
    excel_attachment.set_payload(excel_buffer.getvalue())
    encoders.encode_base64(excel_attachment)
    excel_attachment.add_header('Content-Disposition', 'attachment', filename="Student_Performance_Consolidated_Report.xlsx")
    msg.attach(excel_attachment)

    try:
        # Establish connection
        with smtplib.SMTP(smtp_server, smtp_port, timeout=12) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, faculty_email, msg.as_string())
        return True, "Faculty consolidated summary email sent successfully with report attachment."
    except Exception as e:
        return False, f"Failed to dispatch faculty report. Details: {str(e)}"

def verify_smtp_connection(smtp_config):
    """
    Tests whether the entered SMTP configurations can connect and authenticate successfully.
    """
    smtp_server = smtp_config.get('server', 'smtp.gmail.com')
    smtp_port = int(smtp_config.get('port', 587))
    sender_email = smtp_config.get('email')
    sender_password = smtp_config.get('password')
    
    if not sender_email or not sender_password:
        return False, "SMTP configuration details must be completed."
        
    if sender_email.strip().lower().endswith('@example.com') or sender_password.strip() == 'demo':
        return True, "Demo SMTP active. Mail dispatches will run in a safe simulated offline mode!"
        
    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=8) as server:
            server.starttls()
            server.login(sender_email, sender_password)
        return True, "SMTP connection successfully authenticated. Ready to send emails!"
    except Exception as e:
        return False, f"SMTP testing failed: {str(e)}"
