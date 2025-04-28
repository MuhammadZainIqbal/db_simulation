import sqlite3
import time
import datetime
import json

class MVCCSimulation:
    """
    Simulates Multi-Version Concurrency Control (MVCC) in databases.
    
    MVCC allows multiple transactions to read the same database state without blocking
    by keeping multiple versions of data. Each transaction sees a snapshot of data as it
    was when the transaction started.
    """
    
    def __init__(self, db_path):
        self.db_path = db_path
        
    def _get_timestamp(self):
        """Generate a timestamp string for versioning"""
        return datetime.datetime.now().isoformat()
    
    def run_simulation(self):
        """
        Run a predefined MVCC simulation with multiple transactions
        to demonstrate version handling and transaction isolation.
        """
        results = {
            "explanation": "MVCC Simulation demonstrates how databases handle concurrent transactions by maintaining different versions of data.",
            "timeline": [],
            "transactions": [],
            "versions": []
        }
        
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Clear previous simulation data if any
        cursor.execute("DELETE FROM transaction_log")
        cursor.execute("DELETE FROM account_versions")
        
        # Reset accounts to initial state
        cursor.execute("UPDATE accounts SET balance = 1000.00 WHERE name = 'Alice'")
        cursor.execute("UPDATE accounts SET balance = 2000.00 WHERE name = 'Bob'")
        conn.commit()
        
        # Fetch initial account states
        cursor.execute("SELECT * FROM accounts WHERE name IN ('Alice', 'Bob')")
        initial_accounts = [dict(row) for row in cursor.fetchall()]
        results["timeline"].append({
            "time": self._get_timestamp(),
            "action": "Initial state",
            "data": initial_accounts
        })
        
        # Create Transaction 1 (T1) - Transfer from Alice to Bob
        t1_start = self._get_timestamp()
        cursor.execute(
            "INSERT INTO transaction_log (start_timestamp, status) VALUES (?, ?)",
            (t1_start, "STARTED")
        )
        t1_id = cursor.lastrowid
        
        results["timeline"].append({
            "time": t1_start,
            "action": f"Transaction T{t1_id} started",
            "data": {"transaction_id": t1_id}
        })
        
        # T1 reads Alice's balance
        cursor.execute("SELECT * FROM accounts WHERE name = 'Alice'")
        alice_account = dict(cursor.fetchone())
        alice_initial_balance = alice_account["balance"]
        
        results["timeline"].append({
            "time": self._get_timestamp(),
            "action": f"T{t1_id} reads Alice's balance",
            "data": {"balance": alice_initial_balance}
        })
        
        # Create Transaction 2 (T2) - Independent update to Bob's account
        time.sleep(0.1)  # Small delay to clearly separate transaction times
        t2_start = self._get_timestamp()
        cursor.execute(
            "INSERT INTO transaction_log (start_timestamp, status) VALUES (?, ?)",
            (t2_start, "STARTED")
        )
        t2_id = cursor.lastrowid
        
        results["timeline"].append({
            "time": t2_start,
            "action": f"Transaction T{t2_id} started",
            "data": {"transaction_id": t2_id}
        })
        
        # T2 reads Bob's balance
        cursor.execute("SELECT * FROM accounts WHERE name = 'Bob'")
        bob_account = dict(cursor.fetchone())
        bob_initial_balance = bob_account["balance"]
        
        results["timeline"].append({
            "time": self._get_timestamp(),
            "action": f"T{t2_id} reads Bob's balance",
            "data": {"balance": bob_initial_balance}
        })
        
        # T2 updates Bob's balance (adding 500)
        new_bob_balance = bob_initial_balance + 500
        timestamp = self._get_timestamp()
        
        # Create a new version for Bob's account
        cursor.execute(
            """
            INSERT INTO account_versions (account_id, balance, txn_id, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (bob_account["id"], new_bob_balance, t2_id, timestamp)
        )
        
        results["timeline"].append({
            "time": timestamp,
            "action": f"T{t2_id} creates new version of Bob's account",
            "data": {"new_balance": new_bob_balance}
        })
        
        # T2 commits
        t2_commit = self._get_timestamp()
        cursor.execute(
            "UPDATE transaction_log SET commit_timestamp = ?, status = ? WHERE txn_id = ?",
            (t2_commit, "COMMITTED", t2_id)
        )
        
        # Update the actual account record
        cursor.execute(
            "UPDATE accounts SET balance = ? WHERE name = ?",
            (new_bob_balance, "Bob")
        )
        
        conn.commit()
        
        results["timeline"].append({
            "time": t2_commit,
            "action": f"T{t2_id} commits",
            "data": {"new_bob_balance": new_bob_balance}
        })
        
        # Now T1 continues and tries to read Bob's balance
        # Note: In true MVCC, T1 would see Bob's balance as it was when T1 started
        # We'll simulate this by fetching the version visible to T1
        cursor.execute("""
            SELECT v.balance
            FROM account_versions v
            JOIN transaction_log t ON v.txn_id = t.txn_id
            WHERE v.account_id = ? AND t.start_timestamp < ?
            ORDER BY t.start_timestamp DESC
            LIMIT 1
        """, (bob_account["id"], t1_start))
        
        # If no version exists prior to T1's start, use the initial balance
        bob_balance_t1_sees = bob_initial_balance
        row = cursor.fetchone()
        if row:
            bob_balance_t1_sees = row[0]
        
        results["timeline"].append({
            "time": self._get_timestamp(),
            "action": f"T{t1_id} reads Bob's balance (snapshot isolation)",
            "data": {
                "balance_t1_sees": bob_balance_t1_sees,
                "actual_current_balance": new_bob_balance,
                "note": "T1 sees the version of data as it existed when T1 started"
            }
        })
        
        # T1 updates Alice's balance (subtract 200)
        new_alice_balance = alice_initial_balance - 200
        timestamp = self._get_timestamp()
        
        # Create a new version for Alice's account
        cursor.execute(
            """
            INSERT INTO account_versions (account_id, balance, txn_id, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (alice_account["id"], new_alice_balance, t1_id, timestamp)
        )
        
        results["timeline"].append({
            "time": timestamp,
            "action": f"T{t1_id} creates new version of Alice's account",
            "data": {"new_balance": new_alice_balance}
        })
        
        # T1 updates Bob's balance (add 200)
        new_bob_balance_t1 = bob_balance_t1_sees + 200
        timestamp = self._get_timestamp()
        
        # Create a new version for Bob's account
        cursor.execute(
            """
            INSERT INTO account_versions (account_id, balance, txn_id, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (bob_account["id"], new_bob_balance_t1, t1_id, timestamp)
        )
        
        results["timeline"].append({
            "time": timestamp,
            "action": f"T{t1_id} creates new version of Bob's account",
            "data": {"new_balance": new_bob_balance_t1}
        })
        
        # T1 commits
        t1_commit = self._get_timestamp()
        cursor.execute(
            "UPDATE transaction_log SET commit_timestamp = ?, status = ? WHERE txn_id = ?",
            (t1_commit, "COMMITTED", t1_id)
        )
        
        # Update the actual account records
        cursor.execute(
            "UPDATE accounts SET balance = ? WHERE name = ?",
            (new_alice_balance, "Alice")
        )
        
        # For Bob's balance, we need to handle the conflict
        # In a real MVCC system, this might cause a serialization failure
        # For simulation, we'll apply T1's changes on top of T2's changes
        final_bob_balance = new_bob_balance + 200  # T2's changes + T1's transfer
        cursor.execute(
            "UPDATE accounts SET balance = ? WHERE name = ?",
            (final_bob_balance, "Bob")
        )
        
        conn.commit()
        
        results["timeline"].append({
            "time": t1_commit,
            "action": f"T{t1_id} commits with conflict resolution",
            "data": {
                "new_alice_balance": new_alice_balance,
                "final_bob_balance": final_bob_balance,
                "note": "Bob's final balance combines both T1 and T2's changes"
            }
        })
        
        # Fetch all transactions for the result
        cursor.execute("SELECT * FROM transaction_log")
        results["transactions"] = [dict(row) for row in cursor.fetchall()]
        
        # Fetch all versions for the result
        cursor.execute("""
            SELECT v.*, a.name as account_name 
            FROM account_versions v
            JOIN accounts a ON v.account_id = a.id
            ORDER BY v.timestamp
        """)
        results["versions"] = [dict(row) for row in cursor.fetchall()]
        
        # Fetch final state
        cursor.execute("SELECT * FROM accounts WHERE name IN ('Alice', 'Bob')")
        final_accounts = [dict(row) for row in cursor.fetchall()]
        results["timeline"].append({
            "time": self._get_timestamp(),
            "action": "Final state",
            "data": final_accounts
        })
        
        conn.close()
        
        return results