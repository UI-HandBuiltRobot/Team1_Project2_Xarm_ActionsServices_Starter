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
from xarm_pickup_interfaces.srv import ServoOff



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
        self.servo_off_client = self.create_client(ServoOff, 'servo_off')
        
        self._cancel_requested = False

        for client, name in [
            (self.move_grid_client, 'move_to_grid'),
            (self.grip_client, 'grip_control'),
            (self.check_client, 'grab_check'),
            (self.dropoff_client, 'move_to_dropoff'),
            (self.servo_off_client, 'servo_off'),
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
        self.get_logger().info('Received cancel request.')
        self._cancel_requested = True
        return CancelResponse.ACCEPT

# Original execute callback - no retry -------
    """async def execute_callback(self, goal_handle):
        ""Execute the RetrieveItems goal.

        This method is called in its own thread by the MultiThreadedExecutor,
        so blocking calls are safe here. It must publish feedback periodically
        and return a populated Result when finished.

        TODO(STUDENTS): Implement the pick-and-place loop here.
        ""
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


        return result"""
    
    ## UPDATED execute callback with retry logic -----

    async def execute_callback(self, goal_handle):
        self.get_logger().info("Executing goal...")
        self._cancel_requested = False

        feedback_msg = RetrieveItems.Feedback()
        result = RetrieveItems.Result()

        requested_items = goal_handle.request.num_items
        collected = 0

        # Retry settings
        max_passes = 2
        settle_open = 0.2
        settle_close = 0.5
        settle_move = 0.2

        boxes_pass1 = list(range(1, 10))
        boxes_pass2 = list(range(9, 0, -1))
        passes = [boxes_pass1, boxes_pass2]

        last_pub = 0.0
        cancel_pending = False  # <-- key: "soft cancel" flag

        def publish_ui(state: str, box: int, min_interval: float = 0.06):
            nonlocal last_pub, collected
            feedback_msg.state = state
            feedback_msg.current_box = box
            feedback_msg.items_collected = collected
            goal_handle.publish_feedback(feedback_msg)

            now = time.time()
            dt = now - last_pub
            if dt < min_interval:
                time.sleep(min_interval - dt)
            last_pub = time.time()

        async def call_servo_off():
            req = ServoOff.Request()
            return await self.servo_off_client.call_async(req)

        async def await_step(future, step_name: str, poll_s: float = 0.05):
            nonlocal cancel_pending

            while not future.done():
                if self._cancel_requested and not cancel_pending:
                    cancel_pending = True
                    self.get_logger().warn("Cancel flag detected in await_step")
                    publish_ui("Cancel requested: finishing current motion", -1)
                time.sleep(poll_s)

            return future.result()

        async def do_cancel_shutdown():
            """
            Called after a step completes, once cancel_pending is True.
            Must: stop new attempts + servoOff + mark goal canceled.
            """
            publish_ui("Cancelling: turning servos off", -1)

            try:
                off_res = await call_servo_off()
                if off_res is None or not getattr(off_res, "success", True):
                    self.get_logger().error("servo_off call failed or returned unsuccessful")
            except Exception as e:
                self.get_logger().error(f"servo_off exception: {e}")

            goal_handle.canceled()
            result.success = False
            result.items_collected = collected
            result.message = "Cancelled by user. Current motion finished, servos turned off."
            publish_ui("CANCELLED", -1)
            return result

        async def attempt_box(box_id: int, pass_idx: int) -> str:
            """
            Returns:
            'continue' -> go to next box
            'picked'   -> picked an object
            'cancel'   -> cancel_pending True after finishing a step
            'error'    -> service failure
            """

            # Step 0: Open gripper (box N/A)
            publish_ui(f"Pass {pass_idx}/{max_passes}: Opening gripper", -1)
            open_req = GripControl.Request()
            open_req.close = False
            open_res = await await_step(self.grip_client.call_async(open_req), "open_grip")
            if open_res is None or not open_res.success:
                publish_ui(f"Pass {pass_idx}/{max_passes}: ERROR opening gripper", -1)
                return "error"
            time.sleep(settle_open)
            if cancel_pending:
                return "cancel"

            # Step 1: Home (box N/A)
            publish_ui(f"Pass {pass_idx}/{max_passes}: Going home", -1)
            home_req = MoveToGrid.Request()
            home_req.box_id = 0
            home_res = await await_step(self.move_grid_client.call_async(home_req), "home")
            if home_res is None or not home_res.success:
                publish_ui(f"Pass {pass_idx}/{max_passes}: ERROR going home", -1)
                return "error"
            time.sleep(settle_move)
            if cancel_pending:
                return "cancel"

            # Step 2: Move to box (NOW show box_id)
            publish_ui(f"Pass {pass_idx}/{max_passes}: Moving to box", box_id)
            move_req = MoveToGrid.Request()
            move_req.box_id = box_id
            move_res = await await_step(self.move_grid_client.call_async(move_req), "move_box")
            if move_res is None or not move_res.success:
                publish_ui(f"Pass {pass_idx}/{max_passes}: ERROR moving to box", box_id)
                return "error"
            time.sleep(settle_move)
            if cancel_pending:
                return "cancel"

            # Step 3: Close gripper
            publish_ui(f"Pass {pass_idx}/{max_passes}: Closing gripper", box_id)
            close_req = GripControl.Request()
            close_req.close = True
            close_res = await await_step(self.grip_client.call_async(close_req), "close_grip")
            if close_res is None or not close_res.success:
                publish_ui(f"Pass {pass_idx}/{max_passes}: ERROR closing gripper", box_id)
                return "error"
            time.sleep(settle_close)
            if cancel_pending:
                return "cancel"

            # Step 4: Grab check
            publish_ui(f"Pass {pass_idx}/{max_passes}: Checking grasp", box_id)
            check_req = GrabCheck.Request()
            check_res = await await_step(self.check_client.call_async(check_req), "grab_check")
            if check_res is None:
                publish_ui(f"Pass {pass_idx}/{max_passes}: ERROR grab_check None", box_id)
                return "error"
            if cancel_pending:
                return "cancel"

            if not check_res.object_detected:
                publish_ui(f"Pass {pass_idx}/{max_passes}: No object (continue)", box_id)
                # Open gripper and continue
                _ = await await_step(self.grip_client.call_async(open_req), "open_after_fail")
                time.sleep(settle_open)
                if cancel_pending:
                    return "cancel"
                return "continue"

            # SUCCESS: retract home
            publish_ui(f"Pass {pass_idx}/{max_passes}: Object detected! Going home", box_id)
            _ = await await_step(self.move_grid_client.call_async(home_req), "home_with_obj")
            time.sleep(settle_move)
            if cancel_pending:
                return "cancel"

            # Dropoff
            publish_ui(f"Pass {pass_idx}/{max_passes}: Moving to dropoff", box_id)
            drop_res = await await_step(self.dropoff_client.call_async(MoveToDropoff.Request()), "dropoff")
            if drop_res is None:
                publish_ui(f"Pass {pass_idx}/{max_passes}: ERROR dropoff None", box_id)
                return "error"
            time.sleep(settle_move)
            if cancel_pending:
                return "cancel"

            # Release
            publish_ui(f"Pass {pass_idx}/{max_passes}: Releasing", box_id)
            _ = await await_step(self.grip_client.call_async(open_req), "release")
            time.sleep(settle_open)
            if cancel_pending:
                return "cancel"

            return "picked"

        # ---------------- MAIN PASS LOOP ----------------
        for pass_idx in range(1, max_passes + 1):
            if collected >= requested_items:
                break

            publish_ui(f"Starting pass {pass_idx}/{max_passes}", -1)

            for box_id in passes[pass_idx - 1]:
                if collected >= requested_items:
                    break

                outcome = await attempt_box(box_id, pass_idx)

                if outcome == "cancel":
                    return await do_cancel_shutdown()

                if outcome == "picked":
                    collected += 1
                    publish_ui(f"Collected {collected}/{requested_items}", box_id)

                # continue/error just proceeds

                if collected >= requested_items:
                    break

            if pass_idx < max_passes and collected < requested_items:
                publish_ui(f"Retry needed: {collected}/{requested_items}. Starting pass {pass_idx+1}/{max_passes}", -1)

            if cancel_pending:
                return await do_cancel_shutdown()

        # ---------------- FINISH / RESULT ----------------
        result.items_collected = collected

        if collected >= requested_items:
            goal_handle.succeed()
            result.success = True
            result.message = f"Successfully collected {collected}/{requested_items}."
            publish_ui("SUCCESS", -1)
        else:
            goal_handle.abort()
            result.success = False
            result.message = f"Not enough objects found. Collected {collected}/{requested_items} after {max_passes} passes."
            publish_ui("FAILED", -1)

        # Return home at end (best effort)
        publish_ui("Returning home", -1)
        home_req_final = MoveToGrid.Request()
        home_req_final.box_id = 0
        _ = await await_step(self.move_grid_client.call_async(home_req_final), "final_home")

        # If cancel happened during final_home, still satisfy servoOff requirement
        if cancel_pending:
            return await do_cancel_shutdown()

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
