from services import RequestService
from database import get_connection

print("Checking requests via Service...")
try:
    # Mimic Admin user
    requests = RequestService.get_requests("Administrator", 1, None)
    print(f"Found {len(requests)} requests.")
    for r in requests:
        print(f"- {r.request_number} | {r.client_name} | {r.status_name}")
except Exception as e:
    print(f"Error getting requests: {e}")
