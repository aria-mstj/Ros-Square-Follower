#! /usr/bin/env python3
import math
import matplotlib.pyplot as plt
import rospy
import random
from geometry_msgs.msg import Twist
from geometry_msgs.msg import Point
from turtlesim.msg import Pose
import tf
from nav_msgs.msg import Odometry

points = [(1.5, 1.5), (1.5, -1.5), (-1.5, -1.5), (-1.5, 1.5)]

class RndVelocityGen:
    def __init__(self):
        rospy.init_node('random_velocity')
        rospy.loginfo(
            "CTRL + C to stop the turtlebot")
        rospy.on_shutdown(self.shutdown)
        self.vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=1)
        # self.pose_Subscriber = rospy.Subscriber('/pose', Pose, self.update_pose)
        self.pose = Pose()
        self.plot_x = []
        self.plot_y = []
        self.vel = Twist()
        self.vel.linear.x = 0.5  # m/s
        self.vel.angular.z = 0.5  # rad/s
        self.max_interval = 10
        self.start_time = rospy.get_rostime().secs
        self.tmp = 0
        self.counter = 0

    # def update_pose(self, data):
    #     self.pose = data
        # self.pose.x = round(self.pose.x, 4)
        # self.pose.y = round(self.pose.y, 4)

    def steering_angle(self, point):
        # print("SELF POS IN STEERING : ", (self.pose.x, self.pose.y))
        return math.atan2(point.y - self.pose.y, point.x - self.pose.x)

    def angular_error(self, point):
        # print("ANGULAR_ERROR theta :", self.pose.theta,
        #       "Steering angle", self.steering_angle(point),
        #       "Result", self.steering_angle(point) - self.pose.theta)

        return self.steering_angle(point) - self.pose.theta

    def dist(self, pos1):
        return math.sqrt(((pos1.x - self.pose.x) ** 2) + ((pos1.y - self.pose.y) ** 2))

    def set_vel(self):

        while not rospy.is_shutdown():
            while self.counter < 10:
                data_odom = None
                while data_odom is None:
                    try:
                        data_odom = rospy.wait_for_message("/odom", Odometry, timeout=1)
                        # data_twist = rospy.wait_for_message("/change", Twist, timeout=1)
                        self.pose.x = data_odom.pose.pose.position.x
                        self.pose.y = data_odom.pose.pose.position.y
                        quaternion = (data_odom.pose.pose.orientation.x, data_odom.pose.pose.orientation.y,
                                      data_odom.pose.pose.orientation.z, data_odom.pose.pose.orientation.w)

                        (roll, pitch, theta) = tf.transformations.euler_from_quaternion(quaternion)
                        print("THETA = ", theta)
                        self.pose.theta = theta
                        # print("calculated theta = ", math.atan2(self.pose.x, self.pose.y))
                        # print("DATA_ODOM : ", data_odom.pose.pose.position)
                        # print("DATA_ODOM ANGLE :", self.pose.theta)
                    except:
                        rospy.loginfo("CANT FIND ODOM")

                # self.pose.theta = data_odom.
                point = Pose()
                point.x = points[self.tmp][0]
                point.y = points[self.tmp][1]
                goal_x = points[self.tmp][0]
                goal_y = points[self.tmp][1]
                safe_dist = 0.25
                if self.counter == 1:
                    self.plot_x.append(self.pose.x)
                    self.plot_y.append(self.pose.y)
                distance_error = self.dist(point)
                if distance_error < safe_dist:
                    self.tmp += 1
                if self.tmp == 4:
                    self.tmp = 0
                    self.counter += 1

                point.x = points[self.tmp][0]
                point.y = points[self.tmp][1]
                goal_x = points[self.tmp][0]
                goal_y = points[self.tmp][1]

                x_dif = goal_x - self.pose.x
                y_dif = goal_y - self.pose.y

                angular_error = self.angular_error(point)
                x_forward = 0.5
                constant = 0.5
                angle_to_goal = math.atan2(y_dif, x_dif)
                z_counterclock = 0
                angle_to_goal = angle_to_goal - self.pose.theta
                if angle_to_goal > math.pi:
                    angle_to_goal -= 2 * math.pi
                if angle_to_goal < -math.pi:
                    angle_to_goal += 2 * math.pi

                if abs(angle_to_goal) > 0.1:
                    z_counterclock = constant * (angle_to_goal)
                    # x_forward = 0
                print("Angular_error = ", angular_error)
                # if abs(angular_error) < 0.7:
                #     print("pichesh 0")
                #     z_counterclock = 0
                    # x_forward = 0.9

                print("ANGULAR Result : ", z_counterclock)

                self.vel.linear.x = x_forward
                print("linear speed", self.vel.linear.x)
                # print("ANGULAR VEL : ", self.vel.angular)
                self.vel.angular.z = z_counterclock

                print("SELF = ", self.pose)
                print("LOCATION Follower", self.tmp)
                print("DISTANCE = ", distance_error)

                self.vel_pub.publish(self.vel)
                now = rospy.get_rostime()
                print("Time now: ", now.secs)
                next = 0.5
                rospy.loginfo("Twist: [%5.3f, %5.3f], next change in %i secs - ", self.vel.linear.x, self.vel.angular.z,
                              next)
                rospy.sleep(next)
        # rospy.spin()
            plt.plot(self.plot_x, self.plot_y)
            plt.plot([1.5, 1.5, -1.5, -1.5, 1.5], [1.5, -1.5, -1.5, 1.5, 1.5])
            plt.legend(["Dataset 1", "Dataset 2"])
            plt.savefig("plots.pdf")

            self.shutdown()

    def shutdown(self):
        print("Shutdown!")
        rospy.loginfo("Stop TurtleBot")
        self.vel.linear.x = 0.0
        self.vel.angular.z = 0.0
        self.vel_pub.publish(self.vel)
        rospy.sleep(1)

if __name__ == '__main__':
    try:
        generator = RndVelocityGen()
        generator.set_vel()

    except rospy.ROSInterruptException:
        pass