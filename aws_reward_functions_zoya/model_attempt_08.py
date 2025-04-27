#built up mainly on 3 as baseline, sped up but really bad off course veering
#44.533

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
    
    TURN_THRESHOLD = 10  # threshold for turn detection
    # looking several steps ahead to detect sharp turns (at multiple points)
    LOOKAHEAD_RANGE = [3, 6, 9, 12]  # Added one more lookahead point for better prediction
    
    # initializing turn variables
    is_turning = direction_diff > TURN_THRESHOLD
    approaching_turn = False
    is_sharp_turn = False
    turn_severity = 0
    
    # looking ahead at different points
    for lookahead in LOOKAHEAD_RANGE:
        lookahead_idx = (next_point + lookahead) % len(waypoints)
        future_direction = math.degrees(math.atan2(waypoints[lookahead_idx][1] - waypoints[next_point][1], 
                                              waypoints[lookahead_idx][0] - waypoints[next_point][0]))
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
                
    # *** SPEED PARAMETERS - ADJUSTED FOR HIGHER SPEED ***
    MAX_SPEED = 4.0  # Increased max speed overall
    STRAIGHT_SPEED = 4.0  # Increased target speed on straights
    TURN_SPEED = 2.0  # Increased target speed for normal turns 
    SHARP_TURN_SPEED = 1.3  # Slightly increased target speed for sharp turns 
    
    # Calculate target speed based on turn severity with more granularity
    if is_sharp_turn:
        # Adjust speed based on how sharp the turn is
        sharpness_factor = min(1.0, turn_severity / 45.0)  # Normalize turn severity
        target_speed = SHARP_TURN_SPEED - (sharpness_factor * 0.3)  # Reduce speed for extremely sharp turns
    elif is_turning or approaching_turn:
        # Scale speed based on turn severity - sharper turns get slower speeds
        turn_factor = min(1.0, turn_severity / 30.0)  # Normalize turn severity
        target_speed = STRAIGHT_SPEED - (turn_factor * (STRAIGHT_SPEED - SHARP_TURN_SPEED))
    else:
        target_speed = STRAIGHT_SPEED
        
    # Enhanced speed reward function for better speed control
    # The closer to target speed, the higher the reward
    speed_diff = abs(speed - target_speed)
    if speed < target_speed:
        # Less penalty for being slightly under target speed
        speed_reward = 1.0 - (speed_diff / MAX_SPEED) * 0.8
    else:
        # More penalty for being over target speed
        speed_reward = 1.0 - (speed_diff / MAX_SPEED) * 1.2
        
    # Additional speed penalties for turns
    if (is_turning or approaching_turn) and speed > target_speed * 1.15:  # Slightly more lenient threshold
        speed_reward *= 0.6  # Less severe penalty
    if is_sharp_turn and speed > SHARP_TURN_SPEED * 1.2:  # Slightly more lenient
        speed_reward *= 0.4  # Still significant penalty for excessive speed in sharp turns
        
    # Increased weight for speed reward to encourage optimal speed
    reward += speed_reward * 1.8  # Increased weight (was 1.5)
        
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
    
    # Steering optimization - adjusted for higher speeds
    if is_sharp_turn:
        # In sharp turns, we need appropriate steering
        if abs(steering_angle) < 15:  # Not steering enough in sharp turns
            reward *= 0.8
        elif abs(steering_angle) > 30:  # Too much steering can cause instability
            reward *= 0.9
    elif approaching_turn:
        # Approaching turns - start steering appropriately but smoothly
        if abs(steering_angle) < 10:  # Increased threshold for earlier steering
            reward *= 0.9
        elif abs(steering_angle) > 25:  # Avoid too aggressive steering when approaching
            reward *= 0.9
    else:
        # On straightaways, minimize steering
        reward += (1.0 - abs(steering_angle)/30.0) * 0.5
    
    # Reward for progress
    reward += progress / 100.0
    
    # Reward for efficiency (completing the track in fewer steps)
    # Increased weight to emphasize efficiency with higher speeds
    reward += (progress / steps) * 4  # Increased from 3
    
    return float(reward)