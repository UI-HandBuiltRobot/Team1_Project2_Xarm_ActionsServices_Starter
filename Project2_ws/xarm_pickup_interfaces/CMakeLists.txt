cmake_minimum_required(VERSION 3.8)
project(xarm_pickup_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/GridServicePlaceholder.srv"
  "srv/MoveToDropoff.srv"
  "srv/OpenGripper.srv"
  "srv/CloseGripper.srv"
  "action/RetrieveItems.action"
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
