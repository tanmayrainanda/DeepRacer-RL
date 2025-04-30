import math

def reward_function(params):

  
    #Constants
    GLOBAL_MIN = -1e5
    GLOBAL_MAX = 1e5
    

    #Parameters
    all_wheels_on_track = params['all_wheels_on_track']
    x = params['x']
    y = params['y']
    distance_from_center = params['distance_from_center']
    heading = params['heading']  
    progress = params['progress']
    steps = params['steps']
    speed = params['speed'] 
    steering_angle = params['steering_angle']  
    track_width = params['track_width']
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    closest_waypoint = closest_waypoints[1] 

    # Negative exponential penalty for distance from center
    reward = math.exp(-6 * distance_from_center)
    
    # Giant penalty if vehicle is exiting track
    if not all_wheels_on_track:
        reward = GLOBAL_MIN
    elif progress == 100: 
        reward = GLOBAL_MAX
    else:  
        reward = reward * (progress / 100.0)
    

    next_waypoint = waypoints[min(closest_waypoint + 1, len(waypoints) - 1)]
    next_point_x, next_point_y = next_waypoint[0], next_waypoint[1]
    
    # Calculate the yaw (heading) to the next waypoint
    next_waypoint_yaw = math.degrees(math.atan2(next_point_y - y, next_point_x - x))
    

    heading_degrees = math.degrees(math.radians(heading))
    
    # Penalize reward if orientation of the vehicle deviates too much from ideal orientation

    direction_diff = abs(heading_degrees - next_waypoint_yaw)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
        
    if direction_diff >= 10: 
        reward *= 0.25
    
    # Penalize reward if the car is steering too much
    ABS_STEERING_THRESHOLD = 0.85
    if abs(steering_angle) > ABS_STEERING_THRESHOLD:
        reward *= 0.75
    
    # Reward higher speeds
    reward *= 0.5 + (speed / 8.0)  # Normalize speed (max speed is around 4-8 m/s)
    
    # Decrease throttle while steering to some extent
    if speed > 1 - (0.4 * abs(steering_angle)):
        reward *= 0.8
    
    reward = max(reward, GLOBAL_MIN)
    reward = min(reward, GLOBAL_MAX)
    
    return float(reward)
