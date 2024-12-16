Project Structure
The codebase is organized into different modules, each focusing on a specific aspect of the reliability evaluation process. Below is an overview of the project structure and its components:

1. Data Preparation
Purpose: Load and preprocess the input data for the system, including information about buses, lines, generators, and loads.
Files:
data_processing.py: Handles data import from CSV files and prepares it for simulation.
DADOS/: Contains input files such as:
D_GEN.csv: Generator characteristics (capacity, failure rates, repair times).
D_LIN.csv: Transmission line data (capacity, failure rates, reactivity, etc.).
D_LOAD.csv: Load data (location, magnitude).

2. Sequential Monte Carlo Simulation (SMC)
Purpose: Simulate the system operation over time using random sampling to account for the stochastic behavior of components. Includes the chronological order of events to assess reliability indices.
Key Features:
Time-dependent failure and repair modeling.
Assessment of energy supply under different operational scenarios.
Files:
monte_carlo_Seq.py: Implements the SMC methodology, simulating failures, repairs, and demand fulfillment over time.

3. Non-Sequential Monte Carlo Simulation (SMC NC)
Purpose: Evaluate reliability without chronological modeling, focusing on probabilistic combinations of component states (up/down).
Key Features:
Simplifies computation by removing time-dependency.
Useful for quick reliability estimates.
Files:
monte_carlo_NS.py: Implements the SMC NC methodology using random sampling of states.

4. State Enumeration Method
Purpose: Enumerate all possible system states (combinations of operational and failed components) to calculate exact reliability indices.
Key Features:
Computationally exhaustive but highly accurate for small systems.
Serves as a benchmark for comparing the Monte Carlo results.
Files:
states_enumeration.py: Implements state enumeration to calculate reliability indices.

5. Utility Functions
Purpose: Shared utilities used across different methodologies.
Files:
calcula_fpo.py: Models optimal power flow equations and constraints using pyomo

6. How to Run the Project
Prerequisites
Install Python 3.8+.
Install dependencies from the requirements.txt file:
pip install -r requirements.txt
'GLPK' solver instalation: video reference https://www.youtube.com/watch?v=GaSEZ0kzOkA




