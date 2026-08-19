import os
from ament_index_python.packages import get_package_share_directory 
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterValue
from launch.substitutions import Command

def generate_launch_description():
    pkg_share = get_package_share_directory('igv_assembly')

    resource_path_env = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=os.path.dirname(pkg_share) + os.pathsep + os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    )
    
    urdf_path = os.path.join(pkg_share, 'urdf', 'simple_bot.urdf.xacro')
    world_path = "/home/akshit/IGV_2026/src/igv_assembly/worlds/living_room.sdf"
    
    robot_description_content = ParameterValue(Command(['xacro ', urdf_path]), value_type=str)

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description' : robot_description_content,
            'use_sim_time' : True
        }]    
    )

    gz_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'),
                         'launch',
                         'gz_sim.launch.py')),
        launch_arguments={'gz_args': f'{world_path} -r'}.items()
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        parameters=[{'use_sim_time' : True}]
    )

    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic','robot_description',
            '-name','igv',
            '-x', '-0.8',
            '-z','0.3'
        ],
        output='screen'
    )

    # Corrected GZ message syntax and topic paths
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/depth_camera/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/depth_camera/depth_image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/depth_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo'
        ],
        output="screen"
    )

    rtabmap_params = os.path.join(pkg_share, 'config', 'rtab_config.yaml')
    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        output='screen',
        parameters=[rtabmap_params],
        remappings=[
            ('rgb/image', '/depth_camera/image'),
            ('depth/image', '/depth_camera/depth_image'),
            ('rgb/camera_info', '/depth_camera/camera_info'),
            ('odom', '/odom'),
        ],
        arguments=['-d'], 
    )

    spawn_joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output='screen',
    )

    spawn_diff_drive_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_drive_controller', '--controller-manager', '/controller_manager'],
        output='screen',
    )

    delayed_spawn = TimerAction(period=5.0, actions=[spawn_entity])
    delayed_bridge = TimerAction(period=5.0, actions=[bridge])
    delayed_rtab = TimerAction(period=5.0, actions=[rtabmap_node])
    delayed_controllers = TimerAction(period=8.0, actions=[spawn_joint_state_broadcaster, spawn_diff_drive_controller])

    return LaunchDescription([
        resource_path_env,
        robot_state_publisher_node,
        gz_gazebo,
        delayed_spawn,
        delayed_bridge,
        delayed_rtab,
        delayed_controllers,
        rviz_node,
    ])
