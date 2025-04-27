#sharpturnschange 37.997
#2022reinventeval 37.678

import math

def reward_function(params):
    # Read input parameters
    track_width = params['track_width']
    distance_from_center = params['distance_from_center']
    speed = params['speed']
    steering_angle = params['steering_angle']
    all_wheels_on_track = params['all_wheels_on_track']
    progress = params['progress']
    steps = params['steps']
    heading = params['heading']
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    is_left_of_center = params['is_left_of_center']
    
    # Initialize reward
    reward = 1.0
    
    # 1. Base reward for staying on track
    if not all_wheels_on_track:
        return 1e-4
    
    # 2. Racing line optimization
    # For counterclockwise racing, we want to be on the inside of the turns
    # We'll use the waypoints to identify turns
    prev_point = closest_waypoints[0]
    next_point = closest_waypoints[1]
    
    # Calculate the direction of the track (angle between waypoints)
    track_direction = math.degrees(math.atan2(waypoints[next_point][1] - waypoints[prev_point][1], 
                                             waypoints[next_point][0] - waypoints[prev_point][0]))
    
    # Calculate the difference between the track direction and car heading
    direction_diff = abs(track_direction - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    
    # Determine if we're in a turn based on the change in track direction
    TURN_THRESHOLD = 12  # increased for better turns
    is_turning = direction_diff > TURN_THRESHOLD
    
    # looking several steps ahead to detect sharp turns
    LOOKAHEAD = 5
    is_sharp_turn = False
    
    # check upcoming waypoints for sharp direction changes
    if next_point + LOOKAHEAD < len(waypoints):
        future_point = (next_point + LOOKAHEAD) % len(waypoints)
        future_direction = math.degrees(math.atan2(waypoints[future_point][1] - waypoints[next_point][1], 
                                             waypoints[future_point][0] - waypoints[next_point][0]))
        future_diff = abs(future_direction - track_direction)
        if future_diff > 180:
            future_diff = 360 - future_diff
        is_sharp_turn = future_diff > 20 # threshold to detect sharp turns
        
    # Adjust reward based on racing line
    if is_turning:
        # In turns, reward being on the inside line
        # For counterclockwise, reward being on right side of centerline
        optimal_distance = 0.25 * track_width
        # detecting sharp turn (move closer to inside line if detected)
        if is_sharp_turn:
            optimal_distance = 0.20 * track_width  # Not completely at edge
        if not is_left_of_center:  # Right side of track
            # Reward being close to the optimal distance from center
            reward += (1.0 - abs(distance_from_center - optimal_distance) / optimal_distance) * 0.5
    else:
        # On straightaways, reward being in center
        reward += (1.0 - distance_from_center / (track_width/2)) * 0.3
        
    
    MAX_SPEED = 4.0
    # speed optimisation
    if is_sharp_turn:
        # More conservative speed for sharp turns
        IDEAL_SHARP_TURN_SPEED = 1.5  # Slower for sharp turns
        speed_factor = (1.0 - abs(speed - IDEAL_SHARP_TURN_SPEED) / IDEAL_SHARP_TURN_SPEED)
        reward += speed_factor * 0.7
        # Extra penalty for excessive speed in sharp turns
        if speed > IDEAL_SHARP_TURN_SPEED * 1.5:
            reward *= 0.7
    elif is_turning:
        # Normal turns - slightly faster
        IDEAL_TURN_SPEED = 2.5  # Increased from 2.0 for normal turns
        reward += (1.0 - abs(speed - IDEAL_TURN_SPEED) / IDEAL_TURN_SPEED) * 0.5
    else:
        # Reward for high speed on straights - INCREASED REWARD
        straight_speed_factor = (speed / MAX_SPEED)
        reward += straight_speed_factor * 1.2  # Increased reward for high speeds on straights
    
    # maybe inc speed of turns even in sharp?
    ABS_STEERING_THRESHOLD = 15
    if is_sharp_turn:
        # Allow more steering in sharp turns without penalty
        if abs(steering_angle) > 25:  # Higher threshold for sharp turns
            reward *= 0.8
    elif abs(steering_angle) > ABS_STEERING_THRESHOLD:
        reward *= 0.8
    
    # 5. Reward for progress
    reward += progress / 100.0
    
    # 6. Reward for efficiency (completing the track in fewer steps)
    reward += (progress / steps) * 5
    
    return float(reward)