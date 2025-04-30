def reward_function(params):
    '''
    Rewarding the agent to follow center line with normalized reward components
    '''
    
    # Read input parameters
    track_width = params['track_width']
    distance_from_center = params['distance_from_center']
    abs_steering = abs(params['steering_angle'])
    speed = params['speed']
    steps = params['steps']
    progress = params['progress']
    
    # NORMALIZED DISTANCE REWARD (0-1 scale)
    # Normalize to range [0,1] where 1 = perfect center, 0 = edge of track
    distance_reward = 1 - (distance_from_center / (track_width * 0.5))
    
    # NORMALIZED SPEED REWARD (0-1 scale)
    # Target speed is 2.0, with 0.3 acceptable deviation
    # Different target speeds were kept for different tracks.
    target_speed = 2.0
    max_speed_diff = 0.3
    speed_diff = abs(target_speed - speed)
    
    if speed_diff < max_speed_diff:
        speed_reward = 1 - (speed_diff / max_speed_diff)
    else:
        speed_reward = 0.0  # Fully penalize when outside target range
    
    # NORMALIZED PROGRESS REWARD (0-1 scale)
    # Base progress reward (0-1 scale)
    TOTAL_NUM_STEPS = 300
    expected_progress = (steps / TOTAL_NUM_STEPS) * 100
    
    # Normalize progress to 0-1 where 1.0 means making expected or better progress
    progress_reward = min(1.0, progress / expected_progress) if expected_progress > 0 else 0.0
    
    # Bonus for exceeding expectations at checkpoints (now scaled to 0-1)
    progress_bonus = 0.0
    if (steps % 100) == 0 and progress > expected_progress:
        # Normalize bonus based on how much the car exceeds expectations
        # Max bonus of 1.0 for exceeding by 20% or more
        exceed_percent = (progress - expected_progress) / expected_progress
        progress_bonus = min(1.0, exceed_percent / 0.2)
    
    # Combine base progress and bonus (still 0-1 scale)
    progress_reward = progress_reward + progress_bonus
    
    # FINAL REWARD
    reward = distance_reward + speed_reward + progress_reward
    
    return float(reward)