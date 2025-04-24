import math
def reward_function(params):
    """
    Track - Jennens Super Speedway (62.07m) clockwise
    Target lap time: under 55 seconds
    """
    
    # Read input parameters
    track_width = params['track_width']
    distance_from_center = params['distance_from_center']
    steering_angle = params['steering_angle']
    steering_abs = abs(steering_angle)
    speed = params['speed']
    all_wheels_on_track = params['all_wheels_on_track']
    progress = params['progress']
    steps = params['steps']
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    heading = params['heading']
    is_left_of_center = params['is_left_of_center']
    
    # Initialize reward
    reward = 1.0
    
    # Strongly penalize going off track - this is critical
    if not all_wheels_on_track:
        return 1e-3
    
    # Calculate speed factor - we want to reward higher speeds
    # Max speed is usually around 8-10 m/s
    speed_factor = speed / 10.0
    
    # Get current and next waypoint coordinates
    prev_point = waypoints[closest_waypoints[0]]
    next_point = waypoints[closest_waypoints[1]]
    
    # Calculate direction from current to next waypoint
    track_direction = math.degrees(math.atan2(next_point[1] - prev_point[1], next_point[0] - prev_point[0]))
    
    # Normalize track direction to range [-180, 180]
    track_direction = (track_direction + 360) % 360
    if track_direction > 180:
        track_direction -= 360
    
    # Calculate the difference between the track direction and car heading
    direction_diff = abs(track_direction - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    
    # Penalize if the car's heading isn't aligned with the track direction
    # This ensures car is properly aligned for upcoming track sections
    heading_reward = 1.0
    if direction_diff > 10:
        heading_reward = 0.8
    if direction_diff > 20:
        heading_reward = 0.5
    
    reward *= heading_reward
    
    # Racing line optimization - being in center is not always optimal
    # Calculate the ideal distance from center based on steering angle
    # For straight sections (low steering), center is good
    # For corners (high steering), slight offset from center may be better for racing line
    
    distance_ratio = distance_from_center / (track_width / 2)
    
    if steering_abs < 10:
        # Straight section - stay close to center
        if distance_ratio <= 0.2:
            racing_line_reward = 1.0
        elif distance_ratio <= 0.5:
            racing_line_reward = 0.8
        else:
            racing_line_reward = 0.5
    elif steering_abs < 20:
        # Moderate turn - slight offset can be good
        # Favor inside line (opposite side of steering direction)
        inside_line = (steering_angle < 0 and is_left_of_center) or (steering_angle > 0 and not is_left_of_center)
        if inside_line and distance_ratio <= 0.5:
            racing_line_reward = 1.0
        elif distance_ratio <= 0.7:
            racing_line_reward = 0.8
        else:
            racing_line_reward = 0.5
    else:
        # Sharp turn - tighter line is generally better
        # Favor inside line more aggressively
        inside_line = (steering_angle < 0 and is_left_of_center) or (steering_angle > 0 and not is_left_of_center)
        if inside_line and distance_ratio <= 0.6:
            racing_line_reward = 1.0
        elif distance_ratio <= 0.7:
            racing_line_reward = 0.7
        else:
            racing_line_reward = 0.3
    
    reward *= racing_line_reward
    
    # Speed optimization based on corner severity
    # Ideal speed varies by steering angle
    if steering_abs < 10:
        # Straight or gentle curve - maximum speed
        speed_reward = speed / 10.0
    elif steering_abs < 20:
        # Moderate turn - slightly reduced speed
        optimal_speed = 6.0
        speed_reward = 1.0 - abs(speed - optimal_speed) / optimal_speed
    else:
        # Sharp turn - lower speeds are necessary
        optimal_speed = 4.0
        speed_reward = 1.0 - abs(speed - optimal_speed) / optimal_speed
    
    # Square the speed reward to emphasize its importance
    reward += speed_reward * speed_reward * 2.0
    
    # Penalize excessive or erratic steering
    steering_penalty = (steering_abs / 30.0) ** 2
    reward *= (1.0 - steering_penalty * 0.5)
    
    # Reward for progress - completion efficiency
    # Optimize for lap time by rewarding efficient progress
    if steps > 0:
        progress_per_step = progress / steps
        # Ideal progress per step for 55 second lap (assuming 10 steps/second on 62.07m track)
        ideal_progress = 0.18  # 100% / (55 seconds * 10 steps/second)
        
        if progress_per_step >= ideal_progress:
            # Significantly reward being on pace for record lap
            progress_reward = 2.0
        elif progress_per_step >= ideal_progress * 0.8:
            # Still good pace
            progress_reward = 1.0
        else:
            # Below desired pace
            progress_reward = 0.5
            
        reward += progress_reward
    
    # Extra reward for technical sections mastery
    # Technical sections are characterized by sequences of turns
    # Look ahead to next few waypoints to identify technical sections
    lookahead_distance = 5  # Number of waypoints to look ahead
    
    technical_section = False
    direction_changes = 0
    prev_direction = None
    
    for i in range(lookahead_distance):
        curr_idx = (closest_waypoints[1] + i) % len(waypoints)
        next_idx = (curr_idx + 1) % len(waypoints)
        
        wp1 = waypoints[curr_idx]
        wp2 = waypoints[next_idx]
        
        next_direction = math.atan2(wp2[1] - wp1[1], wp2[0] - wp1[0])
        
        if prev_direction is not None:
            dir_diff = abs(next_direction - prev_direction)
            if dir_diff > 0.2:  # About 11.5 degrees - threshold for direction change
                direction_changes += 1
        
        prev_direction = next_direction
    
    if direction_changes >= 2:
        technical_section = True
    
    if technical_section and all_wheels_on_track and speed > 3.0:
        # Reward maintaining good speed through technical sections
        reward += 1.0
    
    # Special reward for drag strip sections (straightaways)
    # In straightaways (low steering), heavily reward high speeds
    if steering_abs < 8 and speed > 7.0:
        reward += 1.5  # Significant bonus for high speed on straights
    
    # Completion bonus
    if progress == 100:
        reward += 10.0
    
    return float(reward)