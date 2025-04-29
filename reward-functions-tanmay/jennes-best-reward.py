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
    
    # PRIORITY #1: STAY ON TRACK - Strong penalty but allow recovery
    if not all_wheels_on_track or is_offtrack:
        return 0.01  # Strong penalty but not so extreme to prevent learning
    
    # TRACK POSITION: Reward staying on the optimal racing line
    # Calculate distance from center ratio (0 = center, 1 = edge)
    distance_ratio = distance_from_center / (track_width / 2)
    
    # More generous position reward to encourage finding the racing line
    if distance_ratio <= 0.3:  # Near center
        position_reward = 1.0
    elif distance_ratio <= 0.6:  # Mid-position
        position_reward = 0.8
    elif distance_ratio <= 0.9:  # Getting close to edge
        position_reward = 0.5
    else:  # Very close to edge but still on track
        position_reward = 0.2
    
    reward *= position_reward
    
    # SPEED: Much stronger reward for speed to encourage faster laps
    # BUT with appropriate controls based on steering angle
    if steering_angle <= 10.0:  # Straight/gentle curve - prioritize max speed
        speed_reward = (speed / 8.0) * 3.0  # Triple reward for high speed in straights
    elif steering_angle <= 20.0:  # Moderate turning - still reward good speed
        ideal_speed = 6.0
        # Reward high speed but penalize excessive speed
        if speed <= ideal_speed:
            speed_reward = (speed / ideal_speed) * 1.5
        else:
            # Diminishing returns for speeds above ideal but still reward them
            speed_reward = 1.5 + ((speed - ideal_speed) / 4.0)
    else:  # Sharp turning - reward appropriate speed
        ideal_speed = 4.0
        if speed <= ideal_speed:
            speed_reward = speed / ideal_speed
        else:
            # Diminishing returns but don't severely penalize as in previous version
            over_speed_factor = (speed - ideal_speed) / ideal_speed
            speed_reward = 1.0 - (over_speed_factor * 0.5)  # More gentle penalty
            speed_reward = max(0.5, speed_reward)  # Don't let this drop too low
    
    # Add enhanced speed reward component
    reward += (speed_reward * 3.0)  # Increased from 2.0 to 3.0 for more speed emphasis
    
    # STEERING SMOOTHNESS: Penalize very sharp steering changes but allow aggressive driving
    # Make penalty curve more gradual for moderate steering
    if steering_angle <= 15.0:
        steering_penalty = (steering_angle / 30.0) * 0.3  # Reduced penalty for moderate steering
    else:
        steering_penalty = 0.15 + ((steering_angle - 15.0) / 15.0) * 0.4  # Progressive penalty
    
    reward *= (1.0 - steering_penalty)
    
    # PROGRESS: Stronger reward for completion and speed
    if steps > 0:
        # Higher coefficient for progress per step to reward speed
        progress_per_step = progress / steps
        reward += (progress_per_step * 150)  # Increased from 100 to 150
    
    # Significant completion bonus
    if progress >= 100:
        reward += 30.0  # Increased from 20.0
    
    # Add time bonus - reward completing more of the track in fewer steps
    if steps > 0:
        reward += (progress / (steps * 0.1)) * 10  # Explicitly reward completing more in fewer steps
    
    return float(max(0.01, reward))