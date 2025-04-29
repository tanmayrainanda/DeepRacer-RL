def reward_function(params):
    # Extract key parameters
    all_wheels_on_track = params['all_wheels_on_track']
    distance_from_center = params['distance_from_center']
    track_width = params['track_width']
    speed = params['speed']
    steering_angle = abs(params['steering_angle'])
    progress = params['progress']
    steps = params['steps']
    is_offtrack = params['is_offtrack']
    
    # Base reward - start with a positive value
    reward = 5.0
    
    # PRIORITY #1: STAY ON TRACK - Much stronger penalty
    if not all_wheels_on_track or is_offtrack:
        return 0.001  # Severe penalty for going off track
    
    # TRACK POSITION: Reward staying closer to racing line
    # Calculate distance from center ratio (0 = center, 1 = edge)
    distance_ratio = distance_from_center / (track_width / 2)
    
    # More progressive position reward
    if distance_ratio <= 0.2:  # Very close to center
        position_reward = 1.0
    elif distance_ratio <= 0.4:  # Near center
        position_reward = 0.9
    elif distance_ratio <= 0.6:  # Mid-position
        position_reward = 0.7
    elif distance_ratio <= 0.8:  # Getting close to edge
        position_reward = 0.4
    else:  # Very close to edge
        position_reward = 0.1
    
    reward *= position_reward
    
    # SPEED vs STEERING: More sophisticated relationship between speed and steering
    # Lower acceptable speeds in sharp turns to prevent spinning
    if steering_angle <= 5.0:  # Straight sections
        ideal_speed = 8.0
        speed_reward = speed / ideal_speed
    elif steering_angle <= 15.0:  # Gentle curves
        ideal_speed = 6.0
        speed_reward = speed / ideal_speed
    elif steering_angle <= 25.0:  # Moderate curves
        ideal_speed = 4.0
        speed_reward = speed / ideal_speed
    else:  # Sharp turns
        ideal_speed = 2.0
        speed_reward = speed / ideal_speed
        
    # Penalize for going too fast in curves - this helps prevent spinning
    if steering_angle > 15.0 and speed > ideal_speed + 1.0:
        speed_reward *= 0.5
    
    # Cap speed reward at 1.0
    speed_reward = min(speed_reward, 1.0)
    reward += (speed_reward * 2.0)
    
    # STEERING SMOOTHNESS: Stronger penalty for excessive steering
    steering_penalty = (steering_angle / 30.0) * 0.7  # Increased from 0.4 to 0.7
    reward *= (1.0 - steering_penalty)
    
    # PROGRESS: Reward completion and consistent progress
    if steps > 0:
        progress_reward = progress / steps
        reward += (progress_reward * 100)
    
    # Completion bonus
    if progress >= 100:
        reward += 20.0
    
    return float(max(0.001, reward))