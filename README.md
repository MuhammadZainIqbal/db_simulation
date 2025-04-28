# Database Engine Simulation Lab

A comprehensive educational tool for visualizing and understanding core database concurrency control mechanisms through interactive simulations.

## Overview

This application provides interactive visualizations of critical database engine concurrency control mechanisms that are foundational to modern database management systems. Through dynamic simulations, it demonstrates:

- **Multi-Version Concurrency Control (MVCC)**: Visualize how databases maintain multiple versions of data to enable concurrent transactions without traditional locking.
- **Deadlock Detection**: Explore wait-for graph analysis to identify and resolve circular wait conditions between transactions.
- **Two-Phase Locking (2PL)**: Benchmark the performance characteristics of 2PL concurrency control protocols and understand their implementation details.

## Features

- **Interactive Simulations**: Real-time visualizations of database transaction execution with step-by-step playback
- **Educational Explanations**: Comprehensive descriptions of each concurrency control mechanism
- **Wait-For Graph Analysis**: Visual representation of transaction dependencies and deadlock cycles
- **Transaction Timeline Visualization**: Chronological display of operations with detailed event tracking
- **Performance Metrics**: Statistical analysis of transaction throughput and concurrency levels
- **Version Tracking**: Visual representation of data version creation and management in MVCC

## Technology Stack

- **Backend**: Python with Flask web framework
- **Database**: SQLite for data storage and transaction simulation
- **Visualization**: Matplotlib for graph generation
- **Frontend**: HTML5, JavaScript, and Tailwind CSS
- **Graph Analysis**: NetworkX library for deadlock cycle detection

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/db-simulation.git
   cd db-simulation
   ```

2. Create and activate a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Project Structure

```
app.py                 # Flask application entry point
database.db            # SQLite database file
models/                # Simulation models 
  ├── deadlock.py      # Deadlock detection simulation
  ├── mvcc.py          # Multi-Version Concurrency Control simulation
  └── two_phase_locking.py  # Two-Phase Locking benchmark
static/                # Static assets (CSS, JS, images)
templates/             # HTML templates
  ├── deadlock.html    # Deadlock detection visualization
  ├── index.html       # Home page
  ├── mvcc.html        # MVCC simulation interface
  └── two_phase_locking.html  # 2PL benchmark interface
```

## Usage

1. **Home Page**: Navigate between the different simulation options
2. **MVCC Simulation**: Visualize transaction isolation through version-based concurrency control
3. **Deadlock Detection**: Observe how databases identify and resolve circular wait conditions
4. **Two-Phase Locking**: Compare performance characteristics of lock-based concurrency control

## Technical Implementation Details

### Multi-Version Concurrency Control (MVCC)
- Demonstrates version creation and transaction isolation without blocking readers
- Implements snapshot isolation through timestamped versioning
- Visualizes concurrent read/write operations and version management

### Deadlock Detection
- Uses wait-for graph analysis to detect circular dependencies
- Implements graph-based cycle detection algorithms
- Demonstrates deadlock resolution through victim selection and transaction rollback

### Two-Phase Locking (2PL)
- Implements the growing and shrinking phases of 2PL
- Demonstrates lock acquisition protocol and concurrency control
- Benchmarks performance against MVCC for comparison

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request