
import sys
print(sys.executable)
print(sys.path)
import os
import io
import qrcode
from services import RequestService, UserService, STATUS_NEW
from database import init_db, get_connection

def test_backend_logic():
    print("Testing backend logic...")
    
    # Setup clean DB
    init_db("test_features.db")
    
    # Create user
    UserService.create_user("spec", "pass", "Specialist", 3)
    UserService.create_user("qm", "pass", "Quality Manager", 5)
    
    # Create request
    req_num = RequestService.create_request(
        ("Client", "123"), 
        ("SN123", "ModelX", "TypeY"), 
        "Problem"
    )
    print(f"Created request: {req_num}")
    
    conn = get_connection("test_features.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, help_needed, deadline_date FROM requests WHERE request_number = ?", (req_num,))
    req_id, help_needed, deadline = cursor.fetchone()
    conn.close()
    
    # 1. Test Toggle Help
    print(f"Initial help_needed: {help_needed}")
    RequestService.toggle_help_needed(req_id, True)
    
    conn = get_connection("test_features.db")
    cursor = conn.cursor()
    cursor.execute("SELECT help_needed FROM requests WHERE id = ?", (req_id,))
    new_help = cursor.fetchone()[0]
    conn.close()
    
    print(f"After toggle True: {new_help}")
    if new_help != 1:
        print("FAIL: Help needed not set to 1")
    else:
        print("PASS: Help needed set to 1")
        
    RequestService.toggle_help_needed(req_id, False)
    conn = get_connection("test_features.db")
    cursor = conn.cursor()
    cursor.execute("SELECT help_needed FROM requests WHERE id = ?", (req_id,))
    final_help = cursor.fetchone()[0]
    conn.close()
    
    print(f"After toggle False: {final_help}")
    if final_help != 0:
        print("FAIL: Help needed not set to 0")
    else:
        print("PASS: Help needed set to 0")

    # 2. Test Extend Deadline
    print(f"Initial deadline: {deadline}")
    RequestService.extend_deadline(req_id, 3)
    
    conn = get_connection("test_features.db")
    cursor = conn.cursor()
    cursor.execute("SELECT deadline_date FROM requests WHERE id = ?", (req_id,))
    new_deadline = cursor.fetchone()[0]
    conn.close()
    
    print(f"New deadline: {new_deadline}")
    if new_deadline <= deadline:
        print("FAIL: Deadline not extended")
    else:
        print("PASS: Deadline extended")

    # 3. Test QR Code Generation
    print("Testing QR Code generation...")
    try:
        data = "https://example.com"
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        print("PASS: QR Code generated successfully")
    except Exception as e:
        print(f"FAIL: QR Code generation failed: {e}")

    # Cleanup
    if os.path.exists("test_features.db"):
        os.remove("test_features.db")

if __name__ == "__main__":
    # Temporarily patch DB_NAME in database module if needed, but init_db takes arg
    # However, RequestService uses get_connection() which defaults to DB_NAME
    # So we need to patch DB_NAME or modify get_connection usage in services?
    # services.py imports get_connection from database.py.
    # We can patch database.DB_NAME
    import database
    database.DB_NAME = "test_features.db"
    
    test_backend_logic()
