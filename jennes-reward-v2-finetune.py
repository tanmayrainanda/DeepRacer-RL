def reward_function(params):
    """
    Fine-tuning reward function for cloned model - Jennens Super Speedway
    Focus on eliminating off-track penalties while maintaining speed
    """
    
    # Extract key parameters
    all_wheels_on_track = params['all_wheels_on_track']
    distance_from_center = params['distance_from_center']
    track_width = params['track_width']
    speed = params['speed']
    steering_angle = abs(params['steering_angle'])
    progress = params['progress']
    steps = params['steps']
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    heading = params['heading']
    
    # Base reward - start with a substantial positive value
    reward = 5.0
    
    # =================== TRACK ADHERENCE (HIGHEST PRIORITY) ===================
    # Much stronger penalty for going off-track to eliminate off-track incidents
    if not all_wheels_on_track:
        return 0.001  # Severe penalty for off-track
    
    # Calculate distance from center ratio (0 = center, 1 = edge)
    distance_ratio = distance_from_center / (track_width / 2)
    
    # =================== PREVENTIVE BOUNDARY MANAGEMENT ===================
    # Progressive penalties as car approaches track edges
    if distance_ratio <= 0.3:       # Safe zone near center
        position_reward = 1.0
    elif distance_ratio <= 0.5:     # Still good
        position_reward = 0.9
    elif distance_ratio <= 0.7:     # Getting closer to edge - be careful
        position_reward = 0.7
    elif distance_ratio <= 0.85:    # Warning zone - significantly reduce reward
        position_reward = 0.4
    else:                           # Danger zone - severe warning
        position_reward = 0.2
        # If in danger zone AND steering away from center, apply additional penalty
        center_direction = -1 if params['is_left_of_center'] else 1
        steering_direction = -1 if params['steering_angle'] < 0 else 1
        
        if center_direction == steering_direction:  # Steering away from center
            position_reward *= 0.5  # Further reduce reward when steering toward edge
    
    reward *= position_reward
    
    # =================== HEADING ALIGNMENT ===================
    # Calculate track direction to ensure car is properly aligned
    next_point = waypoints[closest_waypoints[1]]
    prev_point = waypoints[closest_waypoints[0]]
    
    import math
    # Calculate track heading
    track_direction = math.degrees(math.atan2(next_point[1] - prev_point[1], 
                                             next_point[0] - prev_point[0]))
    
    # Convert to [-180, 180] range
    track_direction = (track_direction + 360) % 360
    if track_direction > 180:
        track_direction -= 360
        
    # Calculate the difference between track direction and car heading
    direction_diff = abs(track_direction - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
        
    # Reward proper alignment with track
    if direction_diff <= 10:
        reward *= 1.0
    elif direction_diff <= 20:
        reward *= 0.9
    elif direction_diff <= 30:
        reward *= 0.7
    else:
        reward *= 0.5
    
    # =================== SPEED OPTIMIZATION ===================
    # Maintain speed rewards from previous function but with better steering correlation
    if steering_angle <= 10.0:      # Straight/gentle curve - high speed is good
        speed_reward = speed / 8.0
        # Extra bonus for high speed in straight sections
        if speed >= 7.0:
            speed_reward *= 1.2
    elif steering_angle <= 20.0:    # Moderate turning - medium speed
        optimal_speed = 5.0
        speed_reward = 1.0 - (abs(speed - optimal_speed) / optimal_speed) * 0.5
    else:                           # Sharp turning - lower speed
        optimal_speed = 3.5
        speed_reward = 1.0 - (abs(speed - optimal_speed) / optimal_speed) * 0.5
    
    # Add speed reward component with appropriate scaling
    reward += (speed_reward * 2.0)
    
    # =================== SMOOTH DRIVING ===================
    # Penalize excessive steering changes to promote smooth driving
    steering_penalty = (steering_angle / 30.0) * 0.4
    reward *= (1.0 - steering_penalty)
    
    # =================== PROGRESS TRACKING ===================
    # Time efficiency factor - reward consistent progress
    if steps > 0:
        # Target: ~55 second lap time on 62.07m track
        # Assuming 10 steps/second: ~550 steps for target lap
        # So optimal progress per step is about 0.18%
        progress_per_step = progress / steps
        target_progress = 0.18
        
        if progress_per_step >= target_progress:  # On target pace
            reward += (progress_per_step / target_progress) * 3.0
        else:  # Below target pace
            reward += (progress_per_step / target_progress) * 1.5
    
    # Completion bonus
    if progress >= 100:
        reward += 30.0
    
    # Ensure minimum reward is very small but positive for learning
    return float(max(0.001, reward))