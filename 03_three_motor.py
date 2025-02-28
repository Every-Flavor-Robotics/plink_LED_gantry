import time
import threading
import math

from motorgo import BrakeMode, ControlMode, Plink

# Position control proportional gain (tune as needed)
Kp_pos = 10  # Adjust this based on your system's response
Kp_pos_Y = 10  # Higher gain for Y-axis due to mechanical issues

# Lead screw parameters
LEAD_MM = 8.0  # Lead of the screw in mm per revolution

# Desired target position (encoder counts) - initialized later
pos_target_X = None
pos_target_Y = None
initial_position_1 = None
initial_position_2 = None
initial_position_3 = None

def update_target():
    global pos_target_X, pos_target_Y
    while True:
        new_target = input("Enter new X and Y position targets in mm (space-separated, or press Enter to keep current): ")
        try:
            targets = new_target.split()
            if len(targets) >= 1:
                mm_target_X = float(targets[0])
                pos_target_X = (mm_target_X * 2 * math.pi) / LEAD_MM
                print(f"New X target position set to: {pos_target_X} radians ({mm_target_X} mm)")
            if len(targets) >= 2:
                mm_target_Y = float(targets[1])
                pos_target_Y = (mm_target_Y * 2 * math.pi) / LEAD_MM
                print(f"New Y target position set to: {pos_target_Y} radians ({mm_target_Y} mm)")
        except ValueError:
            print("Invalid input! Please enter valid numbers.")    

def main():
    global pos_target_X, pos_target_Y, initial_position_1, initial_position_2, initial_position_3
    plink = Plink()
    plink.power_supply_voltage = 12.0  # Updated power supply voltage
    
    motor_1 = plink.channel1
    motor_2 = plink.channel2
    motor_3 = plink.channel3  # Y-axis motor
    
    motor_1.motor_voltage_limit = 12.0
    motor_2.motor_voltage_limit = 12.0
    motor_3.motor_voltage_limit = 12.0  # Y-axis motor voltage limit
    
    plink.connect()
    
    motor_1.control_mode = ControlMode.VELOCITY
    motor_2.control_mode = ControlMode.VELOCITY
    motor_3.control_mode = ControlMode.VELOCITY  # Y-axis in velocity mode
    
    motor_1.set_velocity_pid_gains(10, 0, 0)
    motor_2.set_velocity_pid_gains(10, 0, 0)
    motor_3.set_velocity_pid_gains(20, 0, 0)  # Higher gain for Y-axis
    
    # Ensure motors stay still during initialization
    motor_1.velocity_command = 0
    motor_2.velocity_command = 0
    motor_3.velocity_command = 0
    time.sleep(2.0)  # Allow encoders to stabilize
    
    # Normalize the initial position to start at 0
    initial_position_1 = motor_1.position
    initial_position_2 = motor_2.position
    initial_position_3 = motor_3.position
    pos_target_X = initial_position_1
    pos_target_Y = initial_position_3
    print(f"Initial position offsets set to: Motor 1: {initial_position_1}, Motor 2: {initial_position_2}, Motor 3: {initial_position_3}")
    
    # Start a separate thread for user input
    input_thread = threading.Thread(target=update_target, daemon=True)
    input_thread.start()

    print_counter = 0
    
    while True:
        # Read current positions and normalize them
        pos_current_1 = motor_1.position
        pos_current_2 = motor_2.position
        pos_current_3 = motor_3.position
        
        # Compute position errors with dead band
        pos_error_1 = pos_target_X - pos_current_1
        pos_error_2 = pos_target_X - pos_current_2
        pos_error_3 = pos_target_Y - pos_current_3
        
        if abs(pos_error_1) < 0.3:
            pos_error_1 = 0
        if abs(pos_error_2) < 0.3:
            pos_error_2 = 0
        if abs(pos_error_3) < 0.3:
            pos_error_3 = 0
        
        # Compute velocity setpoints
        vel_setpoint_1 = Kp_pos * pos_error_1
        vel_setpoint_2 = Kp_pos * pos_error_2
        vel_setpoint_3 = Kp_pos_Y * pos_error_3
        
        # Send velocity commands to the velocity PID controllers
        motor_1.velocity_command = vel_setpoint_1
        motor_2.velocity_command = vel_setpoint_2
        motor_3.velocity_command = vel_setpoint_3
        
        # Print debug information
        if (print_counter%100==0):
            print(f"Target X: {pos_target_X:.3f} rad, Motor 1 Pos: {pos_current_1:.3f}, Motor 2 Pos: {pos_current_2:.3f}, Errors: ({pos_error_1:.3f}, {pos_error_2:.3f}), Vel Commands: ({vel_setpoint_1:.3f}, {vel_setpoint_2:.3f})")
            print(f"Target Y: {pos_target_Y:.3f} rad, Motor 3 Pos: {pos_current_3:.3f}, Error: {pos_error_3:.3f}, Vel Command: {vel_setpoint_3:.3f}")
        
        print_counter += 1
        time.sleep(0.01)  # 10 ms loop


if __name__ == "__main__":
    main()
