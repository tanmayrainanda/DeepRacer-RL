#lookahead and turn sensitivity 1 min 19 secs 
#best one so far but slow

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
    
    TURN_THRESHOLD = 10  # increased for better turns
    # looking several steps ahead to detect sharp turns (at multiple points)
    LOOKAHEAD_RANGE = [3, 6, 9] 
    
    # initializing turn variables
    is_turning = direction_diff > TURN_THRESHOLD
    approaching_turn = False
    is_sharp_turn = False
    turn_severity = 0
    
    #looking ahead at diff points
    for lookahead in LOOKAHEAD_RANGE:
        if next_point + lookahead < len(waypoints):
            future_point = (next_point + lookahead) % len(waypoints)
            future_direction = math.degrees(math.atan2(waypoints[future_point][1] - waypoints[next_point][1], 
                                                 waypoints[future_point][0] - waypoints[next_point][0]))
            future_diff = abs(future_direction - track_direction)
            if future_diff > 180:
                future_diff = 360 - future_diff
            
            # Detect upcoming turns with increasing sensitivity for closer waypoints
            if future_diff > (20 - lookahead/2):  # More sensitive for closer points
                approaching_turn = True
                turn_severity = max(turn_severity, future_diff)
                
            # Sharp turn detection - higher threshold
            if future_diff > 25:
                is_sharp_turn = True
                
    MAX_SPEED = 4.0 # max speed defined overall
    STRAIGHT_SPEED = 3.5  # Target speed on straights
    TURN_SPEED = 2.0      # Target speed for normal turns
    SHARP_TURN_SPEED = 1.2  # Target speed for sharp turns
    
    # Calculate target speed based on turn severity
    if is_sharp_turn:
        target_speed = SHARP_TURN_SPEED
    elif is_turning or approaching_turn:
        # Scale speed based on turn severity - sharper turns get slower speeds
        turn_factor = min(1.0, turn_severity / 30.0)  # Normalize turn severity
        target_speed = STRAIGHT_SPEED - (turn_factor * (STRAIGHT_SPEED - SHARP_TURN_SPEED))
    else:
        target_speed = STRAIGHT_SPEED
        
    # Reward for appropriate speed
    speed_reward = 1.0 - (abs(speed - target_speed) / MAX_SPEED)
    # Heavily penalize being too fast for turns
    if (is_turning or approaching_turn) and speed > target_speed * 1.1:
        speed_reward *= 0.5
    if is_sharp_turn and speed > SHARP_TURN_SPEED * 1.1:
        speed_reward *= 0.3  # Severe penalty for excessive speed in sharp turns
    reward += speed_reward * 1.5
        
     # Racing line optimization
    if is_turning or approaching_turn:
        # In turns, reward being on the inside line
        # For counterclockwise racing, reward being on right side of centerline
        optimal_distance = 0.25 * track_width
        if is_sharp_turn:
            optimal_distance = 0.20 * track_width
        if is_left_of_center:  # Right side of track for inside line
            # Reward being close to the optimal distance from center
            reward += (1.0 - abs(distance_from_center - optimal_distance) / optimal_distance) * 0.5
    else:
        # On straightaways, reward being in center
        reward += (1.0 - distance_from_center / (track_width/2)) * 0.3
    
    # Steering optimization
    if is_sharp_turn:
        # In sharp turns, we need appropriate steering
        if abs(steering_angle) < 15:  # Not steering enough in sharp turns
            reward *= 0.8
        elif abs(steering_angle) > 30:  # Too much steering can cause instability
            reward *= 0.9
    elif approaching_turn:
        # Approaching turns - start steering appropriately
        if abs(steering_angle) < 8:  # Need some steering when approaching turns
            reward *= 0.9
    else:
        # On straightaways, minimize steering
        reward += (1.0 - abs(steering_angle)/30.0) * 0.5
    
    # 5. Reward for progress
    reward += progress / 100.0
    
    # 6. Reward for efficiency (completing the track in fewer steps)
    reward += (progress / steps) * 3
    
    return float(reward)