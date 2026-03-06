#!/usr/bin/env python3
import time
import rclpy
from rclpy.node import Node
from xarm_pickup_interfaces.srv import MoveToGrid, GripControl, GrabCheck, MoveToDropoff, ServoOff
import traceback
from std_srvs.srv import Trigger
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
        
        self.GRIP_SERVO_ID = 1      
        self.GRIP_OPEN = 323
        self.GRIP_CLOSED = 727

        self.empty_close_baseline = None
        self.detect_margin = 12.0  # tune later


        self.grid_positions  = {
            0: [323, 500, 500, 500, 500, 500],
            1: [323, 656, 200, 829, 466, 617],
            2: [323, 526, 151, 808, 462, 513],
            3: [323, 416, 157, 777, 425, 391],
            4: [323, 621, 142, 625, 317, 587],
            5: [323, 531, 193, 739, 383, 512],
            6: [323, 454, 109, 585, 299, 417],
            7: [323, 611, 228, 617, 282, 567],
            8: [323, 525, 183, 572, 269, 510],
            9: [323, 465, 164, 519, 243, 427],
        }

        self.dropoff_position = [727, 466, 95, 673, 437, 799]
# ================== COPY/PASTE ABOVE =================

        '''# From Pose Recorder --
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

        self.dropoff_position = [683, 516, 52, 582, 343, 877]'''

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
            targets = self.grid_positions[box_id]  # list of 6 servo positions (0..1000)
            JOINT_IDS = [2, 3, 4, 5, 6]      # arm joints only
            # targets is length 6: [grip, j2, j3, j4, j5, j6]
            joint_targets = targets[1:]      # drop gripper value

            pairs = [[JOINT_IDS[i], joint_targets[i]] for i in range(5)]
            self.arm.setPosition(pairs, duration=1500, wait=True)

            response.success = True
            response.message = "Moved to grid box."
        except Exception as e:
            response.success = False
            response.message = f"Error occurred: {e}"

        return response
    
    
    def grip_control_callback(self, request, response):
        if self.arm is None:
            response.success = False
            return response

        try:
            target = self.GRIP_CLOSED if request.close else self.GRIP_OPEN

            # Command gripper servo directly
            self.arm.setPosition(self.GRIP_SERVO_ID, target, duration=500, wait=True)

            response.success = True
        except Exception as e:
            self.get_logger().error(f'Gripper control failed: {e}')
            response.success = False

        return response
    
    def grab_check_callback(self, request, response):
        if self.arm is None:
            response.object_detected = False
            return response

        try:
            time.sleep(0.2)

            raw = self.arm.getPosition(self.GRIP_SERVO_ID)

            # 1) None
            if raw is None:
                self.get_logger().error("[GrabCheck] getPosition returned None")
                response.object_detected = False
                return response

            # 2) list/tuple
            if isinstance(raw, (list, tuple)):
                if len(raw) == 0:
                    self.get_logger().error("[GrabCheck] getPosition returned empty list/tuple")
                    response.object_detected = False
                    return response
                pos = float(raw[-1])

            # 3) anything else (number-like)
            else:
                try:
                    pos = float(raw)
                except Exception:
                    self.get_logger().error(f"[GrabCheck] getPosition returned non-numeric type: {type(raw)} val={raw}")
                    response.object_detected = False
                    return response

            # Learn baseline once (assumes first check happens when empty)
            if self.empty_close_baseline is None:
                self.empty_close_baseline = pos
                self.get_logger().warn(f"[GrabCheck] Learned empty-close baseline: {pos:.1f}")
                response.object_detected = False
                return response

            diff = abs(pos - self.empty_close_baseline)
            response.object_detected = diff > self.detect_margin

            self.get_logger().info(
                f"[GrabCheck] pos={pos:.1f}, baseline={self.empty_close_baseline:.1f}, "
                f"diff={diff:.1f}, margin={self.detect_margin:.1f}, detected={response.object_detected}"
            )

        except Exception as e:
            self.get_logger().error(f"Grab check failed: {e}")
            self.get_logger().error(traceback.format_exc())
            response.object_detected = False

        return response
    
    def move_to_dropoff_callback(self, request, response):
        if self.arm is None:
            response.success = False
            return response

        try:
            targets = self.dropoff_position
            JOINT_IDS = [2, 3, 4, 5, 6]
            joint_targets = targets[1:]
            pairs = [[JOINT_IDS[i], joint_targets[i]] for i in range(5)]
            self.arm.setPosition(pairs, duration=1500, wait=True)
            response.success = True
        except Exception as e:
            self.get_logger().error(f"Dropoff move failed: {e}")
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
