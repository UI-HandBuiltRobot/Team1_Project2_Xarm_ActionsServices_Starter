# Xarm-Pose-Recorder

A Python application for recording and playing back xArm robot poses with gripper control. This tool enables you to record a 3x3 grid of poses and a drop-off position, then automatically replay these poses with coordinated gripper open/close operations.

## Prerequisites

- **Hardware**: xArm robot with USB connection
- **Python**: Python 3.7+
- **Dependencies**: 
  ```bash
  pip install xarm
  ```

## Project Files

- **Xarm_pose_recorder.py**: Records and calibrates robot poses for a 3x3 grid and drop-off location
- **Xarm_pose_playback.py**: Replays recorded poses with synchronized gripper control

## How to Use

### Step 1: Record Poses (Xarm_pose_recorder.py)

Run the pose recorder to capture your grid positions:

```bash
python3 Xarm_pose_recorder.py
```

The script uses a GUI with popup dialogs to guide you through the recording process:

#### Recording Sequence:

1. **Grid Box #1 (Gripper Closed)**
   - Fully close the gripper
   - Move the arm so the gripper tip touches the ground in grid box #1
   - Click OK to record the position

2. **Grid Boxes #2-#9**
   - For each remaining grid box, move the arm so the gripper tip touches the ground
   - Click OK to record, or Cancel to finish early
   - The recorder will guide you through boxes 2-9

3. **Drop-off Pose**
   - Position the arm at the desired drop-off location
   - Keep the gripper **closed** while recording
   - Click OK to record

4. **Calibrate Gripper Open Count**
   - Fully open the gripper
   - Click OK to record the gripper_open_count (servo 1 position)

#### Output


The script prints calibration data ready to copy/paste:

```
# ================= COPY/PASTE BELOW =================
gripper_closed_count = 715
gripper_open_count   = 177

POSITIONS = {
    0: [177, 500, 500, 500, 500, 500],
    1: [177, 498, 457, 132, 505, 498],
    ...
}

POSITION_DROP = [715, 866, 434, 712, 445, 1000]
# ================== COPY/PASTE ABOVE =================
```

**Copy these values from your terminal output** - you'll need them for playback.

### Step 2: Playback Poses (Xarm_pose_playback.py)

1. Open **Xarm_pose_playback.py** in a text editor

2. Locate the configuration section at the top of the file:
   ```python
   # ========== PASTE YOUR RECORDED VALUES BELOW ==========
   gripper_closed_count = 715
   gripper_open_count   = 177
   POSITIONS = { ... }
   POSITION_DROP = [...]
   # ========== END PASTED VALUES ==========
   ```

3. Replace these values with the data you copied from the recorder output

4. Connect the robot and run:
   ```bash
   python3 Xarm_pose_playback.py
   ```

#### Playback Sequence

For each recorded pose (0-9):
- Move to the position
- Close the gripper
- Open the gripper (ready for the next item)

Finally:
- Move to the drop-off position
- Open the gripper to release the item
- Close the gripper
- Return to home position

## Servo Configuration

The xArm uses 6 servos, each controlled by their servo ID:

- **Servo 1**: Gripper (servo_id=1)
  - Lower values = gripper closed
  - Higher values = gripper open
- **Servos 2-6**: Arm joints (servo_ids=2-6)

Position values are stored as lists in order: `[servo_1, servo_2, servo_3, servo_4, servo_5, servo_6]`

## Grid Layout

The script records a 3x3 grid represented by boxes 1-9:

```
Box 1  Box 2  Box 3
Box 4  Box 5  Box 6
Box 7  Box 8  Box 9
```

Position 0 (HOME): A default rest position with all servos at neutral values

## Troubleshooting

- **Connection Error**: Ensure the xArm is connected via USB and the `xarm` package is installed
- **Servo issues**: The recorder disables servos (arm goes limp) to allow manual positioning. If servos don't go limp, you can still proceed manually
- **Gripper calibration**: Make sure the gripper is fully closed/open when recording calibration values
