import math

def reward_function(params):
    """
    Simplified reward function that encourages:
    1. Staying on track
    2. Following the center line
    3. Maintaining a moderate speed around 2 m/s
    4. Keeping steering smooth
    """
    
    # Extract parameters
    all_wheels_on_track = params['all_wheels_on_track']
    distance_from_center = params['distance_from_center']
    track_width = params['track_width']
    speed = params['speed']
    steering_angle = params['steering_angle']
    
    # Initialize reward
    reward = 1.0
    

    max_distance = track_width / 2
    
    # Check if car is completely off track
    if distance_from_center >= max_distance:
        return 1e-3  # Return minimum reward if completely off track
    

    center_factor = 1 - (distance_from_center / max_distance) ** 0.5
    reward *= center_factor
    

    speed_reward = 1 - ((speed - 2.0) ** 2) / 4  # Normalize by 4 (max possible deviation)
    speed_reward = max(0.1, speed_reward)  # Ensure minimum speed reward isn't too punishing
    reward *= speed_reward
    

    abs_steering = abs(steering_angle)
    steering_reward = 1 - (abs_steering / 30) ** 0.5
    reward *= steering_reward
    
    return float(reward)
