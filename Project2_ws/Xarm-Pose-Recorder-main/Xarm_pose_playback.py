#!/usr/bin/env python3
"""
xArm 1s Pose Playback

Plays back recorded poses with gripper control.
Close gripper at each pose, move to position, then open gripper.

To use:
1. Record poses using Xarm_pose_recorder.py
2. Copy the gripper_closed_count, gripper_open_count, POSITIONS, and POSITION_DROP
   from the recorder output below
3. Run this script
"""

import time

import xarm
# ================= COPY/PASTE BELOW =================
gripper_closed_count = 671
gripper_open_count   = 401

POSITIONS = {
    0: [500, 500, 500, 500, 500, 500],
    1: [401, 700, 151, 849, 457, 651],
    2: [401, 582, 161, 903, 535, 526],
    3: [401, 392, 147, 828, 467, 369],
    4: [401, 645, 182, 772, 411, 613],
    5: [401, 535, 144, 755, 401, 518],
    6: [401, 440, 147, 739, 390, 413],
    7: [401, 619, 169, 629, 306, 602],
    8: [401, 502, 194, 702, 343, 513],
    9: [401, 436, 209, 686, 334, 422],
}

POSITION_DROP = [671, 491, 86, 755, 478, 880]
# ================== COPY/PASTE ABOVE =================


def main():
    """Connect to arm and play back poses with gripper control."""
    
    # --- Connect ---
    try:
        arm = xarm.Controller("USB")
    except Exception as e:
        print(f"Failed to connect via USB: {e}")
        return 1
    
    print("Connected to xArm. Starting playback...\n")
    
    # --- Play through each pose ---
    for idx in sorted(POSITIONS.keys()):
        
        print(f"Moving to pose {idx}...")
        
        try:

            print(f"  Homing...")
            pose = [gripper_open_count, 500, 500, 500, 500, 500]
            pose_pairs = [[i + 1, pose[i]] for i in range(len(pose))]
            arm.setPosition(pose_pairs, duration=1000, wait=True)
            time.sleep(0.1)
            

            pose = POSITIONS[idx]
            # Move to pose - convert flat list to [servo_id, position] pairs
            print(f"  Moving to position...")
            pose_pairs = [[i + 1, pose[i]] for i in range(len(pose))]
            arm.setPosition(pose_pairs, duration=1000, wait=True)
            time.sleep(0.1)
            
            # Close gripper at pose
            print(f"  Closing gripper...")
            arm.setPosition(1, gripper_closed_count, duration=500, wait=True)
            time.sleep(0.1)
            
            # Open gripper
            print(f"  Opening gripper...")
            arm.setPosition(1, gripper_open_count, duration=500, wait=True)
            time.sleep(0.1)
            
         
        except Exception as e:
            print(f"Error at pose {idx}: {e}")
            return 1
        
        print(f"  Pose {idx} complete.\n")
    pose=POSITION_DROP
    print("Moving to drop position...")
    pose_pairs = [[i + 1, pose[i]] for i in range(len(pose))]
    arm.setPosition(pose_pairs, duration=2000, wait=True)
    # Open gripper at drop position
    print("Opening gripper at drop position...")
    arm.setPosition(1, gripper_open_count, duration=500, wait=True)
    # Slose gripper after drop
    time.sleep(0.5)
    print("Closing gripper...")
    arm.setPosition(1, gripper_closed_count, duration=500, wait=True)
    pose=[gripper_open_count, 500, 500, 500, 500, 500]
    pose_pairs = [[i + 1, pose[i]] for i in range(len(pose))]
    arm.setPosition(pose_pairs, duration=2000, wait=True)
    print("Playback complete!")
    arm.servoOff();
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
