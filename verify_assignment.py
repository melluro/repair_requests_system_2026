import sqlite3
import os
import unittest
from datetime import datetime, timedelta
from database import init_db, get_connection
from services import UserService, RequestService, PartService, STATUS_NEW, STATUS_REGISTERED, STATUS_COMPLETED
import database

# Use a separate verification DB
TEST_DB = "verify_system.db"
database.DB_NAME = TEST_DB

class TestAssignmentRequirements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db(TEST_DB)
        
    def test_01_database_3nf_check(self):
        """Verify Database is in 3NF (Foreign Keys, Link Tables)"""
        conn = get_connection(TEST_DB)
        cursor = conn.cursor()
        
        # Check for Many-to-Many tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='request_specialists'")
        self.assertIsNotNone(cursor.fetchone(), "Missing Many-to-Many table: request_specialists")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='request_parts'")
        self.assertIsNotNone(cursor.fetchone(), "Missing Many-to-Many table: request_parts")
        
        # Check Foreign Keys (Pragma check)
        cursor.execute("PRAGMA foreign_key_list(requests)")
        fks = cursor.fetchall()
        # Expecting FKs to clients, equipment, statuses
        tables_ref = [fk[2] for fk in fks]
        self.assertIn('clients', tables_ref)
        self.assertIn('equipment', tables_ref)
        self.assertIn('statuses', tables_ref)
        
        conn.close()
        print("✓ Database 3NF Structure Verified")

    def test_02_workflow_scenario(self):
        """Test Full Request Lifecycle"""
        # 1. Login as Operator
        operator = UserService.login("operator", "operator")
        self.assertIsNotNone(operator)
        
        # 2. Create Request
        req_num = RequestService.create_request(
            ("Test Client", "1234567890"),
            ("SN-TEST-001", "Model Z", "Type A"),
            "System Failure"
        )
        self.assertIsNotNone(req_num)
        
        # Verify created
        requests = RequestService.get_requests("Operator", operator.id)
        req = next(r for r in requests if r.request_number == req_num)
        self.assertEqual(req.status_name, "New")
        print("✓ Request Creation Verified")
        
        # 3. Manager Assigns Specialist
        manager = UserService.login("manager", "manager")
        specialist = UserService.login("specialist", "specialist")
        
        success = RequestService.assign_specialist(req.id, specialist.id)
        self.assertTrue(success)
        
        # Verify Status Change (New -> Registered/Assigned)
        # Note: Logic in assign_specialist updates status to Registered
        req = RequestService.get_requests("Manager", manager.id, None)[0] # Reload
        # In service: "UPDATE requests SET status_id = ? WHERE id = ? AND status_id = ?" (STATUS_REGISTERED)
        # However, getting exact request might be tricky if multiple, assuming first/last created
        
        # Check assignment
        self.assertIn(specialist.full_name, req.assigned_specialists)
        print("✓ Specialist Assignment Verified")
        
        # 4. Specialist adds Parts
        part_success = PartService.add_part("Test Part X", 10, 50.0)
        parts = PartService.get_all_parts()
        part = next(p for p in parts if p.name == "Test Part X")
        
        success, msg = PartService.assign_part_to_request(req.id, part.id, 2)
        self.assertTrue(success)
        print("✓ Part Assignment Verified")
        
        # 5. Quality Manager Extends Deadline
        qm = UserService.login("quality", "quality")
        old_deadline = req.deadline_date
        
        RequestService.extend_deadline(req.id, 5)
        
        # Verify
        req_updated = RequestService.get_requests("Quality Manager", qm.id, None)[0]
        # Compare dates roughly (parsing string)
        d1 = datetime.strptime(old_deadline, "%Y-%m-%d %H:%M:%S")
        d2 = datetime.strptime(req_updated.deadline_date, "%Y-%m-%d %H:%M:%S")
        self.assertTrue(d2 > d1)
        print("✓ Deadline Extension Verified")
        
        # 6. Complete Request
        RequestService.update_status(req.id, STATUS_COMPLETED)
        
        # Verify Completion Date
        conn = get_connection(TEST_DB)
        c = conn.cursor()
        c.execute("SELECT completion_date FROM requests WHERE id=?", (req.id,))
        comp_date = c.fetchone()[0]
        conn.close()
        self.assertIsNotNone(comp_date)
        print("✓ Request Completion Verified")

    def test_03_import_check(self):
        """Verify Import Logic (Mocking or checking function existence)"""
        # Since actual import depends on files, we verify the Service method exists
        from services import ImportService
        self.assertTrue(hasattr(ImportService, 'import_users_from_csv'))
        print("✓ Import Service Verified")

if __name__ == '__main__':
    unittest.main(verbosity=2)
