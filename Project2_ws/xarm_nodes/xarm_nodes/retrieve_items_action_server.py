#!/usr/bin/env python3
"""
retrieve_items_action_server.py — Scaffold for the RetrieveItems action server.

TODO(STUDENTS): Implement the action server logic in this file.
You will need to:
  1. Define any service types you need and import them below.
  2. Create service clients in __init__ for each hardware service you call.
  3. Fill in goal_callback, cancel_callback, and execute_callback.
"""

from concurrent.futures import wait
from unittest import result

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from rclpy.action import CancelResponse, GoalResponse
from rclpy.executors import MultiThreadedExecutor

import time

from xarm_pickup_interfaces.action import RetrieveItems

# from xarm_pickup_interfaces.srv import YourServiceType  # TODO(STUDENTS): Import your service types here.
from xarm_pickup_interfaces.srv import MoveToGrid
from xarm_pickup_interfaces.srv import GripControl
from xarm_pickup_interfaces.srv import GrabCheck
from xarm_pickup_interfaces.srv import MoveToDropoff



class RetrieveItemsActionServer(Node):
    """Action server that executes a RetrieveItems goal."""

    def __init__(self):
        super().__init__('retrieve_items_action_server')

        # TODO(STUDENTS): Create service clients here for any hardware services you need.
        # Example:
        # self._your_client = self.create_client(YourServiceType, 'service_name')
        self.move_grid_client = self.create_client(MoveToGrid, 'move_to_grid')
        self.grip_client = self.create_client(GripControl, 'grip_control')
        self.check_client = self.create_client(GrabCheck, 'grab_check')
        self.dropoff_client = self.create_client(MoveToDropoff, 'move_to_dropoff')
        
        for client, name in [
            (self.move_grid_client, 'move_to_grid'),
            (self.grip_client, 'grip_control'),
            (self.check_client, 'grab_check'),
            (self.dropoff_client, 'move_to_dropoff'),
        ]:
            if not client.wait_for_service(timeout_sec=5.0):
                self.get_logger().error(f"Service '{name}' not available.")

        self._action_server = ActionServer(
            self,
            RetrieveItems,
            'retrieve_items',
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            execute_callback=self.execute_callback,
        )

        self.get_logger().info('retrieve_items_action_server is running.')

    def goal_callback(self, goal_request):
        
        
        """Accept or reject an incoming goal request.

        TODO(STUDENTS): Add any validation logic here (e.g. reject if num_items is out of range).
        Return GoalResponse.REJECT to refuse a goal before execution begins.
        """
        self.get_logger().info(f'Received goal: num_items={goal_request.num_items}')
        
        if goal_request.num_items < 1 or goal_request.num_items > 9:
            self.get_logger().warn('Invalid goal: num_items must be 1–9')
            return GoalResponse.REJECT
        
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        """Accept or reject a cancel request for an active goal.

        TODO(STUDENTS): Return CancelResponse.REJECT if cancellation should be refused.
        """
        self.get_logger().info('Received cancel request.')
        
        return CancelResponse.ACCEPT

    async def execute_callback(self, goal_handle):
        """Execute the RetrieveItems goal.

        This method is called in its own thread by the MultiThreadedExecutor,
        so blocking calls are safe here. It must publish feedback periodically
        and return a populated Result when finished.

        TODO(STUDENTS): Implement the pick-and-place loop here.
        """
        self.get_logger().info('Executing goal...')

        feedback_msg = RetrieveItems.Feedback()
        result = RetrieveItems.Result()

        # TODO(STUDENTS): Implement your item retrieval loop.
        # A typical loop might:
        #   1. Determine the next grid box to visit.
        #   2. Call a hardware service to move the arm.
        #   3. Call a hardware service to operate the gripper.
        #   4. Publish feedback after each step.
        #   5. Check for cancellation and abort cleanly if requested.
        #
        # --- Calling a service with await ---
        # request = YourServiceType.Request()
        # request.box_index = current_box
        # response = await self._your_client.call_async(request)
        # if not response.success:
        #     self.get_logger().error(f'Service call failed: {response.message}')
        #
        # --- Publishing feedback ---
        # feedback_msg.state = 'searching'
        # feedback_msg.current_box = current_box
        # feedback_msg.items_collected = items_so_far
        # goal_handle.publish_feedback(feedback_msg)
        #
        # --- Checking for cancellation ---
        # if goal_handle.is_cancel_requested:
        #     goal_handle.canceled()
        #     result.success = False
        #     result.message = 'Goal cancelled.'
        #     return result
        requested_items = goal_handle.request.num_items
        collected = 0
        grid_boxes = list(range(1, 10))
        



        for box_id in grid_boxes:
            # cancellation
            if goal_handle.is_cancel_requested:
                self.get_logger().info('Goal cancelled.')
                goal_handle.canceled()
                result.success = False
                result.items_collected = collected
                result.message = 'Goal cancelled.'
                return result

            # 0) Open gripper before moving (prevents pushing things)
            feedback_msg.state = 'Opening gripper'
            feedback_msg.current_box = box_id
            feedback_msg.items_collected = collected
            goal_handle.publish_feedback(feedback_msg)

            open_req = GripControl.Request()
            open_req.close = False
            open_res = await self.grip_client.call_async(open_req)
            if open_res is None or not open_res.success:
                self.get_logger().error(f"Failed to open gripper before box {box_id}")
                continue

            time.sleep(0.2) 

            # 1) Go home BEFORE each box
            feedback_msg.state = 'Going home'
            feedback_msg.current_box = box_id
            feedback_msg.items_collected = collected
            goal_handle.publish_feedback(feedback_msg)

            home_req = MoveToGrid.Request()
            home_req.box_id = 0
            home_res = await self.move_grid_client.call_async(home_req)
            if home_res is None or not home_res.success:
                self.get_logger().error(f"Home move failed: {getattr(home_res, 'message', '')}")
                continue

            # 2) Move to target box
            feedback_msg.state = 'Moving to box'
            feedback_msg.current_box = box_id
            feedback_msg.items_collected = collected
            goal_handle.publish_feedback(feedback_msg)

            move_req = MoveToGrid.Request()
            move_req.box_id = box_id
            move_res = await self.move_grid_client.call_async(move_req)

            if move_res is None:
                self.get_logger().error("move_to_grid returned None")
                continue
            if not move_res.success:
                self.get_logger().error(f"Move failed at box {box_id}: {move_res.message}")
                continue

            # 3) Close gripper
            feedback_msg.state = 'Closing gripper'
            feedback_msg.current_box = box_id
            feedback_msg.items_collected = collected
            goal_handle.publish_feedback(feedback_msg)

            grip_req = GripControl.Request()
            grip_req.close = True
            grip_res = await self.grip_client.call_async(grip_req)
            if grip_res is None or not grip_res.success:
                self.get_logger().error(f"Gripper close failed at box {box_id}")
                continue

            time.sleep(0.5)  # settle time

            # 4) Check grasp
            feedback_msg.state = 'Checking grasp'
            feedback_msg.current_box = box_id
            feedback_msg.items_collected = collected
            goal_handle.publish_feedback(feedback_msg)

            check_req = GrabCheck.Request()
            check_res = await self.check_client.call_async(check_req)
            if check_res is None:
                self.get_logger().error("grab_check returned None")
                continue

            if not check_res.object_detected:
                # open and continue to next box
                open_req = GripControl.Request()
                open_req.close = False
                await self.grip_client.call_async(open_req)
                continue


            # ---- SUCCESS PATH: grabbed something ----

            # (A) Go home before dropoff (safe retract)
            feedback_msg.state = 'Going home (with object)'
            feedback_msg.current_box = box_id
            feedback_msg.items_collected = collected
            goal_handle.publish_feedback(feedback_msg)

            home_req = MoveToGrid.Request()
            home_req.box_id = 0
            home_res = await self.move_grid_client.call_async(home_req)
            if home_res is None or not home_res.success:
                # Don't "continue" here, because you are holding something (maybe).
                self.get_logger().error(f"Home move failed before dropoff: {getattr(home_res, 'message', '')}")
                # proceed cautiously to dropoff anyway

            time.sleep(0.2)

            # (B) Dropoff
            feedback_msg.state = 'Moving to dropoff'
            feedback_msg.current_box = box_id
            feedback_msg.items_collected = collected
            goal_handle.publish_feedback(feedback_msg)

            drop_res = await self.dropoff_client.call_async(MoveToDropoff.Request())
            # If MoveToDropoff has success/message, check it here.

            time.sleep(0.2)

            # (C) Open gripper to release
            feedback_msg.state = 'Releasing'
            feedback_msg.current_box = box_id
            feedback_msg.items_collected = collected
            goal_handle.publish_feedback(feedback_msg)

            open_req = GripControl.Request()
            open_req.close = False
            await self.grip_client.call_async(open_req)

            collected += 1
            feedback_msg.state = 'Item collected'
            feedback_msg.current_box = box_id
            feedback_msg.items_collected = collected
            goal_handle.publish_feedback(feedback_msg)


            if collected >= requested_items:
                break
            
        result.items_collected = collected

        if collected == requested_items:
            goal_handle.succeed()
            result.success = True
            result.message = 'Successfully collected requested items.'
        
        else:
            goal_handle.abort()
            result.success = False
            result.message = 'Not enough objects found in grid.'
        
        
            # ---- Final: return to home position ----
        try:
            feedback_msg.state = 'Returning home'
            feedback_msg.current_box = -1
            feedback_msg.items_collected = collected
            goal_handle.publish_feedback(feedback_msg)

            home_req = MoveToGrid.Request()
            home_req.box_id = 0
            home_res = await self.move_grid_client.call_async(home_req)

            if home_res is None or not home_res.success:
                self.get_logger().error(f"Final home move failed: {getattr(home_res, 'message', '')}")
        except Exception as e:
            self.get_logger().error(f"Exception while returning home: {e}")


        return result


def main(args=None):
    rclpy.init(args=args)
    node = RetrieveItemsActionServer()

    # MultiThreadedExecutor allows goal, cancel, and execute callbacks to run
    # concurrently — required when the execute_callback blocks or uses await.
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
