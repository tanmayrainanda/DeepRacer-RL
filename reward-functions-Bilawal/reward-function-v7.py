import math
import numpy as np

def reward_function(params):
    """
    Focuses on track adherence, path optimization, and appropriate speed adjustments
    """

    track_width = params['track_width']
    distance_from_center = params['distance_from_center']
    all_wheels_on_track = params['all_wheels_on_track']
    steering_angle = params['steering_angle']
    speed = params['speed']
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    heading = params['heading']
    progress = params['progress']
    steps = params['steps']
    
    # Base reward - starts with moderate value
    base_reward = 1.0
    
    # Track position analysis
    track_position_reward = calculate_track_position_reward(distance_from_center, track_width)
    
    # Course analysis
    course_reward = analyze_course(waypoints, closest_waypoints, heading, steering_angle, speed)
    
    # Progress evaluation
    progress_reward = evaluate_progress(progress, steps)
    
    # Combine rewards
    total_reward = base_reward + track_position_reward + course_reward + progress_reward
    
    # Critical failure handling - immediate strong penalty if off track
    if not all_wheels_on_track:
        return 1e-3
    
    # Ensure minimum reward value
    total_reward = max(total_reward, 1e-3)
    
    return float(total_reward)


def calculate_track_position_reward(distance_from_center, track_width):
    """
    Reward function component that evaluates how well the car is positioned on the track
    Higher rewards closer to center line with exponential decay toward edges
    """
    # Normalize distance from center
    normalized_distance = distance_from_center / (track_width / 2)
    
    # Exponential reward decay as car moves away from center
    # Higher exponent (1/3) provides more gradual penalty than original function  
    position_reward = 2.0 * (1 - normalized_distance**(1/3))
    
    return position_reward


def analyze_course(waypoints, closest_waypoints, heading, steering_angle, speed):
    """
    Analyzes upcoming track segments to determine appropriate driving behavior
    and rewards accordingly
    """
    # Look ahead distances for different analyses
    short_look_ahead = 5
    long_look_ahead = 10
    
    # Detect if approaching a turn
    is_approaching_turn = detect_turn(waypoints, closest_waypoints, short_look_ahead, 15)
    is_on_straight = detect_straight(waypoints, closest_waypoints, long_look_ahead, 10)
    
    # Initialize course reward
    course_reward = 0.0
    
    # Reward for proper handling of turns
    if is_approaching_turn:
        # Reward slower speeds in turns
        if speed < 2.0:
            course_reward += 1.0
        
        # Penalize excessive speed in turns
        if speed > 3.0:
            course_reward -= 1.5
    
    # Reward for proper handling of straights
    elif is_on_straight:
        # Reward higher speeds on straights
        if speed > 2.5:
            course_reward += 1.5
        
        # Reward minimal steering on straights
        if abs(steering_angle) < 10:
            course_reward += 0.8
    

    # Penalize excessive steering anywhere
    if abs(steering_angle) > 25:
        course_reward -= 0.5
    
    return course_reward


def detect_turn(waypoints, closest_waypoints, look_ahead, threshold):
    """
    Detects if the upcoming track segment contains a significant turn
    """
    # Get current and future waypoints
    prev_point = waypoints[closest_waypoints[0]]
    next_point = waypoints[closest_waypoints[1]]
    
    # Calculate future point, handling edge case at end of track
    future_idx = min(len(waypoints) - 1, closest_waypoints[1] + look_ahead)
    future_point = waypoints[future_idx]
    
    # Calculate heading change to future waypoint
    current_heading = math.degrees(math.atan2(next_point[1] - prev_point[1], 
                                             next_point[0] - prev_point[0]))
    future_heading = math.degrees(math.atan2(future_point[1] - next_point[1], 
                                            future_point[0] - next_point[0]))
    
    # Compute heading difference
    heading_diff = abs(current_heading - future_heading)
    
    # Adjust for angle wraparound
    if heading_diff > 180:
        heading_diff = 360 - heading_diff
    
    # Return whether difference exceeds threshold
    return heading_diff > threshold


def detect_straight(waypoints, closest_waypoints, look_ahead, threshold):
    """
    Detects if the upcoming track segment is relatively straight
    """
    # Reuse the turn detection but invert the logic
    return not detect_turn(waypoints, closest_waypoints, look_ahead, threshold)


def evaluate_progress(progress, steps):
    """
    Provides rewards based on how efficiently the track is being completed
    """
    # Constants for progress calculation
    TARGET_STEPS = 500  # Expected steps to complete track
    
    # Calculate expected progress at current step
    expected_progress = (steps / TARGET_STEPS) * 100
    
    # If ahead of expected progress, provide bonus
    progress_reward = 0
    if progress > expected_progress:
        # Reward proportional to how far ahead of schedule
        progress_reward = 0.5 * (progress - expected_progress) / 100
    
    return progress_reward
