from interface import LoginWindow
from database import init_db
import os

if __name__ == "__main__":
    # Ensure DB exists
    if not os.path.exists("repair_system.db"):
        init_db()
        
    app = LoginWindow()
    app.mainloop()
