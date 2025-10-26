"""Utility functions for the application."""
import os
import pandas as pd
from werkzeug.utils import secure_filename


def allowed_file(filename, allowed_extensions):
    """Check if a file has an allowed extension.
    
    Args:
        filename: Name of the file
        allowed_extensions: Set of allowed extensions
        
    Returns:
        True if file extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def parse_csv_file(filepath):
    """Parse CSV file containing participant data.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        List of dictionaries with participant data
        
    Raises:
        ValueError: If CSV format is invalid
    """
    try:
        df = pd.read_csv(filepath)
        
        # Check for required columns (case-insensitive)
        columns_lower = [col.lower() for col in df.columns]
        
        if 'name' not in columns_lower or 'email' not in columns_lower:
            raise ValueError("CSV must contain 'name' and 'email' columns")
        
        # Normalize column names
        column_mapping = {}
        for col in df.columns:
            if col.lower() == 'name':
                column_mapping[col] = 'name'
            elif col.lower() == 'email':
                column_mapping[col] = 'email'
        
        df = df.rename(columns=column_mapping)
        
        # Remove rows with empty name or email
        df = df.dropna(subset=['name', 'email'])
        
        # Convert to list of dictionaries
        participants = df[['name', 'email']].to_dict('records')
        
        return participants
        
    except Exception as e:
        raise ValueError(f"Error parsing CSV file: {str(e)}")


def parse_excel_file(filepath):
    """Parse Excel file containing participant data.
    
    Args:
        filepath: Path to the Excel file
        
    Returns:
        List of dictionaries with participant data
        
    Raises:
        ValueError: If Excel format is invalid
    """
    try:
        df = pd.read_excel(filepath)
        
        # Check for required columns (case-insensitive)
        columns_lower = [col.lower() for col in df.columns]
        
        if 'name' not in columns_lower or 'email' not in columns_lower:
            raise ValueError("Excel must contain 'name' and 'email' columns")
        
        # Normalize column names
        column_mapping = {}
        for col in df.columns:
            if col.lower() == 'name':
                column_mapping[col] = 'name'
            elif col.lower() == 'email':
                column_mapping[col] = 'email'
        
        df = df.rename(columns=column_mapping)
        
        # Remove rows with empty name or email
        df = df.dropna(subset=['name', 'email'])
        
        # Convert to list of dictionaries
        participants = df[['name', 'email']].to_dict('records')
        
        return participants
        
    except Exception as e:
        raise ValueError(f"Error parsing Excel file: {str(e)}")


def save_uploaded_file(file, upload_folder):
    """Save an uploaded file securely.
    
    Args:
        file: FileStorage object from Flask
        upload_folder: Folder to save the file
        
    Returns:
        Path to the saved file
    """
    filename = secure_filename(file.filename)
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    return filepath
