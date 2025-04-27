#1 min 20 secs

import math

def reward_function(params):
    #read input params
    track_width = params['track_width']
    distance_from_center = params['distance_from_center']
    speed = params['speed']
    steering_angle = params['steering_angle']
    all_wheels_on_track = params['all_wheels_on_track']
    progress = params['progress']
    steps = params['steps']
    heading = params['heading']
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    is_left_of_center = params['is_left_of_center']
    
    #initialize reward 
    reward = 1.0
    
    #base reward: for when all wheels not on track
    if not all_wheels_on_track:
        return 1e-3
    
    #using waypoints to define turns, for counterclockwise: need to be on the inside of turns. this is for racing line optimisation
    prev_point = closest_waypoints[0]
    next_point = closest_waypoints[1]
    
    #calculate direction of track (angle between waypoints)
    track_direction = math.degrees(math.atan2(waypoints[next_point][1] - waypoints[prev_point][1], waypoints[next_point][0] - waypoints[prev_point][0]))
    
    #calculate difference between track direction and car heading
    direction_diff = abs(track_direction - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    
    #determine if we're on a turn based on track direction
    TURN_THRESHOLD = 10 #in degrees (can adjust based on track)
    is_turning = direction_diff > TURN_THRESHOLD
    
    #adjust the reward based on racing line
    if is_turning:
        #rewards on inside line for turns and for counterclockwise, reward is on right side of centerline
        optimal_distance = 0.25*track_width #not completely at the edge
        if is_left_of_center: #left side of track
            #reward close to optimal distance from center
            reward += (1.0 - abs(distance_from_center - optimal_distance)/optimal_distance) * 0.5
    else: #reward for being in center
        reward += (1.0 - distance_from_center/(track_width/2)) * 0.3
    
    #speed optimisation
    if is_turning:
        #reward for proper speed in turns (slower)
        IDEAL_TURN_SPEED = 2.0 #can adjust
        reward += (1.0 - abs(speed - IDEAL_TURN_SPEED)/IDEAL_TURN_SPEED) * 0.5
    else: #reward for high speed on straights
        reward += (speed/8.0) * 0.8 #8 is max speed
        
    #penalize excessive steering
    ABS_STEERING_THRESHOLD = 15
    if abs(steering_angle) > ABS_STEERING_THRESHOLD:
        reward *= 0.8
    
    #reward for progress
    reward += progress/100.0
    
    #reward for efficiency (for completing track in fewer steps)
    reward += (progress/steps) * 5
    
    return float(reward)