import time
import threading
import math
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from motorgo import BrakeMode, ControlMode, Plink

# Position control proportional gain (tune as needed)
Kp_pos = 5  # X-axis gains
Kp_pos_Y = 5  # Y-axis gains (for your janky coupler)

# Lead screw parameters
LEAD_MM = 8.0  # Lead of the screw in mm per revolution

# Desired target positions (encoder counts) - initialized later
pos_target_X = None
pos_target_Y = None
initial_position_1 = None
initial_position_2 = None
initial_position_3 = None

# Lock to make sure multiple threads aren't stomping on targets
pos_lock = threading.Lock()

# Global variables to hold plot objects and data
fig, ax = None, None
point = None, None
plot_data_x = 0
plot_data_y = 0

def mm_to_radians(mm):
    return (mm * 2 * math.pi) / LEAD_MM

def update_target():
    global pos_target_X, pos_target_Y
    while True:
        new_target = input("Enter new X and Y position targets in mm (space-separated, or press Enter to keep current): ")
        try:
            targets = new_target.split()
            with pos_lock:
                if len(targets) >= 1:
                    pos_target_X = mm_to_radians(float(targets[0]))
                    print(f"New X target position set to: {pos_target_X:.3f} radians ({targets[0]} mm)")
                if len(targets) >= 2:
                    pos_target_Y = mm_to_radians(float(targets[1]))
                    print(f"New Y target position set to: {pos_target_Y:.3f} radians ({targets[1]} mm)")
        except ValueError:
            print("Invalid input! Please enter valid numbers.")

def move_to_target(x, y):
    """Directly update position targets from a plot click (in mm)."""
    global pos_target_X, pos_target_Y
    with pos_lock:
        pos_target_X = mm_to_radians(x)
        pos_target_Y = mm_to_radians(y)
    print(f"Click Move -> X: {x:.1f} mm, Y: {y:.1f} mm")
    print(f"New Targets -> X: {pos_target_X:.3f} rad, Y: {pos_target_Y:.3f} rad")

def on_click(event):
    if event.xdata is not None and event.ydata is not None:
        move_to_target(event.xdata, event.ydata)

def show_xy_plot():
    global fig, ax, point, plot_data_x, plot_data_y
    fig, ax = plt.subplots()
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 200)
    ax.set_xlabel("X Position (mm)")
    ax.set_ylabel("Y Position (mm)")
    ax.set_title("Click to Move Gantry")

    point, = ax.plot([], [], 'ro')  # Initialize point
    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.grid(True)
    plt.show(block=False)

    while True:
        if fig and ax and point:
            point.set_data([plot_data_x], [plot_data_y])
            fig.canvas.draw_idle()
        plt.pause(0.01)

def main():
    global pos_target_X, pos_target_Y, initial_position_1, initial_position_2, initial_position_3, plot_data_x, plot_data_y

    plink = Plink()
    plink.power_supply_voltage = 12.0

    motor_1 = plink.channel1
    motor_2 = plink.channel2
    motor_3 = plink.channel3  # Y-axis motor

    for motor in (motor_1, motor_2, motor_3):
        motor.motor_voltage_limit = 12.0
        motor.control_mode = ControlMode.VELOCITY

    plink.connect()

    motor_1.set_velocity_pid_gains(5, 0, 0)
    motor_2.set_velocity_pid_gains(5, 0, 0)
    motor_3.set_velocity_pid_gains(10, 0, 0)  # Higher gain for Y-axis

    # Ensure motors stay still during initialization
    motor_1.velocity_command = 0
    motor_2.velocity_command = 0
    motor_3.velocity_command = 0
    time.sleep(2.0)

    # Capture initial positions to zero out
    initial_position_1 = motor_1.position
    initial_position_2 = motor_2.position
    initial_position_3 = motor_3.position
    with pos_lock:
        pos_target_X = initial_position_1
        pos_target_Y = initial_position_3

    print(f"Initial positions -> Motor 1: {initial_position_1}, Motor 2: {initial_position_2}, Motor 3: {initial_position_3}")

    # Start input thread
    threading.Thread(target=update_target, daemon=True).start()

    # Start plot thread
    threading.Thread(target=show_xy_plot, daemon=True).start()

    print_counter = 0

    while True:
        pos_current_1 = motor_1.position
        pos_current_2 = motor_2.position 
        pos_current_3 = motor_3.position 

        with pos_lock:
            pos_error_1 = pos_target_X - pos_current_1
            pos_error_2 = pos_target_X - pos_current_2
            pos_error_3 = pos_target_Y - pos_current_3

        if abs(pos_error_1) < 0.5:
            pos_error_1 = 0
        if abs(pos_error_2) < 0.5:
            pos_error_2 = 0
        if abs(pos_error_3) < 0.5:
            pos_error_3 = 0

        vel_setpoint_1 = Kp_pos * pos_error_1
        vel_setpoint_2 = Kp_pos * pos_error_2
        vel_setpoint_3 = Kp_pos_Y * pos_error_3

        motor_1.velocity_command = vel_setpoint_1
        motor_2.velocity_command = vel_setpoint_2
        motor_3.velocity_command = vel_setpoint_3

        if (print_counter % 10 == 0):
            print(f"X: {pos_current_1:.3f}/{pos_target_X:.3f} rad | Errors: ({pos_error_1:.3f}, {pos_error_2:.3f}) | Vels: ({vel_setpoint_1:.3f}, {vel_setpoint_2:.3f})")
            print(f"Y: {pos_current_3:.3f}/{pos_target_Y:.3f} rad | Error: {pos_error_3:.3f} | Vel: {vel_setpoint_3:.3f}")
        
        plot_data_x = pos_current_1 * LEAD_MM / (2 * math.pi)
        plot_data_y = pos_current_3 * LEAD_MM / (2 * math.pi)

        time.sleep(0.01)
        print_counter += 1

if __name__ == "__main__":
    main()