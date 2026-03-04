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
gripper_closed_count = 683
gripper_open_count   = 404

POSITIONS = {
    0: [404, 500, 500, 500, 500, 500],
    1: [404, 649, 166, 857, 506, 649],
    2: [404, 548, 117, 852, 505, 514],
    3: [404, 400, 128, 799, 453, 373],
    4: [404, 630, 135, 715, 381, 599],
    5: [404, 542, 83, 668, 354, 520],
    6: [404, 392, 109, 689, 369, 401],
    7: [404, 612, 151, 612, 305, 597],
    8: [404, 512, 215, 728, 369, 511],
    9: [404, 473, 179, 654, 327, 431],
}

POSITION_DROP = [683, 516, 52, 582, 343, 877]
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
