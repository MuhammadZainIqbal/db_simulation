from flask import Flask, render_template, jsonify, request
import sqlite3
import os
import time
import threading
import functools
from models.mvcc import MVCCSimulation
from models.deadlock import DeadlockDetection
from models.two_phase_locking import TwoPhaseLockingBenchmark

app = Flask(__name__)

# Ensure database directory exists
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

# Global lock for preventing overlapping simulation requests
simulation_lock = threading.Lock()

# Rate limiter implementation for simulation endpoints
class RateLimiter:
    def __init__(self, max_calls=1, period=3):  # Allow 1 call per 3 seconds
        self.calls = {}
        self.max_calls = max_calls
        self.period = period
        self.lock = threading.Lock()
    
    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get client IP or a default if running locally
            client_id = request.remote_addr or "127.0.0.1"
            current_time = time.time()
            
            with self.lock:
                # Clean up old entries
                self.calls = {k: v for k, v in self.calls.items() 
                             if current_time - v[-1] < self.period}
                
                # Check if client has made too many calls
                if client_id in self.calls and len(self.calls[client_id]) >= self.max_calls:
                    last_call = self.calls[client_id][-1]
                    time_left = int(self.period - (current_time - last_call)) + 1
                    return jsonify({
                        "error": f"Please wait {time_left} seconds before trying again.",
                        "rate_limited": True
                    }), 429
                
                # Add this call
                if client_id not in self.calls:
                    self.calls[client_id] = []
                self.calls[client_id].append(current_time)
            
            # Execute the function
            return func(*args, **kwargs)
        
        return wrapper

# Create rate limiter instances
simulation_rate_limiter = RateLimiter(max_calls=1, period=3)

def init_db():
    """Initialize the SQLite database with sample data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        balance REAL NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transaction_log (
        txn_id INTEGER PRIMARY KEY,
        start_timestamp TEXT NOT NULL,
        commit_timestamp TEXT,
        status TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS account_versions (
        version_id INTEGER PRIMARY KEY,
        account_id INTEGER,
        balance REAL,
        txn_id INTEGER,
        timestamp TEXT,
        FOREIGN KEY (account_id) REFERENCES accounts (id),
        FOREIGN KEY (txn_id) REFERENCES transaction_log (txn_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        value INTEGER NOT NULL
    )
    ''')
    
    # Check if we need to insert initial data
    cursor.execute("SELECT COUNT(*) FROM accounts")
    count = cursor.fetchone()[0]
    
    if count == 0:
        cursor.execute("INSERT INTO accounts (name, balance) VALUES ('Alice', 1000.00)")
        cursor.execute("INSERT INTO accounts (name, balance) VALUES ('Bob', 2000.00)")
        
        cursor.execute("INSERT INTO items (name, value) VALUES ('Item 1', 100)")
        cursor.execute("INSERT INTO items (name, value) VALUES ('Item 2', 200)")
        cursor.execute("INSERT INTO items (name, value) VALUES ('Item 3', 300)")
        cursor.execute("INSERT INTO items (name, value) VALUES ('Item 4', 400)")
    
    conn.commit()
    conn.close()

# Initialize the database on startup
init_db()

@app.route('/')
def index():
    """Main page with simulation options"""
    return render_template('index.html')

@app.route('/mvcc')
def mvcc():
    """MVCC simulation page"""
    return render_template('mvcc.html')

@app.route('/api/run-mvcc')
@simulation_rate_limiter
def run_mvcc():
    """Run MVCC simulation and return results"""
    try:
        # Use a lock to prevent multiple simulations running at once
        if not simulation_lock.acquire(blocking=False):
            return jsonify({"error": "Another simulation is still running. Please try again in a moment."}), 429
        
        try:
            # Add a small delay to simulate processing time and avoid race conditions
            time.sleep(0.5)
            
            # Run the simulation
            simulation = MVCCSimulation(DB_PATH)
            results = simulation.run_simulation()
            return jsonify(results)
        finally:
            simulation_lock.release()
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/deadlock')
def deadlock():
    """Deadlock detection simulation page"""
    return render_template('deadlock.html')

@app.route('/api/run-deadlock')
@simulation_rate_limiter
def run_deadlock():
    """Run deadlock detection simulation and return results"""
    try:
        # Use a lock to prevent multiple simulations running at once
        if not simulation_lock.acquire(blocking=False):
            return jsonify({"error": "Another simulation is still running. Please try again in a moment."}), 429
        
        try:
            # Add a small delay to simulate processing time and avoid race conditions
            time.sleep(0.5)
            
            # Run the simulation
            detection = DeadlockDetection(DB_PATH)
            results = detection.detect_deadlocks()
            return jsonify(results)
        finally:
            simulation_lock.release()
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/two-phase-locking')
def two_phase_locking():
    """2PL benchmarking simulation page"""
    return render_template('two_phase_locking.html')

@app.route('/api/run-2pl')
@simulation_rate_limiter
def run_2pl():
    """Run 2PL benchmark simulation and return results"""
    try:
        # Use a lock to prevent multiple simulations running at once
        if not simulation_lock.acquire(blocking=False):
            return jsonify({"error": "Another simulation is still running. Please try again in a moment."}), 429
        
        try:
            # Add a small delay to simulate processing time and avoid race conditions
            time.sleep(0.5)
            
            # Run the simulation
            benchmark = TwoPhaseLockingBenchmark(DB_PATH)
            results = benchmark.run_benchmark()
            return jsonify(results)
        finally:
            simulation_lock.release()
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)