import math

def reward_function(params):
    """
    Generalizable reward function for AWS DeepRacer
    Using lookahead waypoints to optimize racing line across any track
    """
    # Track parameters
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    heading = params['heading']
    track_width = params['track_width']
    distance_from_center = params['distance_from_center']
    all_wheels_on_track = params['all_wheels_on_track']
    speed = params['speed']
    steering_angle = abs(params['steering_angle'])
    progress = params['progress']
    steps = params['steps']
    is_offtrack = params.get('is_offtrack', not all_wheels_on_track)
    
    # Constants
    MAX_SPEED = 8.0  # Maximum speed in m/s
    MIN_SPEED = 1.5  # Minimum speed in m/s
    LOOKAHEAD_POINTS = 8  # Number of waypoints to look ahead
    
    # Base reward
    reward = 1.0
    
    # Priority 1: Stay on track - essential for any track
    if not all_wheels_on_track or is_offtrack:
        return 0.001
    
    # Get current and next waypoints
    prev_point = closest_waypoints[0]
    next_point = closest_waypoints[1]
    
    # Calculate immediate and future track directions
    track_direction = get_track_direction(waypoints, prev_point, next_point)
    
    # Calculate heading difference
    # Normalize to between 0 and 180 degrees
    heading_diff = abs(track_direction - heading)
    if heading_diff > 180:
        heading_diff = 360 - heading_diff
    
    # Get upcoming waypoints for lookahead analysis
    lookahead_points = []
    for i in range(LOOKAHEAD_POINTS):
        point_idx = (next_point + i) % len(waypoints)
        lookahead_points.append(waypoints[point_idx])
    
    # Calculate track curvature based on waypoints
    curvature = calculate_curvature(waypoints, prev_point, lookahead_points)
    
    # Determine optimal speed based on track curvature
    optimal_speed = get_optimal_speed(curvature, MAX_SPEED, MIN_SPEED)
    
    # Calculate optimal racing line
    optimal_distance = calculate_racing_line(waypoints, closest_waypoints, track_width, curvature)
    
    # Calculate racing line reward
    racing_line_reward = calculate_racing_line_reward(distance_from_center, optimal_distance, track_width)
    
    # Speed reward based on track curvature
    if speed <= optimal_speed:
        # Reward for getting close to optimal speed
        speed_reward = speed / optimal_speed
    else:
        # Penalty for exceeding optimal speed by too much on curves
        over_speed_factor = (speed - optimal_speed) / optimal_speed
        speed_reward = 1.0 - (over_speed_factor * curvature * 0.5)
        speed_reward = max(0.3, speed_reward)  # Ensure minimum reward
    
    # Direction reward based on heading alignment with track
    direction_reward = 1.0 - (heading_diff / 90.0)
    direction_reward = max(0.1, direction_reward)  # Ensure minimum reward
    
    # Steering smoothness based on curvature
    steering_factor = calculate_steering_factor(steering_angle, curvature)
    
    # Combine rewards with appropriate weights
    reward = 1.0
    reward += racing_line_reward * 2.0
    reward += speed_reward * 2.0
    reward += direction_reward * 1.5
    reward *= steering_factor
    
    # Progress reward - faster completion
    if steps > 0:
        progress_reward = progress / steps
        reward += (progress_reward * 100)
    
    # Significant completion bonus
    if progress >= 100:
        reward += 30.0
    
    return float(max(0.001, reward))

def get_track_direction(waypoints, prev_point_idx, next_point_idx):
    """
    Calculate the direction of the track (in degrees) between two waypoints
    """
    
    
    # Get the coordinates of the next waypoint
    next_point = waypoints[next_point_idx]
    prev_point = waypoints[prev_point_idx]
    
    # Calculate the direction in radians
    track_direction = math.atan2(next_point[1] - prev_point[1], next_point[0] - prev_point[0])
    
    # Convert to degrees
    track_direction = math.degrees(track_direction)
    
    # Normalize the degrees to 0-360
    if track_direction < 0:
        track_direction += 360
    
    return track_direction

def calculate_curvature(waypoints, current_point_idx, lookahead_points):
    """
    Calculate the curvature of the track ahead
    Higher values indicate sharper turns
    """
    
    
    # If we don't have enough waypoints, return a default value
    if len(lookahead_points) < 3:
        return 0.0
    
    # Calculate the angles between consecutive waypoints
    angles = []
    prev_angle = None
    
    for i in range(len(lookahead_points) - 1):
        # Get two consecutive waypoints
        p1 = lookahead_points[i]
        p2 = lookahead_points[i + 1]
        
        # Calculate the angle between them
        angle = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        
        # Convert to degrees
        angle = math.degrees(angle)
        
        # Normalize
        if angle < 0:
            angle += 360
        
        # Store angle
        if prev_angle is not None:
            # Calculate the delta angle
            delta_angle = abs(angle - prev_angle)
            if delta_angle > 180:
                delta_angle = 360 - delta_angle
            angles.append(delta_angle)
        
        prev_angle = angle
    
    # Calculate the average of the absolute changes in angle
    if len(angles) > 0:
        avg_angle_change = sum(angles) / len(angles)
        # Normalize to a value between 0 and 1
        curvature = min(1.0, avg_angle_change / 30.0)
    else:
        curvature = 0.0
    
    return curvature

def get_optimal_speed(curvature, max_speed, min_speed):
    """
    Calculate optimal speed based on track curvature
    Higher curvature (sharper turns) = lower speed
    """
    # Linear relationship between curvature and speed
    # curvature = 0 (straight) -> max_speed
    # curvature = 1 (very sharp turn) -> min_speed
    optimal_speed = max_speed - curvature * (max_speed - min_speed)
    return optimal_speed

def calculate_racing_line(waypoints, closest_waypoints, track_width, curvature):
    """
    Calculate the optimal distance from center based on upcoming track
    For straight sections: center of track
    For curves: inside of the turn
    """
    
    # Default to center of track
    optimal_distance = 0.0
    
    # Get next and previous waypoints
    prev_idx = closest_waypoints[0]
    next_idx = closest_waypoints[1]
    
    # Get the coordinates
    prev_point = waypoints[prev_idx]
    next_point = waypoints[next_idx]
    
    # For straight sections, stay in center
    if curvature < 0.2:  # Low curvature indicates straight section
        return 0.0
    
    # For curves, we need to determine if it's a left or right turn
    # Look ahead two waypoints to determine turn direction
    lookahead_idx = (next_idx + 1) % len(waypoints)
    lookahead_point = waypoints[lookahead_idx]
    
    # Calculate vectors
    v1 = (next_point[0] - prev_point[0], next_point[1] - prev_point[1])
    v2 = (lookahead_point[0] - next_point[0], lookahead_point[1] - next_point[1])
    
    # Calculate cross product to determine turn direction
    cross_product = v1[0] * v2[1] - v1[1] * v2[0]
    
    # Positive cross product means left turn, negative means right turn
    if cross_product > 0:  # Left turn
        # For left turns, optimal line is on the right side (positive distance)
        optimal_distance = track_width * 0.4 * curvature
    else:  # Right turn
        # For right turns, optimal line is on the left side (negative distance)
        optimal_distance = -track_width * 0.4 * curvature
    
    return optimal_distance

def calculate_racing_line_reward(distance_from_center, optimal_distance, track_width):
    """
    Calculate reward based on how close the car is to the optimal racing line
    """
    # Calculate the target distance from center
    target_distance = optimal_distance
    
    # Calculate how far the car is from the optimal racing line
    distance_from_racing_line = abs(distance_from_center - target_distance)
    
    # Normalize distance
    normalized_distance = distance_from_racing_line / (track_width / 2.0)
    
    # Calculate reward (higher when closer to racing line)
    if normalized_distance <= 0.1:
        racing_line_reward = 1.0
    elif normalized_distance <= 0.25:
        racing_line_reward = 0.8
    elif normalized_distance <= 0.5:
        racing_line_reward = 0.5
    elif normalized_distance <= 0.75:
        racing_line_reward = 0.3
    else:
        racing_line_reward = 0.1
    
    return racing_line_reward

def calculate_steering_factor(steering_angle, curvature):
    """
    Calculate steering factor based on track curvature
    Allow more steering on curves, less on straights
    """
    # Adjust expected steering based on curvature
    expected_steering = curvature * 25.0  # Scale curvature to reasonable steering angles
    
    # Calculate the steering factor
    if steering_angle <= expected_steering:
        # Good steering
        steering_factor = 1.0
    else:
        # Penalize excessive steering
        steering_excess = (steering_angle - expected_steering) / 30.0
        steering_factor = max(0.7, 1.0 - steering_excess)
    
    return steering_factor