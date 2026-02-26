# Project 2 -- Grid Search and Object Dropoff (ROS 2)

This repository contains the scaffolded ROS 2 workspace for **ME:5195 --
Hand Built Robot, Project 2**.

Students are responsible for implementing the action server logic and
service-based task decomposition required to perform grid-based object
retrieval using the HiWonder Xarm 1S.

------------------------------------------------------------------------

# Workspace Structure

    Project2_ws/
    │
    ├── xarm_nodes/
    │   ├── pickup_gui.py
    │   ├── x_arm_hardware_node.py
    │   └── ...
    │
    └── xarm_pickup_interfaces/
        ├── action/RetrieveItems.action
        └── srv/GridServicePlaceholder.srv

------------------------------------------------------------------------

# Packages

## 1️⃣ xarm_pickup_interfaces

This package defines all custom ROS 2 interfaces for the project.

### Action

`RetrieveItems.action`

#### Goal

    int32 num_items

#### Result

    int32 items_collected
    bool success
    string message

#### Feedback

    int32 current_box
    int32 items_collected
    string state

The action name expected in the graph is:

    retrieve_items

⚠️ Do not modify this action definition.

------------------------------------------------------------------------

## 2️⃣ xarm_nodes

This package contains several Python nodes.

### pickup_gui.py
This is a PyQt5-based action client GUI that will be used to initate the action (action client). When run, it:

-   Connects to action name: `retrieve_items`
-   Sends a goal (1--9 items)
-   Displays feedback
-   Allows cancellation

You can run the GUI by entering
``` bash
ros2 run xarm_nodes pickup_gui
```
into the terminal.

DO NOT modify the action client GUI.

### x_arm_hardware_node.py

This node interfaces with the physical Xarm hardware and should contain all hardware communications with the Xarm. It should contain:
-   Xarm object connected via USB
-   Servo commands
-   Gripper control
-   Motion execution logic

Students may modify or extend this node as needed.

------------------------------------------------------------------------

# What Students Must Implement

Students must implement:

-   A ROS 2 **Action Server** using the `RetrieveItems` interface
-   Service-based decomposition of tasks. These might include:
    -   Move to box
    -   Close gripper
    -   Check gripper
-   Continuous feedback publishing
-   Safe cancellation behavior

------------------------------------------------------------------------

# Expected System Behavior

1.  User enters number of items (1--9)
2.  Clicks "Call Action"
3.  Robot:
    -   Searches grid
    -   Grasps object
    -   Transports to dropoff
    -   Repeats until goal satisfied
4.  GUI displays live feedback
5.  Cancel button stops execution safely

------------------------------------------------------------------------

# Dependencies

-   ROS 2 (Humble or newer recommended)
-   rclpy
-   PyQt5

Install PyQt5 if needed:

``` bash
sudo apt install python3-pyqt5
```

------------------------------------------------------------------------

# Academic Integrity

All code must be your team's original implementation.\
You are responsible for understanding and debugging all code submitted.
