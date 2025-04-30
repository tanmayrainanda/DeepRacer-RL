import math
def reward_function(params):
    
    # Constants
    MAX_REWARD = 1e2
    MIN_REWARD = 1e-3
    DIRECTION_THRESHOLD = 10.0
    ABS_STEERING_THRESHOLD = 30
    LOOK_AHEAD_WAYPOINTS = 3  # Number of waypoints to look ahead
    
    # Extract parameters
    all_wheels_on_track = params['all_wheels_on_track']
    x = params['x']
    y = params['y']
    distance_from_center = params['distance_from_center']
    is_left_of_center = params['is_left_of_center']
    heading = params['heading']
    progress = params['progress']
    steps = params['steps']
    speed = params['speed']
    steering_angle = params['steering_angle']
    track_width = params['track_width']
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    
    # Initialize reward with exponential distance penalty (borrowed from example)
    reward = math.exp(-6 * distance_from_center)
    
    # If off track, return minimum reward
    if not all_wheels_on_track:
        return MIN_REWARD
    
    # Get immediate track direction
    prev_point = waypoints[closest_waypoints[0]]
    next_point = waypoints[closest_waypoints[1]]
    track_direction = math.degrees(math.atan2(next_point[1] - prev_point[1], 
                                              next_point[0] - prev_point[0]))
    
    # Calculate the difference between track direction and car heading
    direction_diff = abs(track_direction - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    
    # Look ahead to determine if approaching a curve
    # This uses the concept from the second code snippet
    is_curve = False
    curve_direction = 0  # 0 = straight, 1 = right, -1 = left
    future_track_angles = []
    
    for i in range(1, LOOK_AHEAD_WAYPOINTS):
        if len(waypoints) > closest_waypoints[1] + i:
            future_point_idx = (closest_waypoints[1] + i) % len(waypoints)
            current_point_idx = (closest_waypoints[1] + i - 1) % len(waypoints)
            
            future_point = waypoints[future_point_idx]
            current_point = waypoints[current_point_idx]
            
            future_direction = math.degrees(math.atan2(future_point[1] - current_point[1],
                                                       future_point[0] - current_point[0]))
            
            angle_diff = future_direction - track_direction
            if angle_diff > 180:
                angle_diff -= 360
            elif angle_diff < -180:
                angle_diff += 360
                
            future_track_angles.append(angle_diff)
            
            # Check if this section is a curve
            if abs(angle_diff) > 15:
                is_curve = True
                curve_direction = 1 if angle_diff > 0 else -1
    
    # Calculate average curvature looking ahead
    avg_curvature = sum(abs(angle) for angle in future_track_angles) / len(future_track_angles) if future_track_angles else 0
    
    # Implement racing line optimization
    racing_line_reward = 1.0
    
    if is_curve:
       
        optimal_side = (curve_direction > 0 and is_left_of_center) or (curve_direction < 0 and not is_left_of_center)
        
        if optimal_side:
            # Inside line - good in curves
            # But don't get too close to the edge - sweet spot is around 60-70% away from center
            normalized_distance = distance_from_center / (track_width/2)
            if 0.6 <= normalized_distance <= 0.8:
                racing_line_reward = 1.5  # Perfect inside line
            elif normalized_distance < 0.6:
                racing_line_reward = 1.2  # Good but not optimal
            else:
                racing_line_reward = 0.8  # Too close to edge
        else:
            # Outside line - not ideal in curves
            racing_line_reward = 0.7
    else:
        # For straights, reward being in the center more
        normalized_distance = distance_from_center / (track_width/2)
        racing_line_reward = 1.0 - (normalized_distance * 0.3)
    
    # Speed reward - adjust target speed based on curvature
    max_speed = 4.0  # Assuming max speed is 4 m/s
    
    # Dynamic target speed based on curvature
    target_speed = max_speed
    if avg_curvature > 30:
        target_speed = 2.0  # Sharp curve
    elif avg_curvature > 15:
        target_speed = 3.0  # Moderate curve
    
    # Speed reward - higher reward for being close to the target speed
    speed_reward = 1.0 - (abs(speed - target_speed) / max_speed) * 0.5
    
    # Special reward for steering appropriate to the track segment
    steering_reward = 1.0
    abs_steering = abs(steering_angle)
    
    if is_curve:
        # In curves, reward steering that matches the curve intensity
        expected_steering = min(30, avg_curvature * 0.8)  # Scale curve angle to expected steering
        
        # Reward steering that's appropriate for the curve
        steering_diff = abs(abs_steering - expected_steering)
        if steering_diff < 5:
            steering_reward = 1.3  # Perfect steering for the curve
        elif steering_diff < 10:
            steering_reward = 1.1  # Good steering
        else:
            # Too much or too little steering for this curve
            steering_reward = 0.9
    else:
        # On straights, prefer minimal steering
        if abs_steering < 5:
            steering_reward = 1.2  # Excellent straight line steering
        else:
            steering_reward = 1.0 - (abs_steering / 30.0) * 0.5
    
    # Direction alignment reward
    direction_reward = 1.0
    if direction_diff > DIRECTION_THRESHOLD:
        direction_reward = 0.5
    
    # Progress reward - encourages completing the track in fewer steps
    progress_reward = (progress / steps) if steps > 0 else 0
    
    # Combine all rewards
    reward = reward * racing_line_reward * speed_reward * steering_reward * direction_reward * (1 + progress_reward)
    
    # Scale the reward
    reward = min(reward, MAX_REWARD)
    reward = max(reward, MIN_REWARD)
    
    return float(reward)
