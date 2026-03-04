#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from xarm_pickup_interfaces.srv import CloseGripper, MoveToDropoff, MoveToGrid, OpenGripper

try:
    import xarm
except ImportError:
    xarm = None


class XArmHardwareNode(Node):
    def __init__(self):
        super().__init__('x_arm_hardware_node')
        self.arm = None

        self._connect_usb()

        # TODO(STUDENTS): Add your service servers here. Make sure that all services are defined in the xarm_pickup_interfaces package and that you import them at the top of this file.
        # Example:
        # self.create_service(YourServiceType, 'service_name', self.service_callback)
        self.create_service(MoveToGrid, 'move_to_grid', self.move_to_grid_callback)
        self.create_service(MoveToDropoff, 'move_to_dropoff', self.move_to_dropoff_callback)
        self.create_service(OpenGripper, 'open_gripper', self.open_gripper_callback)
        self.create_service(CloseGripper, 'close_gripper', self.close_gripper_callback)


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
