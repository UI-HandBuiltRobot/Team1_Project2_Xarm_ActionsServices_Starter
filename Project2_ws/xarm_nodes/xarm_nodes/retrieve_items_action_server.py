#!/usr/bin/env python3
"""
retrieve_items_action_server.py — Scaffold for the RetrieveItems action server.

TODO(STUDENTS): Implement the action server logic in this file.
You will need to:
  1. Define any service types you need and import them below.
  2. Create service clients in __init__ for each hardware service you call.
  3. Fill in goal_callback, cancel_callback, and execute_callback.
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from rclpy.action import CancelResponse, GoalResponse
from rclpy.executors import MultiThreadedExecutor

from xarm_pickup_interfaces.action import RetrieveItems
# from xarm_pickup_interfaces.srv import YourServiceType  # TODO(STUDENTS): Import your service types here.


class RetrieveItemsActionServer(Node):
    """Action server that executes a RetrieveItems goal."""

    def __init__(self):
        super().__init__('retrieve_items_action_server')

        # TODO(STUDENTS): Create service clients here for any hardware services you need.
        # Example:
        # self._your_client = self.create_client(YourServiceType, 'service_name')

        # ================= COPY/PASTE BELOW =================
gripper_closed_count = 671
gripper_open_count   = 401

POSITIONS = {
    0: [401, 500, 500, 500, 500, 500],
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

        goal_handle.succeed()
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
