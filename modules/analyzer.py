import pandas as pd
import numpy as np

PROFILE_COLUMNS = ['Name', 'RollNo', 'Branch', 'MobileNumber', 'Email']
# We allow Subject to be optional or required depending on the sheet
MARKS_COLUMNS = ['RollNo', 'Mid1', 'Mid2']

class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass

def standardize_dataframe_columns(df, required_columns):
    """
    Standardizes DataFrame column names by trimming and checking casing.
    Raises DataValidationError if required columns are missing.
    """
    columns_in_file = [str(col).strip() for col in df.columns]
    columns_map = {col.lower(): col for col in df.columns}
    
    missing_cols = []
    normalized_cols_map = {}
    
    for req_col in required_columns:
        req_col_lower = req_col.lower()
        if req_col_lower in columns_map:
            normalized_cols_map[req_col] = columns_map[req_col_lower]
        else:
            missing_cols.append(req_col)
            
    if missing_cols:
        raise DataValidationError(
            f"Missing required columns in uploaded sheet: {', '.join(missing_cols)}. "
            f"Please make sure your sheet contains: {', '.join(required_columns)}"
        )
        
    # Rename and keep standardized columns
    rename_dict = {normalized_cols_map[col]: col for col in required_columns}
    df = df.rename(columns=rename_dict)
    
    # Also standardize Subject column if present
    for col in df.columns:
        if str(col).strip().lower() == 'subject':
            df = df.rename(columns={col: 'Subject'})
            
    # Select only required columns (preserving others optionally)
    extra_cols = [c for c in df.columns if c not in required_columns]
    df = df[required_columns + extra_cols]
    return df

def validate_and_clean_profiles(file_path_or_buffer):
    """
    Validates uploaded student directory contacts sheet.
    Required columns: Name, RollNo, Branch, MobileNumber, Email.
    Subject is optional.
    """
    try:
        # Support Excel or CSV
        if hasattr(file_path_or_buffer, 'name') and file_path_or_buffer.name.endswith('.csv'):
            df = pd.read_csv(file_path_or_buffer)
        else:
            df = pd.read_excel(file_path_or_buffer)
    except Exception as e:
        raise DataValidationError(f"Could not read the uploaded student profile file. Details: {str(e)}")

    df = standardize_dataframe_columns(df, PROFILE_COLUMNS)
    
    # Clean text columns
    cols_to_clean = PROFILE_COLUMNS + (['Subject'] if 'Subject' in df.columns else [])
    for col in cols_to_clean:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({'nan': '', 'None': ''})
        
    return df

def validate_and_clean_marks(file_path_or_buffer):
    """
    Validates uploaded midterm assessment grades sheet.
    Required columns: RollNo, Mid1, Mid2.
    Subject is optional.
    """
    try:
        if hasattr(file_path_or_buffer, 'name') and file_path_or_buffer.name.endswith('.csv'):
            df = pd.read_csv(file_path_or_buffer)
        else:
            df = pd.read_excel(file_path_or_buffer)
    except Exception as e:
        raise DataValidationError(f"Could not read the uploaded midterm marks file. Details: {str(e)}")

    df = standardize_dataframe_columns(df, MARKS_COLUMNS)
    
    # Clean RollNo
    df['RollNo'] = df['RollNo'].astype(str).str.strip().str.upper()
    if 'Subject' in df.columns:
        df['Subject'] = df['Subject'].astype(str).str.strip()
        df['Subject'] = df['Subject'].replace({'nan': '', 'None': ''})
    
    # Coerce Mid marks to numeric, default missing to empty string (which gets mapped to 0 during database merging)
    df['Mid1'] = pd.to_numeric(df['Mid1'], errors='coerce')
    df['Mid2'] = pd.to_numeric(df['Mid2'], errors='coerce')
    
    had_missing = df['Mid1'].isna().any() or df['Mid2'].isna().any()
    
    # Fill empty numeric values with "" so that the merger knows they weren't supplied, or 0.0 if chosen
    df['Mid1'] = df['Mid1'].fillna("")
    df['Mid2'] = df['Mid2'].fillna("")
    
    return df, had_missing

def generate_db_statistics(df_db):
    """
    Calculates overall summary stats based on the complete loaded database.
    Supports records that may not have marks assigned yet.
    """
    total_students = len(df_db)
    if total_students == 0:
        return {}

    # Filter out students who don't have marks computed yet
    evaluated_df = df_db[df_db['Average'].notna() & (~df_db['Average'].astype(str).str.strip().isin(["", "nan", "None"]))]
    total_evaluated = len(evaluated_df)
    
    if total_evaluated == 0:
        return {
            'total_students': total_students,
            'total_evaluated': 0,
            'high_performance_count': 0,
            'medium_performance_count': 0,
            'low_performance_count': 0,
            'high_performance_pct': 0,
            'medium_performance_pct': 0,
            'low_performance_pct': 0,
            'mid1_slow_learners': 0,
            'mid2_slow_learners': 0,
            'slow_in_both_mids': 0,
            'avg_mid1': 0.0,
            'avg_mid2': 0.0,
            'avg_overall': 0.0
        }

    high_perf = len(evaluated_df[evaluated_df['Performance_Category'] == 'High Performance'])
    med_perf = len(evaluated_df[evaluated_df['Performance_Category'] == 'Medium Performance'])
    low_perf = len(evaluated_df[evaluated_df['Performance_Category'] == 'Low Performance'])

    mid1_slow = len(evaluated_df[evaluated_df['Mid1'] < 12.5])
    mid2_slow = len(evaluated_df[evaluated_df['Mid2'] < 12.5])
    
    slow_both = len(evaluated_df[(evaluated_df['Mid1'] < 12.5) & (evaluated_df['Mid2'] < 12.5)])

    avg_mid1 = round(pd.to_numeric(evaluated_df['Mid1']).mean(), 2)
    avg_mid2 = round(pd.to_numeric(evaluated_df['Mid2']).mean(), 2)
    avg_overall = round(pd.to_numeric(evaluated_df['Average']).mean(), 2)

    return {
        'total_students': total_students,
        'total_evaluated': total_evaluated,
        'high_performance_count': high_perf,
        'medium_performance_count': med_perf,
        'low_performance_count': low_perf,
        'high_performance_pct': round((high_perf / total_evaluated) * 100, 2),
        'medium_performance_pct': round((med_perf / total_evaluated) * 100, 2),
        'low_performance_pct': round((low_perf / total_evaluated) * 100, 2),
        'mid1_slow_learners': mid1_slow,
        'mid2_slow_learners': mid2_slow,
        'slow_in_both_mids': slow_both,
        'avg_mid1': avg_mid1,
        'avg_mid2': avg_mid2,
        'avg_overall': avg_overall
    }
