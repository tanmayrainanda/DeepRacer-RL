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
    
    # Initialize reward
    reward = 1.0
    
    # 1. Strongly penalize going off track
    if not all_wheels_on_track:
        return 1e-3
    
    # 2. Basic center line following with graduated reward
    # Calculate distance from center normalized to track width
    normalized_distance = distance_from_center / (track_width/2)
    
    # Higher reward for being closer to center line
    distance_reward = 1 - normalized_distance**2  # Quadratic penalty for distance
    reward *= distance_reward
    
    # 3. Proper turning at corners - compare heading with track direction
    # Calculate the direction of the track (in degrees) using waypoints
    next_point = waypoints[closest_waypoints[1]]
    prev_point = waypoints[closest_waypoints[0]]
    
    track_direction = math.degrees(math.atan2(next_point[1] - prev_point[1], 
                                           next_point[0] - prev_point[0]))
    
  
    direction_diff = abs(track_direction - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    
    # Reward the car for steering in the right direction
    if direction_diff > 15:
      
        abs_steering = abs(steering_angle)
        
        # Right amount of steering based on the turn severity
        if 15 < abs_steering < 30:
           
            reward *= 1.2
        elif abs_steering <= 15:
   
            reward *= 0.8
        else:

            reward *= 0.9
    else:

        abs_steering = abs(steering_angle)
        if abs_steering < 5:

            reward *= 1.2
        else:

            reward *= 1.0 - (abs_steering / 30.0)
    
    # 4. Speed management

    if 1.8 <= speed <= 2.2:
        reward *= 1.2
    elif speed < 1.0: 
        reward *= 0.8
    elif speed > 3.0:  
        reward *= 0.7
    
    return float(reward)
