import os
import glob
import matplotlib.pyplot as plt
import pandas as pd


def read_parameters(filepath):
    params = {}
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                key, value = line.strip().split(maxsplit=1)
                try:
                    value = eval(value)
                except:
                    pass
                params[key] = value
    return params


def plot_simulation(stats_file, params_file, output_dir="plots"):
    params = read_parameters(params_file)
    df = pd.read_csv(stats_file)

    plt.figure(figsize=(18, 10))
    plt.plot(df['frame'], df['infected'], color='red', label='Infected')
    plt.plot(df['frame'], df['susceptible'], color='green', label='Susceptible')
    if params["exposed_enabled"]:
        plt.plot(df['frame'], df['exposed'], color='yellow', label='Exposed')
    if params["recovered_enabled"]:
        plt.plot(df['frame'], df['recovered'], color='blue', label='Recovered')
    plt.plot(df['frame'], df['total_deaths'], color='black', linestyle='--', label='Total Deaths')

    plt.xlabel('Day')
    plt.ylabel('People')

    sim_type = "SIS"
    if params["recovered_enabled"] and params["exposed_enabled"]:
        sim_type = "SEIR"
    elif params["recovered_enabled"]:
        sim_type = "SIRS"
    else:
        print("Invalid simulation parameters exposed / recovered")
        exit(0)

    recovered_info = f"recovered={params['n_recovered']}, \n" if params.get('recovered_enabled', True) else "\n"

    plt.title(f"{sim_type} \n"
              f"susceptible={params['n_susceptible']}, " +
              f"infected={params['n_infected']}, " +
              recovered_info +
              f"mortality_rate={params['mortality_rate']}, " +
              f"death_time={params['death_time']}, " +
              f"susceptible_again_time={params['susceptible_again_time']}, \n" +
              f"incubation_time={params['incubation_time']}, " +
              f"quarantine={params['quarantine_percentage']}%"
              )
    plt.legend()
    plt.grid(True)

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "plot-" + os.path.splitext(os.path.basename(params_file))[0].split("-", 1)[1] + ".png")
    plt.savefig(output_path)
    plt.close()
    print(f"Plot saved: {output_path}")


def main():
    parameter_files = glob.glob("simulation_parameters-*.txt")
    stat_files = glob.glob("simulation_stats-*.csv")

    for param_file in parameter_files:
        suffix = param_file.split("simulation_parameters-")[1].split(".txt")[0]
        stat_file = f"simulation_stats-{suffix}.csv"
        if stat_file in stat_files:
            plot_simulation(stat_file, param_file)
        else:
            print(f"No matching stats file for {param_file}")


if __name__ == "__main__":
    main()
