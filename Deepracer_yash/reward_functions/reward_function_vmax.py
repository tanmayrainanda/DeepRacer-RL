import math

def reward_function(params):
    """
    Estimating track ahead and calculating the maximum velocity
    at the upcoming turn. Penalising for the difference.
    """
    # Extract parameters
    all_wheels_on_track = params['all_wheels_on_track']
    distance_from_center = params['distance_from_center']
    track_width = params['track_width']
    speed = params['speed']
    steering_angle = params['steering_angle']
    heading = params['heading']
    is_offtrack = params['is_offtrack']
    is_crashed = params['is_crashed']
    progress = params['progress']
    steps = params['steps']
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    is_left_of_center = params['is_left_of_center']
    track_length = params['track_length']
    
    # Initialize reward
    reward = 1.0
    
    # CRITICAL FAILURES - return minimal reward
    if is_crashed:
        return 1e-3
    if is_offtrack:
        return 1e-3
    
    # PROGRESS INCENTIVE - reward for % of track completed per step
    # This encourages finishing the track quickly
    progress_reward = progress / steps if steps > 0 else 0
    reward += progress_reward * 10  # Scale up the progress importance
    
    # TRACK POSITION - reward for staying near centerline but allow racing line
    normalized_distance = distance_from_center / (track_width / 2)
    # Quadratic reward - higher near center, falls off toward edges
    center_reward = 1.0 - (normalized_distance ** 1.5)  # Less punitive than square
    reward *= max(0.3, center_reward)  # At least 30% of base reward
    
    # DIRECTION ALIGNMENT with track - enhanced
    prev_waypoint = waypoints[closest_waypoints[0]]
    next_point = waypoints[closest_waypoints[1]]
    next_next_idx = (closest_waypoints[1] + 1) % len(waypoints)
    next_next_point = waypoints[next_next_idx]

    # Get a blended target direction using current and next segments
    track_direction = math.degrees(math.atan2(
        0.6 * (next_point[1] - prev_waypoint[1]) + 0.4 * (next_next_point[1] - next_point[1]),
        0.6 * (next_point[0] - prev_waypoint[0]) + 0.4 * (next_next_point[0] - next_point[0])
    ))

    # Adjust for angle wrap
    if track_direction < 0:
        track_direction += 360

    # Calculate the difference between track direction and heading
    direction_diff = abs(track_direction - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff

    # Much stricter reward for alignment - critical for reducing zigzag
    direction_reward = gaussian(0, 15, direction_diff)  # Narrower width (was 30)
    reward *= max(0.4, direction_reward)  # More impact (was 0.5)
    
    # CURVE DETECTION & TURN DIRECTION - look ahead to plan speed and optimal position
    look_ahead = min(len(waypoints) // 8, 15)  # Look ahead further
    future_angles = []
    
    # Variables to analyze turn direction
    turn_direction = "straight"  # Default is straight
    angle_sum = 0
    
    current_idx = closest_waypoints[1]
    for i in range(look_ahead):
        idx = (current_idx + i) % len(waypoints)
        next_idx = (idx + 1) % len(waypoints)
        
        # Get consecutive waypoints
        wp1 = waypoints[idx]
        wp2 = waypoints[next_idx]
        
        if i > 0:  # We already have a previous point to use
            prev_wp = waypoints[(idx - 1) % len(waypoints)]
            
            # Calculate vectors for consecutive segments
            vector1 = [wp1[0] - prev_wp[0], wp1[1] - prev_wp[1]]
            vector2 = [wp2[0] - wp1[0], wp2[1] - wp1[1]]
            
            # Calculate cross product to determine turn direction
            cross_product = vector1[0] * vector2[1] - vector1[1] * vector2[0]
            
            # Calculate angles between segments
            angle1 = math.atan2(wp1[1] - prev_wp[1], wp1[0] - prev_wp[0])
            angle2 = math.atan2(wp2[1] - wp1[1], wp2[0] - wp1[0])
            
            # Calculate the difference and convert to degrees
            diff = math.degrees(abs(angle2 - angle1))
            """if diff > 180:
                diff = 360 - diff"""
            
            # Accumulate angle changes and cross products to determine overall turn direction
            future_angles.append(diff)
            angle_sum += cross_product
    
    # Determine turn direction from the sum of cross products
    if angle_sum > 5.0:  # Threshold for considering a right turn
        turn_direction = "right"
    elif angle_sum < -5.0:  # Threshold for considering a left turn
        turn_direction = "left"
    
    # Determine max curvature in upcoming track segment
    max_angle = max(future_angles) if future_angles else 0
    
    # Set target speed based on curve severity
    
    if max_angle > 30:  # Sharp turn
        target_speed = 1.0  # Slower for sharp turns
    elif max_angle > 15:  # Moderate turn
        target_speed = 2.0  # Slightly slower
    elif max_angle > 180:
        target_speed = 0.5
    else:  # Straight or gentle curve
        target_speed = 3.5  # Slightly slower on straights for better control
    
    # RACING LINE OPTIMIZATION - based on accurate turn direction detection
    # Check if agent is on the appropriate side of the track for the upcoming turn
    optimal_side_reward = 1.0
    
    if max_angle > 15:  # We're in a significant turn
        # For optimal racing line:
        # - In left turns, want to be on right side of track then move to inside
        # - In right turns, want to be on left side of track then move to inside
        
        # Calculate normalized distance from center (-1 is far left, +1 is far right)
        signed_distance = distance_from_center / (track_width/2)
        if not is_left_of_center:
            signed_distance *= -1  # Adjust sign based on side of track
        
        # Calculate optimal position based on turn direction
        if turn_direction == "left":
            # For left turn: Start on right side (positive distance)
            # Sharp left turns need more setup on the right
            if max_angle > 30:
                optimal_side = 0.7  # Further right for sharp left turns
            else:
                optimal_side = 0.4  # Moderately right for gentle left turns
                
            optimal_side_reward = gaussian(optimal_side, 0.3, signed_distance)
            
        elif turn_direction == "right":
            # For right turn: Start on left side (negative distance)
            # Sharp right turns need more setup on the left
            if max_angle > 30:
                optimal_side = -0.7  # Further left for sharp right turns
            else:
                optimal_side = -0.4  # Moderately left for gentle right turns
                
            optimal_side_reward = gaussian(optimal_side, 0.3, signed_distance)
        
        # Apply the optimal side reward
        reward *= max(0.7, optimal_side_reward)
    
    # CURVE ANTICIPATION - prepare for curves earlier
    if future_angles and max(future_angles[:min(3, len(future_angles))]) > 20:
        # There's a significant curve coming up soon
        
        # If speed is too high approaching a curve
        if speed > target_speed + 0.5:
            reward *= 0.8  # Penalty for approaching curve too fast
            
        # Reward for already starting to turn in the correct direction
        if (turn_direction == "right" and steering_angle > 5) or \
           (turn_direction == "left" and steering_angle < -5):
            reward *= 1.1  # Bonus for anticipating the turn direction correctly
    
    # Reward for being close to target speed
    speed_reward = gaussian(target_speed, 1.0, speed)  # Peak at target speed, fall off by 1.0 m/s
    reward *= max(0.5, speed_reward)  # At least 50% of current reward
    
    # STEERING PENALTY - much stronger penalty for wavering
    abs_steering = abs(steering_angle)
    if abs_steering < 10:
        # Much heavier penalty for small angles (wavering)
        steering_penalty = gaussian(0, 1.5, abs_steering)  # Narrower width
    else:
        # Moderate penalty for necessary turns
        steering_penalty = gaussian(0, 12, abs_steering)  # Still forgiving for actual turns
    
    # Apply more impact from steering penalty
    reward *= max(0.5, steering_penalty)  # More impactful
    
    # STEERING CHANGE PENALTY - penalize rapid steering changes
    # Need to store previous steering in a way that persists across function calls
    if not hasattr(reward_function, 'prev_steering'):
        reward_function.prev_steering = 0.0
        
    steering_change = abs(steering_angle - reward_function.prev_steering)
    # Heavy penalty for rapid steering changes
    steering_change_penalty = gaussian(0, 3, steering_change)
    reward *= max(0.7, steering_change_penalty)
    
    # Store current steering for next iteration
    reward_function.prev_steering = steering_angle
    
    # SPEED BONUS - reward high speed when safe
    if future_angles and all(angle < 10 for angle in future_angles[:min(3, len(future_angles))]):
        # If upcoming track is straight
        speed_bonus = speed / 4.0  # Up to 100% bonus at max speed
        reward *= (1.0 + speed_bonus)
    
    # CONSISTENCY REWARD - stronger emphasis on smooth driving
    if not hasattr(reward_function, 'prev_speed'):
        reward_function.prev_speed = speed
    
    speed_change = abs(speed - reward_function.prev_speed)
    
    # Reward consistency (smooth speed transitions)
    consistency_reward = gaussian(0, 0.5, speed_change)
    reward *= (1.0 + 0.1 * consistency_reward)  # Up to 10% bonus for perfect consistency
    
    # Store current speed for next iteration
    reward_function.prev_speed = speed
    
    return float(max(reward, 1e-3))  # Ensure positive reward

# Helper function for Gaussian reward - peaks at target value and falls off according to width
def gaussian(mean, width, x):
    """Width controls how quickly the function falls off from the mean"""
    return math.exp(-0.5 * ((x - mean) / width) ** 2)