import sqlite3
import time
import datetime
import random
import matplotlib
# Set non-interactive backend before importing pyplot
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO

class TwoPhaseLockingBenchmark:
    """
    Simulates and benchmarks Two-Phase Locking (2PL) protocol in databases.
    
    Two-Phase Locking is a concurrency control method that ensures serializability
    by dividing transaction execution into two phases:
    1. Growing phase (only acquire locks, never release)
    2. Shrinking phase (only release locks, never acquire)
    """
    
    def __init__(self, db_path):
        self.db_path = db_path
        
    def _get_timestamp(self):
        """Generate a timestamp string"""
        return datetime.datetime.now().isoformat()
    
    def run_benchmark(self):
        """
        Run a benchmark comparing 2PL with MVCC performance and characteristics.
        
        Returns:
            dict: Results of the benchmark including timing, conflicts, and analysis.
        """
        results = {
            "explanation": "Two-Phase Locking (2PL) simulation and comparison with MVCC",
            "benchmarks": {
                "2pl": {"timeline": [], "conflicts": 0, "aborts": 0, "duration": 0},
                "mvcc": {"timeline": [], "conflicts": 0, "aborts": 0, "duration": 0},
            },
            "comparison": {},
            "chart": None
        }
        
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Reset items to initial state
        cursor.execute("UPDATE items SET value = 100 WHERE name = 'Item 1'")
        cursor.execute("UPDATE items SET value = 200 WHERE name = 'Item 2'")
        cursor.execute("UPDATE items SET value = 300 WHERE name = 'Item 3'")
        cursor.execute("UPDATE items SET value = 400 WHERE name = 'Item 4'")
        conn.commit()
        
        # Simulate 2PL protocol
        start_time = time.time()
        self._simulate_2pl(cursor, results["benchmarks"]["2pl"]["timeline"])
        end_time = time.time()
        results["benchmarks"]["2pl"]["duration"] = end_time - start_time
        
        # Reset items to initial state
        cursor.execute("UPDATE items SET value = 100 WHERE name = 'Item 1'")
        cursor.execute("UPDATE items SET value = 200 WHERE name = 'Item 2'")
        cursor.execute("UPDATE items SET value = 300 WHERE name = 'Item 3'")
        cursor.execute("UPDATE items SET value = 400 WHERE name = 'Item 4'")
        conn.commit()
        
        # Simulate MVCC protocol
        start_time = time.time()
        self._simulate_mvcc(cursor, results["benchmarks"]["mvcc"]["timeline"])
        end_time = time.time()
        results["benchmarks"]["mvcc"]["duration"] = end_time - start_time
        
        # Count conflicts and aborts in 2PL simulation
        for event in results["benchmarks"]["2pl"]["timeline"]:
            if "conflict" in event.get("action", "").lower():
                results["benchmarks"]["2pl"]["conflicts"] += 1
            if "abort" in event.get("action", "").lower():
                results["benchmarks"]["2pl"]["aborts"] += 1
        
        # Count conflicts and aborts in MVCC simulation
        for event in results["benchmarks"]["mvcc"]["timeline"]:
            if "conflict" in event.get("action", "").lower():
                results["benchmarks"]["mvcc"]["conflicts"] += 1
            if "abort" in event.get("action", "").lower():
                results["benchmarks"]["mvcc"]["aborts"] += 1
        
        # Generate comparison analysis
        results["comparison"] = {
            "speed": {
                "2pl": results["benchmarks"]["2pl"]["duration"],
                "mvcc": results["benchmarks"]["mvcc"]["duration"],
                "faster": "MVCC" if results["benchmarks"]["mvcc"]["duration"] < results["benchmarks"]["2pl"]["duration"] else "2PL",
                "difference_pct": abs(1 - (results["benchmarks"]["mvcc"]["duration"] / results["benchmarks"]["2pl"]["duration"])) * 100
            },
            "conflicts": {
                "2pl": results["benchmarks"]["2pl"]["conflicts"],
                "mvcc": results["benchmarks"]["mvcc"]["conflicts"],
                "difference": abs(results["benchmarks"]["2pl"]["conflicts"] - results["benchmarks"]["mvcc"]["conflicts"])
            },
            "aborts": {
                "2pl": results["benchmarks"]["2pl"]["aborts"],
                "mvcc": results["benchmarks"]["mvcc"]["aborts"],
                "difference": abs(results["benchmarks"]["2pl"]["aborts"] - results["benchmarks"]["mvcc"]["aborts"])
            },
            "analysis": [
                "MVCC generally provides better concurrency by allowing multiple versions of data.",
                "2PL prevents conflicts by using strict locking but can lead to more waiting time.",
                "MVCC performs better for read-heavy workloads, while 2PL may be better for write-intensive workloads with potential conflicts.",
                "2PL has potential for deadlocks which MVCC largely avoids.",
                "MVCC requires more storage space for maintaining multiple versions."
            ]
        }
        
        # Generate comparison chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        metrics = ['Duration (s)', 'Conflicts', 'Aborts']
        two_pl_values = [
            results["benchmarks"]["2pl"]["duration"],
            results["benchmarks"]["2pl"]["conflicts"],
            results["benchmarks"]["2pl"]["aborts"]
        ]
        mvcc_values = [
            results["benchmarks"]["mvcc"]["duration"],
            results["benchmarks"]["mvcc"]["conflicts"],
            results["benchmarks"]["mvcc"]["aborts"]
        ]
        
        x = range(len(metrics))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], two_pl_values, width, label='2PL')
        ax.bar([i + width/2 for i in x], mvcc_values, width, label='MVCC')
        
        ax.set_ylabel('Values')
        ax.set_title('2PL vs MVCC Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(metrics)
        ax.legend()
        
        # Save the chart to a base64 encoded string
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_data = base64.b64encode(buffer.read()).decode()
        results["chart"] = image_data
        plt.close()
        
        conn.close()
        
        return results
    
    def _simulate_2pl(self, cursor, timeline):
        """
        Simulate transactions using the Two-Phase Locking protocol.
        
        Args:
            cursor: Database cursor
            timeline: List to append events to
        """
        # Initialize lock table (in-memory for simulation)
        locks = {}
        
        # Define transaction set
        transactions = [
            {"id": 201, "name": "T201", "ops": [
                {"type": "read", "item": "Item 1"},
                {"type": "read", "item": "Item 3"},
                {"type": "write", "item": "Item 1", "value_change": 50},
                {"type": "write", "item": "Item 3", "value_change": -30}
            ]},
            {"id": 202, "name": "T202", "ops": [
                {"type": "read", "item": "Item 2"},
                {"type": "read", "item": "Item 1"},
                {"type": "write", "item": "Item 2", "value_change": -20},
                {"type": "write", "item": "Item 1", "value_change": 10}
            ]},
            {"id": 203, "name": "T203", "ops": [
                {"type": "read", "item": "Item 3"},
                {"type": "read", "item": "Item 4"},
                {"type": "write", "item": "Item 4", "value_change": 25},
                {"type": "write", "item": "Item 3", "value_change": 15}
            ]}
        ]
        
        # Process transactions
        for txn in transactions:
            timeline.append({
                "time": self._get_timestamp(),
                "action": f"Transaction {txn['name']} started (2PL)",
                "txn_id": txn["id"]
            })
            
            txn_locks = []  # Track locks acquired by this transaction
            txn_conflict = False
            txn_data = {}  # Local transaction data
            
            # Phase 1: Growing phase (acquire all locks needed)
            for op in txn["ops"]:
                item = op["item"]
                lock_type = "READ" if op["type"] == "read" else "WRITE"
                
                # Check if lock can be acquired
                if item in locks:
                    current_lock = locks[item]
                    
                    # If another transaction has a WRITE lock, we have a conflict
                    if current_lock["txn_id"] != txn["id"] and (current_lock["type"] == "WRITE" or lock_type == "WRITE"):
                        timeline.append({
                            "time": self._get_timestamp(),
                            "action": f"{txn['name']} - Lock conflict on {item}: {current_lock['txn_id']} holds {current_lock['type']} lock",
                            "txn_id": txn["id"],
                            "conflict": True
                        })
                        txn_conflict = True
                        break
                    
                    # Upgrade READ lock to WRITE if needed by same transaction
                    if current_lock["txn_id"] == txn["id"] and current_lock["type"] == "READ" and lock_type == "WRITE":
                        locks[item] = {"txn_id": txn["id"], "type": "WRITE"}
                        timeline.append({
                            "time": self._get_timestamp(),
                            "action": f"{txn['name']} - Upgraded READ lock to WRITE lock on {item}",
                            "txn_id": txn["id"]
                        })
                else:
                    # Acquire new lock
                    locks[item] = {"txn_id": txn["id"], "type": lock_type}
                    txn_locks.append(item)
                    
                    timeline.append({
                        "time": self._get_timestamp(),
                        "action": f"{txn['name']} - Acquired {lock_type} lock on {item}",
                        "txn_id": txn["id"]
                    })
                
                # For READ operations, get the current value
                if op["type"] == "read":
                    cursor.execute(f"SELECT value FROM items WHERE name = ?", (item,))
                    value = cursor.fetchone()["value"]
                    txn_data[item] = value
                    
                    timeline.append({
                        "time": self._get_timestamp(),
                        "action": f"{txn['name']} - Read {item} = {value}",
                        "txn_id": txn["id"],
                        "data": {"item": item, "value": value}
                    })
            
            # If conflict occurred, abort transaction
            if txn_conflict:
                timeline.append({
                    "time": self._get_timestamp(),
                    "action": f"Transaction {txn['name']} aborted due to lock conflict",
                    "txn_id": txn["id"],
                    "abort": True
                })
                
                # Release all locks held by this transaction
                for item in txn_locks:
                    if item in locks and locks[item]["txn_id"] == txn["id"]:
                        del locks[item]
                
                continue
            
            # Perform writes (still in phase 1 since we haven't released any locks)
            for op in txn["ops"]:
                if op["type"] == "write":
                    item = op["item"]
                    original_value = txn_data.get(item)
                    
                    # If we don't have the value in local data, fetch it
                    if original_value is None:
                        cursor.execute(f"SELECT value FROM items WHERE name = ?", (item,))
                        original_value = cursor.fetchone()["value"]
                    
                    new_value = original_value + op["value_change"]
                    
                    # Apply change to database (we don't actually commit until all operations are done)
                    cursor.execute(f"UPDATE items SET value = ? WHERE name = ?", (new_value, item))
                    
                    timeline.append({
                        "time": self._get_timestamp(),
                        "action": f"{txn['name']} - Write {item} = {new_value} (changed by {op['value_change']})",
                        "txn_id": txn["id"],
                        "data": {"item": item, "old_value": original_value, "new_value": new_value}
                    })
            
            # Phase 2: Shrinking phase (release all locks)
            for item in txn_locks:
                if item in locks and locks[item]["txn_id"] == txn["id"]:
                    del locks[item]
                    
                    timeline.append({
                        "time": self._get_timestamp(),
                        "action": f"{txn['name']} - Released lock on {item}",
                        "txn_id": txn["id"]
                    })
            
            # Commit the transaction
            timeline.append({
                "time": self._get_timestamp(),
                "action": f"Transaction {txn['name']} committed",
                "txn_id": txn["id"],
                "commit": True
            })
            
            cursor.connection.commit()
            
            # Add some delay between transactions for more realistic simulation
            time.sleep(0.1)
    
    def _simulate_mvcc(self, cursor, timeline):
        """
        Simulate transactions using MVCC protocol for comparison.
        
        Args:
            cursor: Database cursor
            timeline: List to append events to
        """
        # Define transaction set (same operations as 2PL for comparison)
        transactions = [
            {"id": 301, "name": "T301", "ops": [
                {"type": "read", "item": "Item 1"},
                {"type": "read", "item": "Item 3"},
                {"type": "write", "item": "Item 1", "value_change": 50},
                {"type": "write", "item": "Item 3", "value_change": -30}
            ]},
            {"id": 302, "name": "T302", "ops": [
                {"type": "read", "item": "Item 2"},
                {"type": "read", "item": "Item 1"},
                {"type": "write", "item": "Item 2", "value_change": -20},
                {"type": "write", "item": "Item 1", "value_change": 10}
            ]},
            {"id": 303, "name": "T303", "ops": [
                {"type": "read", "item": "Item 3"},
                {"type": "read", "item": "Item 4"},
                {"type": "write", "item": "Item 4", "value_change": 25},
                {"type": "write", "item": "Item 3", "value_change": 15}
            ]}
        ]
        
        # In-memory version store for MVCC simulation
        version_store = {}
        read_timestamps = {}  # Tracks read timestamps for each transaction
        write_timestamps = {}  # Tracks write timestamps for each transaction
        txn_start_times = {}  # Tracks start times for each transaction
        
        # Create a temporary version table for simulation
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS temp_item_versions (
            version_id INTEGER PRIMARY KEY,
            item_name TEXT NOT NULL,
            value INTEGER NOT NULL,
            txn_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
        """)
        cursor.connection.commit()
        
        # Initialize version store with current values
        cursor.execute("SELECT * FROM items")
        items = cursor.fetchall()
        current_time = self._get_timestamp()
        
        for item in items:
            item_name = item["name"]
            value = item["value"]
            
            # Add initial version
            cursor.execute(
                "INSERT INTO temp_item_versions (item_name, value, txn_id, timestamp) VALUES (?, ?, ?, ?)",
                (item_name, value, 0, current_time)
            )
            
            version_store[item_name] = [{
                "value": value,
                "txn_id": 0,  # System transaction
                "timestamp": current_time
            }]
        
        cursor.connection.commit()
        
        # Process transactions
        for txn in transactions:
            # Start transaction
            start_time = self._get_timestamp()
            txn_start_times[txn["id"]] = start_time
            read_timestamps[txn["id"]] = start_time
            write_timestamps[txn["id"]] = start_time
            
            timeline.append({
                "time": start_time,
                "action": f"Transaction {txn['name']} started (MVCC)",
                "txn_id": txn["id"]
            })
            
            txn_data = {}  # Local transaction data
            
            # Process each operation
            for op in txn["ops"]:
                item = op["item"]
                
                if op["type"] == "read":
                    # In MVCC, read the most recent version visible to this transaction
                    visible_versions = []
                    
                    # Get versions for this item
                    cursor.execute("""
                        SELECT * FROM temp_item_versions
                        WHERE item_name = ? AND timestamp <= ?
                        ORDER BY timestamp DESC
                    """, (item, txn_start_times[txn["id"]]))
                    
                    item_versions = cursor.fetchall()
                    
                    if item_versions:
                        latest_version = item_versions[0]
                        value = latest_version["value"]
                        txn_data[item] = value
                        
                        timeline.append({
                            "time": self._get_timestamp(),
                            "action": f"{txn['name']} - Read {item} = {value} (version from {latest_version['timestamp']})",
                            "txn_id": txn["id"],
                            "data": {"item": item, "value": value}
                        })
                    else:
                        # No visible version found (shouldn't happen with our setup)
                        timeline.append({
                            "time": self._get_timestamp(),
                            "action": f"{txn['name']} - No visible version for {item}",
                            "txn_id": txn["id"],
                            "error": True
                        })
                
                elif op["type"] == "write":
                    # Get the most recent value
                    original_value = txn_data.get(item)
                    
                    if original_value is None:
                        # If we haven't read this item yet, find the visible version
                        cursor.execute("""
                            SELECT * FROM temp_item_versions
                            WHERE item_name = ? AND timestamp <= ?
                            ORDER BY timestamp DESC
                            LIMIT 1
                        """, (item, txn_start_times[txn["id"]]))
                        
                        version = cursor.fetchone()
                        if version:
                            original_value = version["value"]
                        else:
                            # No visible version found (shouldn't happen with our setup)
                            timeline.append({
                                "time": self._get_timestamp(),
                                "action": f"{txn['name']} - Cannot write to {item}: no visible version",
                                "txn_id": txn["id"],
                                "error": True
                            })
                            continue
                    
                    # Calculate new value
                    new_value = original_value + op["value_change"]
                    timestamp = self._get_timestamp()
                    
                    # Check for write conflicts - in MVCC, we need to ensure this transaction's
                    # read set hasn't been modified by other transactions
                    cursor.execute("""
                        SELECT * FROM temp_item_versions
                        WHERE item_name = ? AND timestamp > ? AND txn_id != ?
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, (item, txn_start_times[txn["id"]], txn["id"]))
                    
                    conflict_version = cursor.fetchone()
                    
                    if conflict_version:
                        # Write conflict detected - in a real system, this would trigger abort
                        timeline.append({
                            "time": timestamp,
                            "action": f"{txn['name']} - Write conflict on {item}: newer version exists",
                            "txn_id": txn["id"],
                            "conflict": True
                        })
                        continue
                    
                    # Create new version in MVCC
                    cursor.execute(
                        "INSERT INTO temp_item_versions (item_name, value, txn_id, timestamp) VALUES (?, ?, ?, ?)",
                        (item, new_value, txn["id"], timestamp)
                    )
                    
                    timeline.append({
                        "time": timestamp,
                        "action": f"{txn['name']} - Create new version of {item} = {new_value} (changed by {op['value_change']})",
                        "txn_id": txn["id"],
                        "data": {"item": item, "old_value": original_value, "new_value": new_value}
                    })
            
            # Commit the transaction
            commit_time = self._get_timestamp()
            
            timeline.append({
                "time": commit_time,
                "action": f"Transaction {txn['name']} committed",
                "txn_id": txn["id"],
                "commit": True
            })
            
            cursor.connection.commit()
            
            # Update actual item values to reflect the final committed versions
            for op in txn["ops"]:
                if op["type"] == "write":
                    item = op["item"]
                    
                    # Get the latest value this transaction wrote
                    cursor.execute("""
                        SELECT value FROM temp_item_versions
                        WHERE item_name = ? AND txn_id = ?
                        ORDER BY version_id DESC
                        LIMIT 1
                    """, (item, txn["id"]))
                    
                    latest_value = cursor.fetchone()
                    
                    if latest_value:
                        # Update the actual item in the database
                        cursor.execute(
                            "UPDATE items SET value = ? WHERE name = ?",
                            (latest_value["value"], item)
                        )
            
            cursor.connection.commit()
            
            # Add some delay between transactions for more realistic simulation
            time.sleep(0.1)
        
        # Clean up temporary table
        cursor.execute("DROP TABLE temp_item_versions")
        cursor.connection.commit()