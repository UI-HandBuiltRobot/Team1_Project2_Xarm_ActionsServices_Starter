#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from xarm_pickup_interfaces.srv import MoveToGrid, GripControl, GrabCheck, MoveToDropoff, ServoOff

# from xarm_pickup_interfaces.srv import YourServiceType  # TODO(STUDENTS): Import your service types here.

try:
    import xarm
except ImportError:
    xarm = None


class XArmHardwareNode(Node):
    def __init__(self):
        super().__init__('x_arm_hardware_node')
        self.arm = None

        self._connect_usb()
        
        
        ###need to edit positions
        self.grid_positions = {
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

        self.dropoff_position = [683, 516, 52, 582, 343, 877]

        # TODO(STUDENTS): Add your service servers here. Make sure that all services are defined in the xarm_pickup_interfaces package and that you import them at the top of this file.
        # Example:
        # self.create_service(YourServiceType, 'service_name', self.service_callback)

        self.create_service(MoveToGrid,'move_to_grid', self.move_to_grid_callback)
        self.create_service(GripControl,'grip_control', self.grip_control_callback)
        self.create_service(GrabCheck,'grab_check', self.grab_check_callback)
        self.create_service(MoveToDropoff,'move_to_dropoff', self.move_to_dropoff_callback)
        self.create_service(ServoOff,'servo_off', self.servo_off_callback)
             
         
        self.get_logger().info('x_arm_hardware_node is running.')

    def _connect_usb(self):
        if xarm is None:
            self.get_logger().error('xarm Python library not found. Install it before running hardware control.')
            return

        try:
            self.arm = xarm.Controller('USB')
            self.get_logger().info('Connected to xArm over USB.')
        except Exception as exc:
            self.get_logger().error(f'Failed to connect to xArm over USB: {exc}')

    def move_to_grid_callback(self, request, response):

        if self.arm is None:
            response.success = False
            response.message = "Arm not connected."
            return response

        box_id = request.box_id

        if box_id not in self.grid_positions:
            response.success = False
            response.message = "Invalid box ID."
            return response

        try:
            joint_targets = self.grid_positions[box_id]
            self.arm.setPosition(*joint_targets, wait=True)

            response.success = True
            response.message = "Moved to grid box."
        except Exception as e:
            response.success = False
            response.message = str(e)

        return response
    
    
    def grip_control_callback(self, request, response):

        if self.arm is None:
            response.success = False
            return response

        try:
            if request.close:
                self.arm.closeGripper()
            else:
                self.arm.openGripper()

            response.success = True
        except Exception:
            response.success = False

        return response
    
    def grab_check_callback(self, request, response):

        if self.arm is None:
            response.object_detected = False
            return response

        try:
            gripper_position = self.arm.getGripperPosition()

            threshold = 200  # Tune this in lab

            response.object_detected = gripper_position > threshold
        except Exception:
            response.object_detected = False

        return response
    
    
    def move_to_dropoff_callback(self, request, response):

        if self.arm is None:
            response.success = False
            return response

        try:
            self.arm.setPosition(*self.dropoff_position, wait=True)
            response.success = True
        except Exception:
            response.success = False

        return response
   
    
   
    def servo_off_callback(self, request, response):

        if self.arm is None:
            response.success = False
            return response

        try:
            self.arm.servoOff()
            response.success = True
        except Exception:
            response.success = False

        return response
    # TODO(STUDENTS): Add your service callback methods here.
    # Suggestions:
    # 1) Validate inputs before sending commands (e.g. are joint angles within limits?).
    # 2) Return clear success/failure info to the caller via the response object.
    #
    # Example:
    # def service_callback(self, request, response):
    #     # ... perform arm action ...
    #     response.success = True
    #     return response


def main(args=None):
    rclpy.init(args=args)
    node = XArmHardwareNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
