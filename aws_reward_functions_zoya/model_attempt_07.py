#35.917 but veering off track a lot more than 6

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
    
    # 1. Base reward for staying on track - harsher penalty
    if not all_wheels_on_track:
        return 1e-6  # Even smaller reward when off track
    
    # 2. Racing line optimization
    prev_point = closest_waypoints[0]
    next_point = closest_waypoints[1]
    
    # Calculate the direction of the track (angle between waypoints)
    track_direction = math.degrees(math.atan2(waypoints[next_point][1] - waypoints[prev_point][1], 
                                             waypoints[next_point][0] - waypoints[prev_point][0]))
    
    # Calculate the difference between the track direction and car heading
    direction_diff = abs(track_direction - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    
    # Reduced threshold to detect turns earlier
    TURN_THRESHOLD = 8  # Lower this to detect turns sooner
    
    # Expanded lookahead range to detect turns earlier and more points
    LOOKAHEAD_RANGE = [2, 4, 6, 8, 10]  # Added more points and start looking sooner
    
    # initializing turn variables
    is_turning = direction_diff > TURN_THRESHOLD
    approaching_turn = False
    is_sharp_turn = False
    turn_severity = 0
    
    # Looking ahead at different points to detect turns earlier
    for lookahead in LOOKAHEAD_RANGE:
        if next_point + lookahead < len(waypoints):
            future_point = (next_point + lookahead) % len(waypoints)
            future_direction = math.degrees(math.atan2(waypoints[future_point][1] - waypoints[next_point][1], 
                                                 waypoints[future_point][0] - waypoints[next_point][0]))
            future_diff = abs(future_direction - track_direction)
            if future_diff > 180:
                future_diff = 360 - future_diff
            
            # More sensitive turn detection - lowered thresholds
            if future_diff > (15 - lookahead/2):  # More sensitive for all points
                approaching_turn = True
                turn_severity = max(turn_severity, future_diff)
                
            # More sensitive sharp turn detection
            if future_diff > 20:  # Lowered from 25 to detect sharp turns earlier
                is_sharp_turn = True
                
    # Speed range
    MIN_SPEED = 1.0
    MAX_SPEED = 4.0
    
    # More conservative target speeds for different scenarios
    STRAIGHT_SPEED = 3.5    # Slightly lower max speed on straights for better control
    TURN_SPEED = 1.8        # Lower speed for normal turns
    SHARP_TURN_SPEED = 1.2  # Even lower speed for sharp turns
    
    # Calculate target speed based on turn severity with more conservative approach
    if is_sharp_turn:
        # For sharp turns, even more conservative speed adjustment
        turn_factor = min(1.0, turn_severity / 35.0)  # More sensitive to severity
        target_speed = SHARP_TURN_SPEED + (1 - turn_factor) * (TURN_SPEED - SHARP_TURN_SPEED) * 0.3
    elif is_turning or approaching_turn:
        # More conservative speed adjustment for turns
        turn_factor = min(1.0, turn_severity / 25.0)  # More sensitive normalization
        target_speed = TURN_SPEED - (turn_factor * (TURN_SPEED - SHARP_TURN_SPEED)) * 0.8
    else:
        # On straightaways, push for optimized speed
        target_speed = STRAIGHT_SPEED
        
    # Ensure we don't go below minimum speed
    target_speed = max(MIN_SPEED, target_speed)
        
    # Reward for appropriate speed
    speed_reward = 1.0 - (abs(speed - target_speed) / (MAX_SPEED - MIN_SPEED))
    
    # Stricter speed penalties
    if (is_turning or approaching_turn) and speed > target_speed * 1.05:  # Stricter threshold
        speed_reward *= 0.5  # Stronger penalty for excessive speed in turns
    if is_sharp_turn and speed > target_speed * 1.02:  # Very strict threshold for sharp turns
        speed_reward *= 0.3  # Severe penalty for excessive speed in sharp turns
    
    # Bonus for appropriate speed when safe
    if not is_turning and not approaching_turn and speed > MIN_SPEED + 2:
        speed_reward *= 1.2  # Bonus for maintaining higher speeds when safe
    
    reward += speed_reward * 2.5  # Increase importance of speed control
        
    # Racing line optimization - better turn handling
    if is_turning or approaching_turn:
        # In turns, reward being on the inside line
        optimal_distance = 0.20 * track_width  # Tighter racing line
        if is_sharp_turn:
            optimal_distance = 0.15 * track_width  # Even tighter for sharp turns
        
        if is_left_of_center:  # Left side of track for inside line in counterclockwise racing
            # Stronger reward for optimal line positioning
            line_factor = (1.0 - abs(distance_from_center - optimal_distance) / optimal_distance)
            reward += line_factor * 0.8  # Increased weight
        else:
            # Penalty for being on wrong side in turns
            reward *= 0.8
    else:
        # On straightaways, reward being in center
        reward += (1.0 - distance_from_center / (track_width/2)) * 0.3
    
    # Improved steering optimization for turns
    if is_sharp_turn:
        # For sharp turns, reward appropriate steering more clearly
        if abs(steering_angle) < 15:  # Not steering enough in sharp turns
            reward *= 0.7  # Stronger penalty
        elif abs(steering_angle) > 25 and abs(steering_angle) < 30:  # Good steering range for sharp turns
            reward *= 1.2  # Bonus for correct steering angle
        elif abs(steering_angle) > 30:  # Too much steering can cause instability
            reward *= 0.8
    elif approaching_turn:
        # Approaching turns - start steering appropriately
        if abs(steering_angle) < 10:  # Need more steering when approaching turns
            reward *= 0.8
        elif abs(steering_angle) > 12 and abs(steering_angle) < 20:  # Good range for approaching turns
            reward *= 1.1  # Small bonus for preparing for the turn properly
    else:
        # On straightaways, minimize steering but with small tolerance
        straightaway_steering = (1.0 - abs(steering_angle)/20.0)
        reward += straightaway_steering * 0.5
    
    # Balanced progress and speed rewards
    speed_progress_reward = (speed / MAX_SPEED) * (progress / 100.0)
    reward += speed_progress_reward * 1.5  # Slightly reduced to prioritize control over raw speed
    
    # Progress reward
    reward += progress / 100.0
    
    # Efficiency reward - slightly reduced to prioritize control
    reward += (progress / steps) * 3
    
    return float(reward)