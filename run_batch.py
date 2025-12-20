import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from mesa.batchrunner import batch_run
from model import KilobotFormationModel

# --- SCALABILITY CONFIGURATION ---

# No fixed size parameters, now they are variable.
fixed_params = {}

variable_params = {
    # SIZES TO TEST:
    # 10 -> 100 robots
    # 20 -> 400 robots
    # 30 -> 900 robots
    "side_length": [10, 20, 30], 

    # To check scalability, we test:
    "ir_error": [0.02],          
    "failure_prob": [0.0001],
    "lost_message_prob": [0.25], 
}


NUM_ITERATIONS = 25
MAX_STEPS = 1350

def run_experiment():
    print(f"Starting scalability test...")
    print(f"Testing sizes: {variable_params['side_length']}")

    params = {**fixed_params, **variable_params}

    results = batch_run(
        KilobotFormationModel,
        parameters=params,
        iterations=NUM_ITERATIONS,
        max_steps=MAX_STEPS,
        number_processes=None, 
        data_collection_period=-1, 
        display_progress=True
    )

    df = pd.DataFrame(results)
    
    # Calculate the total number of robots so the graph is clearer
    # (side_length 5 becomes "25 Robots")
    df['Total_Robots'] = df['side_length'] * df['side_length']
    
    return df

def analyze_scalability(df):
    
    # Summary statistics
    summary = df.groupby(['Total_Robots', 'ir_error', 'lost_message_prob', 'failure_prob'])[['Accuracy', 'Convergence_Time', 'Avg_Messages']].agg(['mean', 'std'])
    print("\n--- SCALABILITY SUMMARY ---")
    print(summary)
    summary.to_csv("results.csv")

    sns.set(style="whitegrid", font_scale=1.1)

    # --- CHART 1: ACCURACY ---
    g1 = sns.relplot(
        data=df,
        kind="line",
        x="Total_Robots",
        y="Accuracy",
        hue="ir_error",
        col="lost_message_prob",
        row="failure_prob",
        style="ir_error",
        markers=True,
        dashes=False,
        linewidth=2.5,
        palette="viridis",
        height=4,
        aspect=1.2
    )
    
    g1.fig.suptitle('Scalability: accuracy stability (Rows: failure prob)', y=1.02)
    g1.set_titles("Loss: {col_name} | Fail: {row_name}")
    g1.set_ylabels("Accuracy")
    g1.set_xlabels("Swarm size")
    
    for ax in g1.axes.flat:
        ax.set_ylim(-0.05, 1.05)
        
    plt.savefig("scalability_chart_accuracy.png")
    print("Clean accuracy chart saved")

    # --- CHART 2: TIME ---
    df_converged = df[df['Convergence_Time'] > 0]

    if not df_converged.empty:
        g2 = sns.relplot(
            data=df_converged,
            kind="line",
            x="Total_Robots",
            y="Convergence_Time",
            hue="ir_error",
            col="lost_message_prob",
            row="failure_prob",
            style="ir_error",
            markers=True,
            dashes=False,
            linewidth=2.5,
            palette="magma",
            height=4,
            aspect=1.2
        )
        g2.fig.suptitle('Scalability: convergence time (Rows: failure prob)', y=1.02)
        g2.set_titles("Loss: {col_name} | Fail: {row_name}")
        g2.set_ylabels("Steps")
        g2.set_xlabels("Swarm size")
        
        plt.savefig("scalability_chart_time.png")
        print("Clean time chart saved")

    # --- CHART 3: MESSAGES ---
    g3 = sns.catplot(
        data=df,
        kind="bar",
        x="Total_Robots",
        y="Avg_Messages",
        hue="ir_error",
        col="lost_message_prob",
        row="failure_prob",
        palette="Blues_d",
        height=4,
        aspect=1.2
    )
    g3.fig.suptitle('Scalability: communication efficiency (Rows: failure prob)', y=1.02)
    g3.set_titles("Loss: {col_name} | Fail: {row_name}")
    g3.set_ylabels("Avg msgs/robot")
    g3.set_xlabels("Swarm size")
    
    plt.savefig("scalability_chart_messages.png")
    print("Messages chart saved")
    
    plt.show()

if __name__ == "__main__":
    df_results = run_experiment()
    analyze_scalability(df_results)