import os
from ament_index_python.packages import get_package_share_directory 
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction , SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('igv_assembly')


    resource_path_env = SetEnvironmentVariable(
    name='GZ_SIM_RESOURCE_PATH',
    value=os.path.dirname(pkg_share) + os.pathsep + os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    )
    urdf_path = os.path.join(pkg_share, 'urdf', 'igv_assembly.urdf')

    # world_path = os.path.join(pkg_share, 'worlds', 'empty_world.sdf')
    world_path = 'shapes.sdf'
    with open(urdf_path, 'r') as f:
        robot_description_content  = f.read() 

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description' : robot_description_content,
            'use_sim_time' : True
        }]    
    )

    ign_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'),
                         'launch',
                         'gz_sim.launch.py')),
                         launch_arguments={'gz_args': f'{world_path} -r'}.items())
    rviz_node = Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            output="screen",
            parameters=[{'use_sim_time' : True}]
            # arguments=["-d", "/home/navya/Documents/robot/src/robot/config/display.rviz"],
        )

    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic','robot_description',
            '-name','igv',
            '-z','0.3'
        ],
        output='screen'
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V',
            '/joint_states@sensor_msgs/msg/JointState[ignition.msgs.Model',
            '/depth_camera/image@sensor_msgs/msg/Image[ignition.msgs.Image',
            '/depth_camera/depth_image@sensor_msgs/msg/Image[ignition.msgs.Image',
            '/depth_camera/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo'
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
    arguments=['-d'],  # -d = delete previous database on each launch, good while iterating
)
    libgl_env = SetEnvironmentVariable(
        name='LIBGL_ALWAYS_SOFTWARE',
        value='1'
    )

    delayed_spawn = TimerAction(period=5.0, actions=[spawn_entity])
    delayed_bridge = TimerAction(period=5.0, actions=[bridge])
    delayed_rtab = TimerAction(period=5.0, actions=[rtabmap_node])

    return LaunchDescription([
        resource_path_env,
        libgl_env,
        robot_state_publisher_node,
        ign_gazebo,
        delayed_spawn,
        delayed_bridge,
        delayed_rtab,
        rviz_node,
    ])

    
