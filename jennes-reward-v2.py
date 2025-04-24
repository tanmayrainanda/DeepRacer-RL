def reward_function(params):
    
    # Extract key parameters
    all_wheels_on_track = params['all_wheels_on_track']
    distance_from_center = params['distance_from_center']
    track_width = params['track_width']
    speed = params['speed']
    steering_angle = abs(params['steering_angle'])
    progress = params['progress']
    steps = params['steps']
    
    # Base reward - start with a positive value
    reward = 5.0
    
    # PRIORITY #1: STAY ON TRACK
    # Strong off-track penalty but not too extreme to allow learning
    if not all_wheels_on_track:
        return 0.1  # Still allow some small reward to help with learning
    
    # TRACK POSITION: Reward staying on track with reasonable margins
    # Calculate distance from center ratio (0 = center, 1 = edge)
    distance_ratio = distance_from_center / (track_width / 2)
    
    # More generous position reward to keep car on track
    if distance_ratio <= 0.3:       # Near center
        position_reward = 1.0
    elif distance_ratio <= 0.6:     # Mid-position
        position_reward = 0.8
    elif distance_ratio <= 0.9:     # Getting close to edge
        position_reward = 0.5
    else:                           # Very close to edge but still on track
        position_reward = 0.3
    
    reward *= position_reward
    
    # SPEED: Encourage speed but keep it reasonable based on steering
    # Simpler speed reward calculation with reasonable scaling
    if steering_angle <= 10.0:      # Straight/gentle curve - high speed is good
        speed_reward = speed / 8.0  # Assuming max speed around 8-10 m/s
    elif steering_angle <= 20.0:    # Moderate turning - medium speed
        speed_reward = speed / 6.0
        # Cap the reward at 1.0 for this range
        speed_reward = min(speed_reward, 1.0)
    else:                           # Sharp turning - lower speed
        speed_reward = speed / 4.0
        # Cap the reward at 1.0 for this range
        speed_reward = min(speed_reward, 1.0)
    
    # Add speed reward component
    reward += (speed_reward * 2.0)
    
    # STEERING SMOOTHNESS: Penalize excessive steering but not too harshly
    # Milder steering penalty to encourage smoother driving
    steering_penalty = (steering_angle / 30.0) * 0.4
    reward *= (1.0 - steering_penalty)
    
    # PROGRESS: Reward completion and consistent progress
    # Simple progress reward component
    if steps > 0:
        progress_reward = progress / steps
        # Scale to make the progress reward meaningful but not overwhelming
        reward += (progress_reward * 100)
    
    # Significant completion bonus
    if progress >= 100:
        reward += 20.0
    
    # Return float reward value - keep the scale reasonable
    return float(max(0.1, reward))  # Ensure minimum reward is 0.1