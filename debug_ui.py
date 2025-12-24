import tkinter as tk
from interface import MainApp, setup_styles
from models import User

# Mock User
user = User(id=1, username="admin", full_name="Admin User", role_id=1, role_name="Administrator")

root = tk.Tk()
# Hide root window
root.withdraw()

# Setup styles (normally done in LoginWindow or MainApp init)
setup_styles()

app = MainApp(user)
# We don't need to run mainloop to trigger __init__ -> load_data
# load_data is called in __init__
# Just destroy it after a brief moment
app.update()
app.destroy()
