import math
def reward_function(params):
    # Read input parameters
    speed = params['speed']
    steering_angle = params['steering_angle']
    all_wheels_on_track = params['all_wheels_on_track']
    distance_from_center = params['distance_from_center']
    track_width = params['track_width']
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    off_track = params['is_offtrack']
    # ---------------------------
    # Step 1: Base reward on speed
    # ---------------------------
    reward = speed  # Faster is generally better
    
    # ---------------------------
    # Step 2: Penalize steering (higher penalty for small angles)
    # ---------------------------
    abs_steering = abs(steering_angle)
    if abs_steering < 15:
        # Higher penalty for small angles (wavering)
        steering_penalty = 1 - (0.5 * (15 - abs_steering) / 15)
    else:
        # Lower penalty for large angles (necessary for turns)
        steering_penalty = 1 - (0.3 * min(abs_steering, 30) / 30)
        
    reward *= steering_penalty
    
    # ---------------------------
    # Step 3: Estimate corner radius
    # ---------------------------
    def calculate_distance(p1, p2):
        return math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    
    def calculate_area(a, b, c):
        s = (a + b + c) / 2
        return math.sqrt(max(s * (s - a) * (s - b) * (s - c), 0))
    
    def get_corner_radius(waypoints, closest_waypoints):
        behind_index = closest_waypoints[0]
        center_index = closest_waypoints[1]
        next_index = (center_index + 1) % len(waypoints)
        A = waypoints[behind_index]
        B = waypoints[center_index]
        C = waypoints[next_index]
        a = calculate_distance(B, C)
        b = calculate_distance(A, C)
        c = calculate_distance(A, B)
        area = calculate_area(a, b, c)
        if area == 0:
            return float('inf')  # Straight line = infinite radius
        return (a * b * c) / (4 * area)
    
    radius = get_corner_radius(waypoints, closest_waypoints)
    
    # ---------------------------
    # Step 4: Calculate max safe speed (centripetal acceleration limit)
    # ---------------------------
    if radius == float('inf'):
        V_max = 4.0  # Straight = allow high speed (tune as per DeepRacer limits)
    else:
        g = 9.8  # m/s²
        friction_coeff = 1.5  # You can tune this
        V_max = math.sqrt(friction_coeff * radius * g)
    
    # Normalize V_max to range (0, 4.0) based on DeepRacer speeds
    V_max = min(V_max, 4.0)
    
    # ---------------------------
    # Step 5: Reward driving close to the ideal speed
    # ---------------------------
    speed_ratio = speed / V_max
    speed_reward = max(0.0, 1 - abs(1 - speed_ratio))  # Peak reward at speed = V_max
    reward *= speed_reward
    
    # ---------------------------
    # Step 6: Giving a very small reward if the car is off track
    # ---------------------------
    
    if off_track:
        reward = 0.1
    
    return float(max(reward, 1e-3))