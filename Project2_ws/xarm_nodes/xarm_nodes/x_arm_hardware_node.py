#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

try:
    import xarm
except ImportError:
    xarm = None


class XArmHardwareNode(Node):
    def __init__(self):
        super().__init__('x_arm_hardware_node')
        self.arm = None

        self._connect_usb()

        # TODO(STUDENTS): Add your service servers here.
        # Example:
        # self.create_service(YourServiceType, 'service_name', self.handle_service_name)

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

        # TODO(STUDENTS): Hardware communications live here and in helper methods you add below.
        # Suggestions:
        # 1) Wrap low-level arm calls in methods (move_joint, set_gripper, read_state).
        # 2) Validate bounds before sending commands.
        # 3) Return clear success/failure info to service callbacks.


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
