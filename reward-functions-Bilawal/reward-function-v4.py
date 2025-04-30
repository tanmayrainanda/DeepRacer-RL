import math

def reward_function(params):

    # Read input parameters
    track_width = params['track_width']
    distance_from_center = params['distance_from_center']
    all_wheels_on_track = params['all_wheels_on_track']
    steering_angle = params['steering_angle']
    speed = params['speed']
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    heading = params['heading']
    steps = params.get('steps', 0)
    progress = params.get('progress', 0)
    
    # Initialize reward - starting significantly higher to allow for meaningful penalties
    reward = 5.0
    
    # ===============================
    # 1. CRITICAL: Staying on track - SEVERE penalty for going off track
    # ===============================
    if not all_wheels_on_track:
        # Much stronger penalty - essentially ends the episode with a very negative reward
        return 1e-6
    

    reward += 2.0
    
    # ===============================
    # 2. Center line following - exponential reward
    # ===============================
    # Calculate distance from center normalized to track width
    normalized_distance = distance_from_center / (track_width/2)
    
    # Exponentially higher reward for being closer to center line

    center_reward = math.exp(-3 * normalized_distance)
    
    # Scale the impact of center line following
    reward *= center_reward
    
    # Additional severe penalty when getting dangerously close to edge

    if normalized_distance > 0.8:
        reward *= 0.5  # Cut reward in half when near the edge
    
    # ===============================
    # 3. Proper turning - align with track direction
    # ===============================

    next_point = waypoints[closest_waypoints[1]]
    prev_point = waypoints[closest_waypoints[0]]
    
    # Get track direction and car heading
    track_direction = math.degrees(math.atan2(next_point[1] - prev_point[1], 
                                           next_point[0] - prev_point[0]))
    

    direction_diff = abs(track_direction - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    

    # Look ahead by 3 waypoints
    next_waypoint_idx = (closest_waypoints[1] + 3) % len(waypoints)
    future_point = waypoints[next_waypoint_idx]
    

    upcoming_direction = math.degrees(math.atan2(future_point[1] - next_point[1], 
                                             future_point[0] - next_point[0]))
    

    track_curvature = abs(upcoming_direction - track_direction)
    if track_curvature > 180:
        track_curvature = 360 - track_curvature
    
    # Determine if we're in a curve or straight section
    is_curve = track_curvature > 10
    
    # Steering reward based on track conditions
    abs_steering = abs(steering_angle)
    
    if is_curve:

        if direction_diff < 10:
            # Car is aligned with track direction
            reward *= 1.2
        elif direction_diff > 20:
            # Car heading is too different from track direction
            reward *= 0.8
        
        # Check steering appropriateness for curves
        if 10 < abs_steering < 25:
            # Good steering for a turn, but not excessive
            reward *= 1.3
        elif abs_steering <= 5:

            reward *= 0.8
    else:

        if abs_steering < 5:

            reward *= 1.2
        else:

            reward *= 0.9 - (abs_steering / 40.0)
    
    # ===============================
    # 4. Speed management - adaptive based on track conditions
    # ===============================
    optimal_speed = 2.5
    

    if is_curve:
        optimal_speed = 2.0 
    

    speed_reward = 1.0 - abs(speed - optimal_speed) / optimal_speed
    reward *= max(speed_reward, 0.5) 
    

    if speed < 1.0:  # Too slow
        reward *= 0.7
    
    # ===============================
    # 5. Progress incentive
    # ===============================
    # Small reward for making progress around the track

    if progress > 0:
        progress_reward = progress / 100.0  
        reward += progress_reward
    
    return float(reward)
