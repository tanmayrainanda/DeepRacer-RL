import math
import numpy as np
def reward_function(params):
    
    # Parameters for Speed Incentive
    FUTURE_STEP = 6
    TURN_THRESHOLD_SPEED = 6    
    SPEED_THRESHOLD_SLOW = 1.8  
    SPEED_THRESHOLD_FAST = 2    

    # Parameters for Straightness Incentive
    FUTURE_STEP_STRAIGHT = 8
    TURN_THRESHOLD_STRAIGHT = 25    
    STEERING_THRESHOLD = 11         

    # Parameters for Progress Incentive
    TOTAL_NUM_STEPS = 675 


    def identify_corner(waypoints, closest_waypoints, future_step):

        # Identify next waypoint and a further waypoint
        point_prev = waypoints[closest_waypoints[0]]
        point_next = waypoints[closest_waypoints[1]]
        point_future = waypoints[min(len(waypoints) - 1,
                                     closest_waypoints[1] + future_step)]

        # Calculate headings to waypoints
        heading_current = math.degrees(math.atan2(point_prev[1]-point_next[1], 
                                               point_prev[0] - point_next[0]))
        heading_future = math.degrees(math.atan2(point_prev[1] - point_future[1], 
                                               point_prev[0] - point_future[0]))

        # Calculate the difference between the headings
        diff_heading = abs(heading_current - heading_future)


        if diff_heading > 180:
            diff_heading = 360 - diff_heading

        # Calculate distance to further waypoint
        dist_future = np.linalg.norm([point_next[0] - point_future[0],
                                      point_next[1] - point_future[1]])  

        return diff_heading, dist_future


    def select_speed(waypoints, closest_waypoints, future_step):

        # Identify if a corner is in the future
        diff_heading, dist_future = identify_corner(waypoints,
                                                    closest_waypoints,
                                                    future_step)

        if diff_heading < TURN_THRESHOLD_SPEED:
            # If there's no corner encourage going faster
            go_fast = True
        else:
            # If there is a corner encourage slowing down
            go_fast = False

        return go_fast


    def select_straight(waypoints, closest_waypoints, future_step):

        # Identify if a corner is in the future
        diff_heading, dist_future = identify_corner(waypoints,
                                                    closest_waypoints,
                                                    future_step)

        if diff_heading < TURN_THRESHOLD_STRAIGHT:
            # If there's no corner encourage going straighter
            go_straight = True
        else:
            # If there is a corner don't encourage going straighter
            go_straight = False

        return go_straight


    # Read input parameters
    all_wheels_on_track = params['all_wheels_on_track']
    closest_waypoints = params['closest_waypoints']
    distance_from_center = params['distance_from_center']
    is_offtrack = params['is_offtrack']
    progress = params['progress']
    speed = params['speed']
    steering_angle = params['steering_angle']
    steps = params['steps']
    track_width = params['track_width']
    waypoints = params['waypoints']

    # Strongly discourage going off track
    if is_offtrack:
        reward = 1e-3
        return float(reward)
    
    # Give higher reward if the car is closer to centre line and vice versa

    reward = 1 - (distance_from_center/(track_width/2))**(1/4) 


    if (steps % 50) == 0 and progress/100 > (steps/TOTAL_NUM_STEPS):

        reward += progress - (steps/TOTAL_NUM_STEPS)*100

    # Implement straightness incentive
    stay_straight = select_straight(waypoints, closest_waypoints, 
                                    FUTURE_STEP_STRAIGHT)
    if stay_straight and abs(steering_angle) < STEERING_THRESHOLD:
        reward += 0.3

    # Implement speed incentive
    go_fast = select_speed(waypoints, closest_waypoints, FUTURE_STEP)

    if (go_fast and speed > SPEED_THRESHOLD_FAST and 
            abs(steering_angle) < STEERING_THRESHOLD):
        reward += 2.0
    elif not go_fast and speed < SPEED_THRESHOLD_SLOW:
        reward += 0.5    

    # Implement stay on track incentive
    if not all_wheels_on_track:
        reward -= 0.5

    reward = max(reward, 1e-3)
    return float(reward)
