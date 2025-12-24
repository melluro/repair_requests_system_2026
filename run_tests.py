import unittest
import os
import sqlite3
import database
from database import init_db, get_connection
from services import UserService, RequestService, PartService, STATUS_NEW, STATUS_COMPLETED
from models import User

class TestRepairSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use a separate test database
        database.DB_NAME = "test_repair_system.db"
        # Reset DB for testing
        init_db()

    def test_01_user_login(self):
        user = UserService.login("admin", "admin")
        self.assertIsNotNone(user)
        self.assertEqual(user.role_name, "Administrator")
        
        user = UserService.login("wrong", "pass")
        self.assertIsNone(user)

    def test_02_create_request(self):
        req_num = RequestService.create_request(
            ("John Doe", "555-0100"),
            ("SN123", "AC Model X", "Cooling"),
            "Not working"
        )
        self.assertIsNotNone(req_num)
        
        requests = RequestService.get_requests("Administrator", 1)
        self.assertTrue(any(r.request_number == req_num for r in requests))

    def test_03_assign_specialist(self):
        # Get request
        requests = RequestService.get_requests("Administrator", 1)
        req = requests[0]
        
        # Get specialist (id 3 is specialist from seed)
        specs = UserService.get_specialists()
        spec_id = specs[0][0]
        
        success = RequestService.assign_specialist(req.id, spec_id)
        self.assertTrue(success)
        
        # Check assignment
        requests = RequestService.get_requests("Administrator", 1)
        self.assertIn(specs[0][1], requests[0].assigned_specialists)

    def test_04_complete_request(self):
        requests = RequestService.get_requests("Administrator", 1)
        req = requests[0]
        
        success = RequestService.update_status(req.id, STATUS_COMPLETED)
        self.assertTrue(success)
        
        # Check completion date
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT completion_date FROM requests WHERE id=?", (req.id,))
        date = c.fetchone()[0]
        conn.close()
        self.assertIsNotNone(date)

    def test_05_stats(self):
        from stats_module import calculate_statistics
        stats = calculate_statistics()
        self.assertEqual(stats['completed_count'], 1)
        self.assertIn("Not working", stats['problem_types'])

    def test_06_parts(self):
        # Test adding part
        success = PartService.add_part("Test Part", 10, 100.0)
        self.assertTrue(success)
        
        # Test assigning to request
        parts = PartService.get_all_parts()
        test_part = next(p for p in parts if p.name == "Test Part")
        
        requests = RequestService.get_requests("Administrator", 1)
        req = requests[0]
        
        success, msg = PartService.assign_part_to_request(req.id, test_part.id, 2)
        self.assertTrue(success)
        
        # Check usage
        req_parts = PartService.get_parts_for_request(req.id)
        self.assertEqual(len(req_parts), 1)
        self.assertEqual(req_parts[0].quantity_used, 2)
        
        # Check stock deduction
        updated_parts = PartService.get_all_parts()
        updated_part = next(p for p in updated_parts if p.id == test_part.id)
        self.assertEqual(updated_part.stock_quantity, 8)

if __name__ == '__main__':
    unittest.main()
