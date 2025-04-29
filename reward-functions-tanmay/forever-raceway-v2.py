import math
def reward_function(params):
    """
    Advanced reward function for the Forever Raceway track
    - Maximizes speed on straightaways (full 4m/s)
    - Encourages controlled sliding around corners
    - Allows strategic corner cutting (at least 2 wheels on track)
    - Optimized for the 7.9s record lap time
    """
    
    # Read input parameters
    track_width = params['track_width']
    distance_from_center = params['distance_from_center']
    steering_angle = abs(params['steering_angle'])
    speed = params['speed']
    all_wheels_on_track = params['all_wheels_on_track']
    wheels_on_track = params.get('wheels_on_track', 4)  # Default to 4 if not available
    is_offtrack = params['is_offtrack']
    progress = params['progress']
    steps = params['steps']
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    heading = params['heading']
    is_left_of_center = params['is_left_of_center']
    
    # Target lap time is 7.9 seconds
    # At 15 steps/second, this is approximately 119 steps
    TARGET_STEPS = 119
    
    # Initialize reward
    reward = 1.0
    
    # Calculate the direction of the centerline based on the closest waypoints
    prev_point = closest_waypoints[0]
    next_point = closest_waypoints[1]
    
    # Get the coordinates of the next waypoint and the previous waypoint
    next_point_coords = waypoints[next_point]
    prev_point_coords = waypoints[prev_point]
    
    # Calculate the direction in radius, arctan2(dy, dx), converting to degrees
    track_direction = math.degrees(math.atan2(next_point_coords[1] - prev_point_coords[1], 
                                              next_point_coords[0] - prev_point_coords[0]))
    
    # Calculate the difference between the track direction and the heading direction of the car
    direction_diff = abs(track_direction - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    
    # Look ahead to future waypoints to anticipate upcoming turns
    look_ahead_waypoint = (next_point + 3) % len(waypoints)
    future_point_coords = waypoints[look_ahead_waypoint]
    
    # Calculate direction change between current segment and upcoming segment
    upcoming_direction = math.degrees(math.atan2(future_point_coords[1] - next_point_coords[1],
                                               future_point_coords[0] - next_point_coords[0]))
    upcoming_turn_angle = abs(upcoming_direction - track_direction)
    if upcoming_turn_angle > 180:
        upcoming_turn_angle = 360 - upcoming_turn_angle
    
    # Determine if we're approaching a turn or on a straightaway
    # For sharp turns, use lower threshold to detect them further in advance
    TURN_THRESHOLD = 15
    SHARP_TURN_THRESHOLD = 60  # For 90-degree turns
    
    # Flag to track if we're in a turn
    is_in_turn = direction_diff > TURN_THRESHOLD or upcoming_turn_angle > TURN_THRESHOLD
    is_in_sharp_turn = direction_diff > SHARP_TURN_THRESHOLD
    
    # Speed reward - Maximum speed on straights, controlled in turns
    if is_in_sharp_turn:
        # In a sharp 90-degree turn - slight slide is good (2.0-3.0 m/s)
        if 2.0 <= speed <= 3.0:
            reward += 2.0  # Significant reward for ideal cornering speed
        elif speed < 2.0:  # Too slow
            reward -= 1.0
        else:  # Too fast for sharp turn, but not heavily penalized
            reward -= 0.5
    elif is_in_turn:
        # In a moderate turn - reward higher speeds (2.5-3.5 m/s)
        if 2.5 <= speed <= 3.5:
            reward += 1.5
        elif speed < 2.5:  # Too slow
            reward -= 0.5
        else:  # Slightly too fast
            reward -= 0.2
    else:
        # On a straightaway - reward maximum speed (3.5-4.0 m/s)
        if speed >= 3.8:
            reward += 3.0  # Strong incentive to go all out on straights
        elif speed >= 3.5:
            reward += 2.0
        else:
            reward += speed / 2.0  # Proportional but smaller reward
    
    # Steering reward - Allow aggressive steering in turns, smooth on straights
    if is_in_turn:
        # In a turn, reward more aggressive steering
        if steering_angle > 15 and steering_angle <= 30:
            reward += 1.0  # Perfect steering for turn
        elif steering_angle > 30:
            reward += 0.5  # More aggressive than needed but still good
    else:
        # On straightaway, reward minimal steering
        if steering_angle < 5:
            reward += 1.0
        elif steering_angle < 10:
            reward += 0.5
        elif steering_angle > 15:
            reward -= 0.5  # Penalize excessive steering on straights
    
    # Corner cutting reward - Allow strategic corner cutting
    if all_wheels_on_track:
        reward += 0.5
    elif not is_offtrack and wheels_on_track >= 2:
        # Strategic corner cutting (2-3 wheels on track)
        if is_in_turn:
            reward += 1.0  # Reward cutting corners in turns
        else:
            reward += 0.2  # Smaller reward for cutting on straights
    else:
        # Fully off track
        reward -= 3.0
    
    # Racing line reward - different for inside vs outside of turns
    marker_1 = 0.1 * track_width
    marker_2 = 0.25 * track_width
    marker_3 = 0.4 * track_width
    
    if is_in_turn:
        # In turns, reward being closer to inside line
        # Determine optimal side based on turn direction
        next_next_point = (next_point + 1) % len(waypoints)
        next_next_coords = waypoints[next_next_point]
        
        # Simple turn direction detection
        # Calculate cross product to determine if turn is left or right
        v1x = next_point_coords[0] - prev_point_coords[0]
        v1y = next_point_coords[1] - prev_point_coords[1]
        v2x = next_next_coords[0] - next_point_coords[0]
        v2y = next_next_coords[1] - next_point_coords[1]
        
        cross_product = v1x * v2y - v1y * v2x
        
        # If cross product is positive, we're turning left; if negative, turning right
        optimal_side_is_left = cross_product > 0
        
        # Reward being on the inside of the turn
        if (optimal_side_is_left and is_left_of_center) or (not optimal_side_is_left and not is_left_of_center):
            # On optimal side for turn
            if distance_from_center <= marker_3:
                reward += 1.5  # Strong reward for inside line
            else:
                reward += 0.5  # Still on inside but far from center
        else:
            # On outside of turn
            reward -= 0.5  # Small penalty for outside line
    else:
        # On straights, reward being close to center
        if distance_from_center <= marker_1:
            reward += 1.0
        elif distance_from_center <= marker_2:
            reward += 0.5
        elif distance_from_center <= marker_3:
            reward += 0.1
    
    # Progress reward - encourage completing the track in fewer steps
    reward += progress / 100.0  # Basic reward for progress
    
    if progress == 100:  # Completed lap
        # Bonus for completing the track
        reward += 10.0
        
        # Additional bonus for completing in good time
        if steps <= TARGET_STEPS:
            reward += 50.0 * (1.0 - (steps / TARGET_STEPS))  # Much larger bonus for fast completion
        else:
            # Still reward completion but with diminishing returns for slower times
            reward += 10.0 * (TARGET_STEPS / steps)
    
    # Prevent zero or negative reward
    reward = max(0.01, reward)
    
    return float(reward)