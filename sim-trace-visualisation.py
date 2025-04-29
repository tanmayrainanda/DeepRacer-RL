import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm

def load_sim_trace_csv(file_path):
    """Load simulation trace data from CSV file"""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return None

def extract_sim_trace_data_from_csv(df):
    """Extract relevant data from the simulation trace DataFrame"""
    required_columns = ['X', 'Y', 'steer', 'throttle', 'reward', 'tstamp']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Warning: Missing columns in CSV: {missing_columns}")
    
    data = {
        'x': df['X'].tolist() if 'X' in df.columns else [],
        'y': df['Y'].tolist() if 'Y' in df.columns else [],
        'steering': df['steer'].tolist() if 'steer' in df.columns else [],
        'throttle': df['throttle'].tolist() if 'throttle' in df.columns else [],
        'reward': df['reward'].tolist() if 'reward' in df.columns else [],
        'timestamp': df['tstamp'].tolist() if 'tstamp' in df.columns else [],
        'progress': df['progress'].tolist() if 'progress' in df.columns else [],
        'all_wheels_on_track': df['all_wheels_on_track'].tolist() if 'all_wheels_on_track' in df.columns else [],
        'closest_waypoint': df['closest_waypoint'].tolist() if 'closest_waypoint' in df.columns else []
    }
    
    if 'throttle' in df.columns:
        data['speed'] = df['throttle'].tolist()
    else:
        data['speed'] = [0] * len(data['x'])
        
    return data

def extract_waypoints_data(waypoints_data):
    """Extract track waypoints"""
    if isinstance(waypoints_data, dict) and 'waypoints' in waypoints_data:
        waypoints = waypoints_data['waypoints']
    elif isinstance(waypoints_data, list):
        waypoints = waypoints_data
    else:
        print("Waypoints data format not recognized")
        return None
    
    # Extract the coordinates
    waypoint_x = [wp[0] for wp in waypoints]
    waypoint_y = [wp[1] for wp in waypoints]
    
    # If waypoints have width information
    waypoint_left_x = []
    waypoint_left_y = []
    waypoint_right_x = []
    waypoint_right_y = []
    
    if len(waypoints[0]) > 2:  # Check if additional track width info exists
        for wp in waypoints:
            if len(wp) >= 4:  # [x, y, left_x, left_y, right_x, right_y]
                waypoint_left_x.append(wp[2])
                waypoint_left_y.append(wp[3])
                if len(wp) >= 6:
                    waypoint_right_x.append(wp[4])
                    waypoint_right_y.append(wp[5])
    
    return {
        'center_x': waypoint_x,
        'center_y': waypoint_y,
        'left_x': waypoint_left_x,
        'left_y': waypoint_left_y,
        'right_x': waypoint_right_x,
        'right_y': waypoint_right_y
    }

def visualize_deepracer_sim_csv(csv_file_path, color_metric='speed', 
                            save_path=None, show_plot=True, figsize=(12, 10)):
    """
    Visualize DeepRacer simulation trace from CSV file
    
    Parameters:
    - csv_file_path: Path to the simulation trace CSV file
    - color_metric: Metric to use for coloring the trace ('speed', 'reward', 'steering', 'progress')
    - save_path: Path to save the visualization (None = don't save)
    - show_plot: Whether to display the plot
    - figsize: Figure size as tuple (width, height)
    """
    df = load_sim_trace_csv(csv_file_path)
    if df is None:
        print("Failed to load simulation trace data")
        return
    
    trace_data = extract_sim_trace_data_from_csv(df)
    
    plt.figure(figsize=figsize)
    
    points = np.array([trace_data['x'], trace_data['y']]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    if color_metric == 'speed' or color_metric == 'throttle':
        values = trace_data['speed'][:-1]
        cmap = plt.cm.plasma
        norm = plt.Normalize(min(trace_data['speed']), max(trace_data['speed']))
        colorbar_label = 'Throttle'
    elif color_metric == 'reward':
        values = trace_data['reward'][:-1]
        cmap = plt.cm.viridis
        norm = plt.Normalize(min(trace_data['reward']), max(trace_data['reward']))
        colorbar_label = 'Reward'
    elif color_metric == 'steering':
        values = trace_data['steering'][:-1]
        cmap = plt.cm.coolwarm
        norm = plt.Normalize(min(trace_data['steering']), max(trace_data['steering']))
        colorbar_label = 'Steering Angle'
    elif color_metric == 'progress':
        values = trace_data['progress'][:-1]
        cmap = plt.cm.autumn
        norm = plt.Normalize(min(trace_data['progress']), max(trace_data['progress']))
        colorbar_label = 'Progress (%)'
    else:
        values = trace_data['speed'][:-1]
        cmap = plt.cm.plasma
        norm = plt.Normalize(min(trace_data['speed']), max(trace_data['speed']))
        colorbar_label = 'Throttle'
    
    lc = LineCollection(segments, cmap=cmap, norm=norm)
    lc.set_array(np.array(values))
    lc.set_linewidth(3)
    line = plt.gca().add_collection(lc)
    
    cbar = plt.colorbar(line, ax=plt.gca())
    cbar.set_label(colorbar_label)
    
    # Mark start and finish
    if len(trace_data['x']) > 0:
        plt.plot(trace_data['x'][0], trace_data['y'][0], 'go', markersize=10, label='Start')
        plt.plot(trace_data['x'][-1], trace_data['y'][-1], 'ro', markersize=10, label='Finish')
    
    plt.title('DeepRacer Simulation Trace', fontsize=16)
    plt.xlabel('X Position (m)', fontsize=12)
    plt.ylabel('Y Position (m)', fontsize=12)
    plt.axis('equal')  # Equal aspect ratio
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper right')
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    if show_plot:
        plt.show()
    else:
        plt.close()

def create_metrics_plots_from_csv(csv_file_path, save_path=None, show_plot=True, figsize=(15, 10)):
    """Create additional plots showing throttle, reward, and steering over time from CSV data"""
    # Load CSV data
    df = load_sim_trace_csv(csv_file_path)
    if df is None:
        print("Failed to load simulation trace data")
        return
    
    trace_data = extract_sim_trace_data_from_csv(df)
    
    fig, axs = plt.subplots(4, 1, figsize=figsize, sharex=True)
    
    # Time values - convert to seconds or use steps as proxy
    if trace_data['timestamp'] and len(trace_data['timestamp']) > 0:
        # Convert timestamps to seconds from start
        start_time = trace_data['timestamp'][0]
        time_values = [(t - start_time) / 1000 for t in trace_data['timestamp']]  # Assuming ms
    else:
        time_values = list(range(len(trace_data['steering'])))
    
    # Plot throttle (proxy for speed)
    axs[0].plot(time_values, trace_data['speed'], 'b-', linewidth=2)
    axs[0].set_ylabel('Throttle')
    axs[0].set_title('Throttle over Time')
    axs[0].grid(True)
    
    # Plot reward
    axs[1].plot(time_values, trace_data['reward'], 'g-', linewidth=2)
    axs[1].set_ylabel('Reward')
    axs[1].set_title('Reward over Time')
    axs[1].grid(True)
    
    # Plot steering angle
    axs[2].plot(time_values, trace_data['steering'], 'r-', linewidth=2)
    axs[2].set_ylabel('Steering Angle')
    axs[2].set_title('Steering Angle over Time')
    axs[2].grid(True)
    
    # Plot progress if available
    if trace_data['progress'] and len(trace_data['progress']) > 0:
        axs[3].plot(time_values, trace_data['progress'], 'purple', linewidth=2)
        axs[3].set_ylabel('Progress (%)')
        axs[3].set_title('Progress over Time')
        axs[3].set_xlabel('Time (seconds)')
        axs[3].grid(True)
    else:

        fig.delaxes(axs[3])
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    if show_plot:
        plt.show()
    else:
        plt.close()

if __name__ == "__main__":
    sim_trace_csv_file = "Catalunya-General.csv"
    
    # Visualize the simulation trace
    visualize_deepracer_sim_csv(sim_trace_csv_file, color_metric='throttle', 
                              save_path="deepracer_visualization.png")
    
    create_metrics_plots_from_csv(sim_trace_csv_file, save_path="deepracer_metrics.png")
    
    visualize_deepracer_sim_csv(sim_trace_csv_file, color_metric='reward', save_path="deepracer_visualization_reward.png")
    visualize_deepracer_sim_csv(sim_trace_csv_file, color_metric='steering', save_path="deepracer_visualization_steering.png")
    visualize_deepracer_sim_csv(sim_trace_csv_file, color_metric='progress', save_path="deepracer_visualization_progress.png")