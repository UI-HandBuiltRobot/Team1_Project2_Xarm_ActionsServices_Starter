#!/usr/bin/env python3

import sys
import threading

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QGridLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from xarm_pickup_interfaces.action import RetrieveItems


class UiBridge(QObject):
    status_text = pyqtSignal(str)
    current_state = pyqtSignal(str)
    current_box = pyqtSignal(str)
    items_collected = pyqtSignal(str)
    goal_active = pyqtSignal(bool)


class XarmPickupGuiClient(Node):
    def __init__(self, bridge: UiBridge):
        super().__init__('xarm_pickup_gui_client')
        self.bridge = bridge
        self.action_client = ActionClient(self, RetrieveItems, 'retrieve_items')
        self.goal_handle = None
        self._goal_lock = threading.Lock()

    def send_goal(self, num_items: int):
        if not self.action_client.wait_for_server(timeout_sec=2.0):
            self.bridge.status_text.emit('Server not available')
            self.bridge.goal_active.emit(False)
            return

        goal_msg = RetrieveItems.Goal()
        goal_msg.num_items = num_items

        self.bridge.status_text.emit(f'Sending goal: num_items={num_items}')
        send_future = self.action_client.send_goal_async(goal_msg, feedback_callback=self._feedback_callback)
        send_future.add_done_callback(self._goal_response_callback)

    def _goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.bridge.status_text.emit('Goal rejected')
            self.bridge.goal_active.emit(False)
            return

        with self._goal_lock:
            self.goal_handle = goal_handle

        self.bridge.status_text.emit('Goal accepted')
        self.bridge.goal_active.emit(True)

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_callback)

    def _feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        box_text = str(feedback.current_box) if feedback.current_box >= 0 else 'N/A'

        self.bridge.current_state.emit(feedback.state)
        self.bridge.current_box.emit(box_text)
        self.bridge.items_collected.emit(str(feedback.items_collected))
        self.bridge.status_text.emit('Feedback received')

    def _result_callback(self, future):
        result = future.result().result
        self.bridge.status_text.emit(
            f'Done: success={result.success} items={result.items_collected}'
        )
        self.bridge.goal_active.emit(False)

        with self._goal_lock:
            self.goal_handle = None

    def cancel_goal(self):
        with self._goal_lock:
            active_goal = self.goal_handle

        if active_goal is None:
            self.bridge.status_text.emit('No active goal to cancel')
            return

        self.bridge.status_text.emit('Cancel requested')
        cancel_future = active_goal.cancel_goal_async()
        cancel_future.add_done_callback(self._cancel_done_callback)

    def _cancel_done_callback(self, future):
        cancel_response = future.result()
        if len(cancel_response.goals_canceling) > 0:
            self.bridge.status_text.emit('Cancel accepted by server')
        else:
            self.bridge.status_text.emit('Cancel rejected or goal already finished')


class PickupGuiWidget(QWidget):
    def __init__(self, ros_node: XarmPickupGuiClient, bridge: UiBridge):
        super().__init__()
        self.ros_node = ros_node
        self.bridge = bridge

        self.setWindowTitle('Xarm Grid Pickup')
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout()

        self.label_input = QLabel('Number of items (1-9)')
        self.spin_items = QSpinBox()
        self.spin_items.setRange(1, 9)
        self.spin_items.setValue(1)

        self.button_call = QPushButton('Call Action')
        self.button_cancel = QPushButton('Cancel')
        self.button_cancel.setEnabled(False)

        status_layout = QGridLayout()
        status_layout.addWidget(QLabel('Status'), 0, 0)
        status_layout.addWidget(QLabel('Current state'), 1, 0)
        status_layout.addWidget(QLabel('Current box'), 2, 0)
        status_layout.addWidget(QLabel('Items collected'), 3, 0)

        self.value_status = QLabel('Idle')
        self.value_state = QLabel('-')
        self.value_box = QLabel('-')
        self.value_items = QLabel('0')

        status_layout.addWidget(self.value_status, 0, 1)
        status_layout.addWidget(self.value_state, 1, 1)
        status_layout.addWidget(self.value_box, 2, 1)
        status_layout.addWidget(self.value_items, 3, 1)

        layout.addWidget(self.label_input)
        layout.addWidget(self.spin_items)
        layout.addWidget(self.button_call)
        layout.addWidget(self.button_cancel)
        layout.addLayout(status_layout)

        self.setLayout(layout)

    def _connect_signals(self):
        self.button_call.clicked.connect(self._on_call_action)
        self.button_cancel.clicked.connect(self._on_cancel_action)

        self.bridge.status_text.connect(self.value_status.setText)
        self.bridge.current_state.connect(self.value_state.setText)
        self.bridge.current_box.connect(self.value_box.setText)
        self.bridge.items_collected.connect(self.value_items.setText)
        self.bridge.goal_active.connect(self._set_goal_active)

    def _on_call_action(self):
        num_items = self.spin_items.value()
        self._set_goal_active(True)

        send_thread = threading.Thread(
            target=self.ros_node.send_goal,
            args=(num_items,),
            daemon=True,
        )
        send_thread.start()

    def _on_cancel_action(self):
        self.ros_node.cancel_goal()

    def _set_goal_active(self, active: bool):
        self.button_call.setEnabled(not active)
        self.button_cancel.setEnabled(active)


def _spin_ros(node: Node):
    rclpy.spin(node)


def main(args=None):
    rclpy.init(args=args)

    bridge = UiBridge()
    ros_node = XarmPickupGuiClient(bridge)

    ros_thread = threading.Thread(target=_spin_ros, args=(ros_node,), daemon=True)
    ros_thread.start()

    app = QApplication(sys.argv)
    widget = PickupGuiWidget(ros_node, bridge)
    widget.show()

    exit_code = app.exec_()

    ros_node.destroy_node()
    rclpy.shutdown()
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
