#!/usr/bin/env python3
"""
xArm 1s Pose Recorder (pip install xarm)

Records:
- POSITIONS: dict[int, list[int]] for grid poses, with entry 0 = HOME
- POSITION_DROP: list[int] for drop-off pose

Rules:
- gripper_closed_count recorded when gripper is fully closed (servo 1)
- gripper_open_count recorded when gripper is fully open (servo 1)
- All POSITIONS[*][0] replaced with gripper_open_count
- POSITION_DROP[0] set to gripper_closed_count
"""

import time

import xarm

# ---------- GUI (tkinter) ----------
import tkinter as tk
from tkinter import messagebox


SERVO_IDS = [1, 2, 3, 4, 5, 6]


def ask_ok_cancel(title, msg):
    """Return True if OK, False if Cancel."""
    return messagebox.askokcancel(title, msg)


def ask_yes_no(title, msg):
    """Return True if Yes, False if No."""
    return messagebox.askyesno(title, msg)


def read_all(arm):
    """Read all 6 servo positions as a list in servo-id order."""
    vals = [arm.getPosition(servo_id) for servo_id in SERVO_IDS]
    # Some libs return tuples/lists; ensure plain ints.
    return [int(v) for v in vals]


def main():
    # Create hidden Tk root so message boxes work cleanly
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    # --- Connect ---
    try:
        arm = xarm.Controller("USB")
    except Exception as e:
        messagebox.showerror("Connection Error", f"Failed to connect via USB:\n\n{e}")
        return 1

    # --- Initialize outputs ---
    POSITIONS = {0: [500, 500, 500, 500, 500, 500]}
    POSITION_DROP = None

    # --- Disable all servos (go limp) ---
    try:
        arm.servoOff()
    except Exception as e:
        messagebox.showwarning(
            "Servo Off Warning",
            f"Could not disable servos with arm.servoOff().\n"
            f"You can still proceed, but the arm may fight you.\n\n{e}",
        )

    time.sleep(0.2)

    # --- Record grid poses with gripper CLOSED ---
    if not ask_ok_cancel(
        "Pose Recorder",
        "Step 1:\n"
        "1) CLOSE the gripper completely.\n"
        "2) Move the arm so the gripper TIP touches the ground in GRID BOX #1.\n\n"
        "Click OK to record Box #1 (Cancel to quit)."
    ):
        return 0

    pose1 = read_all(arm)
    gripper_closed_count = int(pose1[0])  # servo 1
    POSITIONS[1] = pose1

    messagebox.showinfo(
        "Recorded",
        f"Recorded Box #1.\n\n"
        f"Captured gripper_closed_count = {gripper_closed_count}\n\n"
        "Next you will record boxes #2..#9.\n"
        "You can stop early by clicking 'No' when asked to continue."
    )

    # Record boxes 2..9
    for idx in range(2, 10):
        if not ask_ok_cancel(
            f"Position for Box #{idx}",
            f"Move the arm so the gripper TIP touches the ground in GRID BOX #{idx}.\n\n"
            "Click OK to record (Cancel to finish recording)."
        ):
            break

        POSITIONS[idx] = read_all(arm)
        messagebox.showinfo("Recorded", f"Recorded Box #{idx}.")

    # --- Drop-off pose (with gripper closed) ---
    if not ask_ok_cancel(
        "Drop-off Pose",
        "Step 2:\n"
        "Position the arm at the DROP-OFF location.\n\n"
        "IMPORTANT: Keep the gripper CLOSED.\n\n"
        "Click OK to record drop-off pose (Cancel to quit)."
    ):
        return 0

    POSITION_DROP = read_all(arm)

    # --- Record gripper OPEN count ---
    if not ask_ok_cancel(
        "Open Gripper",
        "Step 3:\n"
        "OPEN the gripper completely.\n\n"
        "Click OK to record gripper_open_count (servo 1)."
    ):
        return 0

    gripper_open_count = int(arm.getPosition(1))

    # --- Post-process poses per your rules ---
    # Set all grid poses to use OPEN gripper value in index 0
    for k, pose in list(POSITIONS.items()):
        if len(pose) != 6:
            raise RuntimeError(f"Pose at key {k} is not length 6: {pose}")
        pose[0] = gripper_open_count
        POSITIONS[k] = pose

    # Set drop pose to use CLOSED gripper value
    POSITION_DROP[0] = gripper_closed_count

    # --- Print copy/paste-ready output ---
    print("\n\n# ================= COPY/PASTE BELOW =================")
    print(f"gripper_closed_count = {gripper_closed_count}")
    print(f"gripper_open_count   = {gripper_open_count}\n")

    print("POSITIONS = {")
    for k in sorted(POSITIONS.keys()):
        print(f"    {k}: {POSITIONS[k]},")
    print("}\n")

    print(f"POSITION_DROP = {POSITION_DROP}")
    print("# ================== COPY/PASTE ABOVE =================\n")

    messagebox.showinfo(
        "Done",
        "All requested values recorded.\n\n"
        "Copy POSITIONS and POSITION_DROP from your terminal output."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())