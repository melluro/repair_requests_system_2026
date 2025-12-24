from database import get_connection
from datetime import datetime

def calculate_statistics():
    """
    Calculates statistics for completed requests.
    Returns a dictionary with:
    - completed_count: Total number of completed requests
    - average_days: Average repair duration in days
    - problem_types: Dictionary mapping problem types (description) to count
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all completed requests
    cursor.execute("""
        SELECT creation_date, completion_date, problem_description
        FROM requests
        WHERE status_id = 5 AND completion_date IS NOT NULL
    """)
    rows = cursor.fetchall()
    conn.close()
    
    completed_count = len(rows)
    total_duration = 0
    problem_types = {}
    
    for created, completed, problem in rows:
        try:
            start_dt = datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(completed, "%Y-%m-%d %H:%M:%S")
            duration = (end_dt - start_dt).days
            # Ensure non-negative duration
            if duration < 0: 
                duration = 0
            total_duration += duration
        except ValueError:
            continue # Skip invalid dates
            
        # Group by problem type (simple string counting)
        # In a real system, we might normalize this or use a separate "FailureType" entity
        # For now, we use the description or maybe we should have added a type field.
        # The prompt mentions "Breakdown by failure types". 
        # "Equipment" has "type", maybe use that?
        # The existing code used problem_description. Let's use equipment type instead if possible?
        # "Breakdown by failure types" usually refers to *what went wrong*, which is in problem_description.
        # But problem_description is free text. Grouping by free text is messy.
        # However, following the previous logic and simplicity, I'll count exact matches of problem_description.
        # Better: Group by Equipment Type? No, "Failure Types".
        # Let's assume the user enters standard failure types or we just count unique descriptions.
        if problem in problem_types:
            problem_types[problem] += 1
        else:
            problem_types[problem] = 1
            
    average_days = (total_duration / completed_count) if completed_count > 0 else 0
    
    return {
        "completed_count": completed_count,
        "average_days": round(average_days, 2),
        "problem_types": problem_types
    }
