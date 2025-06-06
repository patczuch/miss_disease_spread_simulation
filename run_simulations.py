import subprocess
import itertools
import sys

# Define parameter options
mortality_rates = [0.1, 0.5, 0.7]
death_times = [100, 300]
susceptible_again_times = [300, 500]
n_susceptibles = [30, 50]
n_infecteds = [5, 20]
recovered_enableds = [True, False]
exposed_enableds = [True, False]
incubation_times = [100, 300]
quarantine_percentages = [0, 0.001, 0.01]

# Get the current Python interpreter path (from the same venv)
python_executable = sys.executable

# Generate all combinations
combinations = list(itertools.product(
    recovered_enableds,
    exposed_enableds,
    mortality_rates,
    death_times,
    susceptible_again_times,
    n_susceptibles,
    n_infecteds,
    quarantine_percentages
))

# Run main.py with valid parameter combinations
for combo in combinations:
    (
        recovered_enabled,
        exposed_enabled,
        mortality_rate,
        death_time,
        susceptible_again_time,
        n_susceptible,
        n_infected,
        quarantine_percentage
    ) = combo

    # Skip invalid combination
    if exposed_enabled and not recovered_enabled:
        continue

    # Use only one incubation_time per run if exposed is enabled
    incubation_times_to_test = incubation_times if exposed_enabled else [None]

    for incubation_time in incubation_times_to_test:
        cmd = [
            python_executable, "main.py",
            "--mortality_rate", str(mortality_rate),
            "--death_time", str(death_time),
            "--susceptible_again_time", str(susceptible_again_time),
            "--n_susceptible", str(n_susceptible),
            "--n_infected", str(n_infected),
            "--recovered_enabled", str(recovered_enabled),
            "--exposed_enabled", str(exposed_enabled),
            "--quarantine_percentage", str(quarantine_percentage)
        ]

        if incubation_time is not None:
            cmd += ["--incubation_time", str(incubation_time)]

        print("Running:", " ".join(cmd))
        subprocess.run(cmd)