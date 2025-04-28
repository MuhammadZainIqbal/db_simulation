import sqlite3
import networkx as nx
import matplotlib
# Set non-interactive backend before importing pyplot
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import base64
from io import BytesIO
import time

class DeadlockDetection:
    """
    Simulates deadlock detection in databases using a wait-for graph.
    
    A deadlock occurs when two or more transactions are waiting for each other
    to release locks, resulting in a cycle in the wait-for graph.
    """
    
    def __init__(self, db_path):
        self.db_path = db_path
        
    def detect_deadlocks(self):
        """
        Run a deadlock detection simulation using a wait-for graph.
        
        Returns:
            dict: Results of the simulation including the wait-for graph and detected deadlocks.
        """
        results = {
            "explanation": "Deadlock detection using wait-for graph analysis",
            "transactions": [],
            "resources": [],
            "locks": [],
            "waits_for": [],
            "deadlocks": [],
            "graph_image": None,
            "steps": []
        }
        
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Clear any existing locks
        cursor.execute("DELETE FROM locks")
        conn.commit()
        
        # Get resources
        cursor.execute("SELECT * FROM resources")
        resources = [dict(row) for row in cursor.fetchall()]
        results["resources"] = resources
        
        # Define transaction ids for simulation
        transaction_ids = [101, 102, 103, 104]
        results["transactions"] = [{"id": t_id, "name": f"T{t_id}"} for t_id in transaction_ids]
        
        # Set up a simulation scenario that will create a deadlock
        lock_operations = [
            # T101 acquires lock on Resource A
            {"txn_id": 101, "resource_id": 1, "lock_type": "EXCLUSIVE"},
            
            # T102 acquires lock on Resource B
            {"txn_id": 102, "resource_id": 2, "lock_type": "EXCLUSIVE"},
            
            # T103 acquires lock on Resource C
            {"txn_id": 103, "resource_id": 3, "lock_type": "EXCLUSIVE"},
            
            # T104 acquires lock on Resource D
            {"txn_id": 104, "resource_id": 4, "lock_type": "EXCLUSIVE"},
            
            # T101 waits for Resource B (held by T102)
            {"txn_id": 101, "resource_id": 2, "lock_type": "WAITING"},
            
            # T102 waits for Resource C (held by T103)
            {"txn_id": 102, "resource_id": 3, "lock_type": "WAITING"},
            
            # T103 waits for Resource D (held by T104)
            {"txn_id": 103, "resource_id": 4, "lock_type": "WAITING"},
            
            # T104 waits for Resource A (held by T101) - creates a cycle
            {"txn_id": 104, "resource_id": 1, "lock_type": "WAITING"}
        ]
        
        # Apply locks and record the simulation steps
        for i, lock in enumerate(lock_operations):
            cursor.execute(
                "INSERT INTO locks (transaction_id, resource_id, lock_type) VALUES (?, ?, ?)",
                (lock["txn_id"], lock["resource_id"], lock["lock_type"])
            )
            conn.commit()
            
            # Get resource name for better reporting
            cursor.execute("SELECT name FROM resources WHERE id = ?", (lock["resource_id"],))
            resource_name = cursor.fetchone()[0]
            
            action = ""
            if lock["lock_type"] == "EXCLUSIVE":
                action = f"Transaction T{lock['txn_id']} acquires exclusive lock on {resource_name}"
            else:
                action = f"Transaction T{lock['txn_id']} waits for lock on {resource_name}"
                
                # Find who holds the lock
                cursor.execute("""
                    SELECT transaction_id FROM locks 
                    WHERE resource_id = ? AND lock_type = 'EXCLUSIVE'
                """, (lock["resource_id"],))
                holder = cursor.fetchone()
                if holder:
                    action += f" (held by T{holder[0]})"
            
            results["steps"].append({
                "step": i + 1,
                "action": action,
                "lock": lock
            })
            
            # Small delay to make the simulation more realistic
            time.sleep(0.1)
        
        # Collect all locks for result
        cursor.execute("SELECT * FROM locks")
        locks = [dict(row) for row in cursor.fetchall()]
        results["locks"] = locks
        
        # Build wait-for graph
        wait_for_graph = nx.DiGraph()
        
        # Add all transactions as nodes
        for txn in results["transactions"]:
            wait_for_graph.add_node(txn["id"], label=f"T{txn['id']}")
        
        # Add wait-for edges
        for lock in locks:
            if lock["lock_type"] == "WAITING":
                resource_id = lock["resource_id"]
                waiting_txn = lock["transaction_id"]
                
                # Find who holds the exclusive lock
                cursor.execute("""
                    SELECT transaction_id FROM locks 
                    WHERE resource_id = ? AND lock_type = 'EXCLUSIVE'
                """, (resource_id,))
                holder = cursor.fetchone()
                
                if holder:
                    holding_txn = holder[0]
                    # Add an edge from waiting transaction to holding transaction
                    wait_for_graph.add_edge(waiting_txn, holding_txn)
                    
                    # Add to results
                    results["waits_for"].append({
                        "waiting_txn": waiting_txn,
                        "waiting_txn_name": f"T{waiting_txn}",
                        "holding_txn": holding_txn,
                        "holding_txn_name": f"T{holding_txn}",
                        "resource_id": resource_id
                    })
        
        # Detect cycles (deadlocks)
        try:
            cycles = list(nx.simple_cycles(wait_for_graph))
            for cycle in cycles:
                cycle_with_names = [f"T{txn_id}" for txn_id in cycle]
                results["deadlocks"].append({
                    "cycle": cycle,
                    "cycle_with_names": cycle_with_names,
                    "description": " → ".join(cycle_with_names) + f" → {cycle_with_names[0]}"
                })
                
                # Add a step for deadlock detection
                results["steps"].append({
                    "step": len(results["steps"]) + 1,
                    "action": f"Deadlock detected: {' → '.join(cycle_with_names)} → {cycle_with_names[0]}",
                    "is_deadlock": True
                })
        except nx.NetworkXNoCycle:
            # No cycles found
            results["steps"].append({
                "step": len(results["steps"]) + 1,
                "action": "No deadlocks detected in the wait-for graph.",
                "is_deadlock": False
            })
        
        # Generate graph visualization
        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(wait_for_graph)
        nx.draw(wait_for_graph, pos, with_labels=True, node_color='lightblue', 
                node_size=500, arrows=True, arrowsize=20)
        
        # Save the graph to a base64 encoded string
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_data = base64.b64encode(buffer.read()).decode()
        results["graph_image"] = image_data
        plt.close()
        
        # Add deadlock resolution step
        if results["deadlocks"]:
            # Choose a victim transaction (usually the youngest transaction in the deadlock)
            victim = results["deadlocks"][0]["cycle"][0]
            
            # Delete the victim's locks
            cursor.execute("DELETE FROM locks WHERE transaction_id = ?", (victim,))
            conn.commit()
            
            results["steps"].append({
                "step": len(results["steps"]) + 1,
                "action": f"Deadlock resolved by aborting Transaction T{victim} (victim selection)",
                "victim": victim
            })
        
        conn.close()
        
        return results