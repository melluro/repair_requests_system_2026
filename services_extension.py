    @staticmethod
    def toggle_help_needed(request_id, needed: bool):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE requests SET help_needed = ? WHERE id = ?", (1 if needed else 0, request_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error toggling help: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def update_deadline(request_id, new_date_str):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE requests SET deadline_date = ? WHERE id = ?", (new_date_str, request_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating deadline: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def assign_specialist(request_id, specialist_id):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Check if already assigned
            cursor.execute("SELECT * FROM request_specialists WHERE request_id = ? AND specialist_id = ?", (request_id, specialist_id))
            if cursor.fetchone():
                return True # Already assigned
            
            cursor.execute("INSERT INTO request_specialists (request_id, specialist_id) VALUES (?, ?)", (request_id, specialist_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error assigning specialist: {e}")
            return False
        finally:
            conn.close()
