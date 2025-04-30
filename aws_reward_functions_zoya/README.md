# AWS DeepRacer Model Experimentation

This file documents the experimentation and results for various reward function models trained for AWS DeepRacer. The models were evaluated on multiple tracks with different configurations to find the optimal balance between speed and stability.

## Overview

The experiments focused on:
- Different speed thresholds
- Various track types for training and evaluation
- Reward function optimizations
- Stability vs. speed trade-offs

## Models and Results

### Attempt 01
- **Speed Thresholds**: 0.5-1
- **Track Trained On**: Jennens-Clockwise
- **Tracks Evaluated On**: Jennens-Clockwise
- **Best Lap Time**: 01:20:000
- **Off-Tracks**: 1-2
- **Configuration**:
  - Turn threshold
  - No lookahead
  - Progress & step rewards
  - is_left_of_centre
  - all_wheels_on_track

### Attempt 02
- **Speed Thresholds**: 1-4
- **Track Trained On**: Jennens-Clockwise
- **Tracks Evaluated On**: Jennens-Clockwise, reinvent 2022-Clockwise
- **Best Lap Times**: 00:37:990, 00:37:670
- **Off-Tracks**: 3-4, 6-11
- **Configuration**:
  - Same as Attempt 01, plus:
  - Lookahead number
  - is_sharp_turn
  - Increased turn threshold

### Attempt 03 (Most Stable)
- **Speed Thresholds**: 0.5-1
- **Track Trained On**: Jennens-Clockwise
- **Tracks Evaluated On**: Jennens-Clockwise, DBro Super Raceway-Clockwise
- **Best Lap Times**: 01:19:000, 01:18:000
- **Off-Tracks**: 0-1, 2
- **Configuration**:
  - Same as Attempt 02, plus:
  - Lookahead array
  - approaching_turn
  - turn_severity
  - Different speeds for straights, turns and sharp turns

### Attempt 04/05
- **Speed Thresholds**: 2-4
- **Track Trained On**: Jennens-Clockwise
- **Tracks Evaluated On**: No evaluation, training graph too unstable
- **Notes**: Iterating on model 3 to get a higher speed

### Attempt 06 (Faster Version of 3)
- **Speed Thresholds**: 1-4
- **Track Trained On**: Jennens-Clockwise
- **Tracks Evaluated On**: Jennens-Clockwise
- **Best Lap Time**: 00:35:803
- **Off-Tracks**: 1-2
- **Configuration**:
  - Same as Attempt 03, but:
  - Kept min and max speed
  - Sharp turn, turn and straight speed
  - Altered penalties

### Attempt 07
- **Speed Thresholds**: 1-4
- **Track Trained On**: Jennens-Clockwise
- **Tracks Evaluated On**: Jennens-Clockwise
- **Best Lap Time**: 00:35:917
- **Off-Tracks**: 1-3
- **Configuration**:
  - Same as Attempt 06, plus:
  - Added more values to lookahead array

### Attempt 08
- **Speed Thresholds**: 1-4
- **Track Trained On**: Jennens-Clockwise
- **Tracks Evaluated On**: Jennens-Clockwise
- **Best Lap Time**: 00:44:533
- **Off-Tracks**: 5-7
- **Configuration**:
  - Started from model 03 again
  - Added one more lookahead point to the array
  - Adjusted speed thresholds for different track types

### Attempt 09
- **Speed Thresholds**: 1-4
- **Track Trained On**: Jennens-Clockwise
- **Tracks Evaluated On**: Jennens-Clockwise
- **Best Lap Time**: 00:45:273
- **Off-Tracks**: 2-5
- **Configuration**:
  - Started from model 03 again
  - Tried to make it faster

### Attempt 10
- **Speed Thresholds**: 1-4
- **Track Trained On**: DBro Super Raceway-Clockwise
- **Tracks Evaluated On**: DBro Super Raceway-Clockwise
- **Best Lap Time**: 00:47:621
- **Off-Tracks**: 4-7
- **Configuration**:
  - Same as model 03

### Attempt 11
- **Speed Thresholds**: 0.5-1
- **Track Trained On**: DBro Super Raceway-Clockwise
- **Tracks Evaluated On**: DBro Super Raceway-Clockwise
- **Best Lap Time**: 01:04:460
- **Off-Tracks**: 0
- **Configuration**:
  - Same as model 03
  - Adjusted for slower speed to improve stability

### Attempt 12
- **Speed Thresholds**: 1-4
- **Track Trained On**: DBro Super Raceway-Clockwise
- **Tracks Evaluated On**: DBro Super Raceway-Clockwise
- **Best Lap Time**: 00:40:481
- **Off-Tracks**: 2-5
- **Configuration**:
  - Same as model 06

### Attempt 13
- **Speed Thresholds**: 0.5-1
- **Track Trained On**: Jennens-Clockwise
- **Tracks Evaluated On**: Jennens-Clockwise
- **Best Lap Time**: 01:19:326
- **Off-Tracks**: 4-16
- **Configuration**:
  - Same as model 03

### Attempt 14
- **Speed Thresholds**: 0.5-2
- **Track Trained On**: Jennens-Clockwise
- **Tracks Evaluated On**: Jennens-Clockwise
- **Best Lap Time**: 00:46:525
- **Off-Tracks**: 0
- **Configuration**:
  - Same as model 03

### Attempt 15
- **Speed Thresholds**: 0.5-2
- **Track Trained On**: Catalunya-Clockwise
- **Tracks Evaluated On**: Catalunya-Clockwise, Jennens-Clockwise
- **Best Lap Times**: 00:54:398, 00:54:537
- **Off-Tracks**: 3-4, 0-4
- **Configuration**:
  - Cloned model 14
  - Trained on Catalunya (Jennens + Catalunya)

### Attempt 16
- **Speed Thresholds**: 0.5-1
- **Track Trained On**: Catalunya-Clockwise
- **Tracks Evaluated On**: Catalunya-Clockwise
- **Best Lap Time**: 01:10:998
- **Off-Tracks**: 1-3
- **Configuration**:
  - Cloned model 15
  - Trained on Catalunya
  - Made speed slower for stability

### Attempt 17
- **Speed Thresholds**: 0.5-2
- **Track Trained On**: Reinvent 2022-Clockwise
- **Tracks Evaluated On**: Forever Raceway-Counterclockwise, Reinvent 2022-Counterclockwise
- **Best Lap Times**: 00:28:733, 00:38:941
- **Off-Tracks**: 0-1, 1-3
- **Configuration**:
  - Cloned model 15
  - Trained on reinvent (Jennens + Catalunya + reinvent)

### Attempt 18
- **Speed Thresholds**: 0.5-2
- **Track Trained On**: Forever Raceway-Counterclockwise
- **Tracks Evaluated On**: Forever Raceway-Counterclockwise
- **Best Lap Time**: 00:20:737
- **Off-Tracks**: 0
- **Configuration**:
  - Same as model 03

### Attempt 19
- **Speed Thresholds**: 1-4
- **Track Trained On**: Catalunya-Clockwise
- **Tracks Evaluated On**: Catalunya-Clockwise
- **Best Lap Time**: 00:46:591
- **Off-Tracks**: 4-9
- **Configuration**:
  - Same as model 06

### Attempt 20
- **Speed Thresholds**: 0.5-2
- **Track Trained On**: Catalunya-Clockwise
- **Tracks Evaluated On**: Catalunya-Clockwise
- **Best Lap Time**: 01:02:669
- **Off-Tracks**: 4-5
- **Configuration**:
  - Same as model 06

### Attempt 21
- **Speed Thresholds**: 0.5-2
- **Track Trained On**: Catalunya-Clockwise
- **Tracks Evaluated On**: Catalunya-Clockwise
- **Best Lap Time**: 00:57:865
- **Off-Tracks**: 1-2
- **Configuration**:
  - Same as model 03

### Attempt 22
- **Speed Thresholds**: 0.5-2
- **Track Trained On**: Jennens-Clockwise
- **Tracks Evaluated On**: Jennens-Clockwise
- **Best Lap Time**: 01:05:203
- **Off-Tracks**: 1
- **Configuration**:
  - Cloned model 21
  - Trained on Jennens

### Attempt 23
- **Speed Thresholds**: 0.5-2
- **Track Trained On**: Reinvent 2022-Counterclockwise
- **Tracks Evaluated On**: Reinvent 2022-Counterclockwise, Reinvent 2022-Clockwise, Forever Raceway-Counterclockwise
- **Best Lap Times**: 00:38:941, 00:40:743, 00:28:733
- **Off-Tracks**: 1-3, 1, 0
- **Configuration**:
  - Cloned model 22
  - Trained on reInvent

## Key Findings

### Best Models by Performance

#### Most Stable Model
- **Model**: Attempt 03
- **Speed Thresholds**: 0.5-1
- **Best Lap Time**: ~01:19:000
- **Off-Tracks**: 0-1
- **Key Features**: Lookahead array, turn_severity, different speeds for different track conditions

#### Fastest Models with Good Stability
- **Model**: Attempt 06
- **Speed Thresholds**: 1-4
- **Best Lap Time**: 00:35:803
- **Off-Tracks**: 1-2
- **Key Features**: Optimized penalties, speed thresholds for different track conditions

#### Best Performance on Forever Raceway
- **Model**: Attempt 18
- **Speed Thresholds**: 0.5-2
- **Best Lap Time**: 00:20:737
- **Off-Tracks**: 0
- **Key Features**: Based on model 03 configuration

#### Most Versatile Model
- **Model**: Attempt 17
- **Speed Thresholds**: 0.5-2
- **Trained on**: Multiple tracks (Jennens + Catalunya + reinvent)
- **Best Lap Times**: 00:28:733 (Forever Raceway), 00:38:941 (Reinvent)
- **Off-Tracks**: 0-1, 1-3
- **Key Features**: Transfer learning from model 15

### Reward Function Evolution

1. **Basic Features (Attempt 01)**:
   - Turn threshold
   - Progress & step rewards
   - Track position monitoring

2. **Added Predictive Features (Attempt 02-03)**:
   - Lookahead capabilities
   - Turn detection and severity assessment
   - Speed differentiation based on track conditions

3. **Optimization Phase (Attempt 06-09)**:
   - Fine-tuning penalties
   - Expanding lookahead array
   - Balancing speed vs. stability

4. **Track Specialization (Attempt 10-23)**:
   - Adapting models to specific tracks
   - Transfer learning across tracks
   - Building generalized models through sequential training



