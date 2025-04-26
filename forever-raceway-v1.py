def reward_function(params):
    """
    Reward function for the Forever Raceway track
    - Focuses on handling sharp 90-degree turns
    - Encourages speed on straightaways
    - Penalizes going off track or slow progress
    - Rewards staying close to racing line
    """
    
    # Read input parameters
    track_width = params['track_width']
    distance_from_center = params['distance_from_center']
    steering_angle = abs(params['steering_angle'])
    speed = params['speed']
    all_wheels_on_track = params['all_wheels_on_track']
    progress = params['progress']
    steps = params['steps']
    is_left_of_center = params['is_left_of_center']
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    heading = params['heading']
    
    # Initialize reward
    reward = 1.0
    
    # Target lap time is 7.9 seconds, assuming track length is about 30-35m
    # The estimated track length is derived from the record lap time and max speed
    TARGET_STEPS = 40  # Estimate based on 7.9s lap at 15 steps/second
    
    # Speed reward - We want maximum speed on straightaways, slower on turns
    # Calculate the direction of the centerline based on the closest waypoints
    prev_point = closest_waypoints[0]
    next_point = closest_waypoints[1]
    
    # Identify sharp turns vs straightaways based on waypoints
    # Get the coordinates of the next waypoint and the previous waypoint
    next_point_coords = waypoints[next_point]
    prev_point_coords = waypoints[prev_point]
    
    # Calculate the direction in radius, arctan2(dy, dx), converting to degrees
    import math
    track_direction = math.degrees(math.atan2(next_point_coords[1] - prev_point_coords[1], 
                                              next_point_coords[0] - prev_point_coords[0]))
    
    # Calculate the difference between the track direction and the heading direction of the car
    direction_diff = abs(track_direction - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    
    # Determine if we're approaching a turn or on a straightaway
    # For 90-degree turns in this track, we'll consider angles > 20 degrees as turns
    TURN_THRESHOLD = 20
    
    # Adjust speed based on track segment
    if direction_diff > TURN_THRESHOLD:
        # In a turn - reward slower speeds
        # Ideal speed for sharp turns: 1-2 m/s
        if 1.0 <= speed <= 2.0:
            reward += 1.0
        elif speed < 1.0:  # Too slow, minor penalty
            reward -= 0.5
        else:  # Too fast for turn
            reward -= (speed - 2.0) * 0.5
    else:
        # On a straightaway - reward higher speeds
        # Ideal speed: 3-4 m/s
        reward += speed / 4.0  # Proportional reward to speed
    
    # Penalize excessive steering on straightaways, but allow it in turns
    if direction_diff <= TURN_THRESHOLD and steering_angle > 15:
        reward -= 0.5
    
    # Center line reward
    # Calculate 3 markers that are farther and farther away from the center line
    marker_1 = 0.1 * track_width
    marker_2 = 0.25 * track_width
    marker_3 = 0.5 * track_width
    
    # Give higher reward if the car is closer to center line
    if distance_from_center <= marker_1:
        reward += 1.0
    elif distance_from_center <= marker_2:
        reward += 0.5
    elif distance_from_center <= marker_3:
        reward += 0.1
    else:
        reward += 0.0  # Likely off track
    
    # Off track penalty
    if not all_wheels_on_track:
        reward -= 2.0
    
    # Progress reward - encourage completing the track in fewer steps
    if progress == 100:  # Completed lap
        # Bonus for completing the track
        reward += 10.0
        
        # Additional bonus for completing in good time
        if steps < TARGET_STEPS:
            reward += 10.0 * (1.0 - (steps / TARGET_STEPS))
    
    # Prevent zero or negative reward
    reward = max(0.01, reward)
    
    return float(reward)