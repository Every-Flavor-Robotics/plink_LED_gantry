import time
import threading
import math

from motorgo import BrakeMode, ControlMode, Plink

# Position control proportional gain (tune as needed)
Kp_pos = 10  # Adjust this based on your system's response

# Lead screw parameters
LEAD_MM = 8.0  # Lead of the screw in mm per revolution

# Desired target position (encoder counts) - initialized later
pos_target = None
initial_position_1 = None
initial_position_2 = None

def update_target():
    global pos_target
    while True:
        new_target = input("Enter new position target in mm (or press Enter to keep current): ")
        try:
            mm_target = float(new_target)  # Convert input to float (in mm)
            pos_target = (mm_target * 2 * math.pi) / LEAD_MM  # Convert mm to radians
            print(f"New target position set to: {pos_target} radians ({mm_target} mm)")
        except ValueError:
            print("Invalid input! Please enter a valid number.")    

def main():
    global pos_target, initial_position_1, initial_position_2
    plink = Plink()
    plink.power_supply_voltage = 12.0  # Updated power supply voltage
    
    motor_1 = plink.channel1
    motor_2 = plink.channel2
    
    motor_1.motor_voltage_limit = 12.0  # Updated motor voltage limit
    motor_2.motor_voltage_limit = 12.0  # Updated motor voltage limit
    
    plink.connect()
    
    motor_1.control_mode = ControlMode.VELOCITY
    motor_2.control_mode = ControlMode.VELOCITY
    
    motor_1.set_velocity_pid_gains(10, 0, 0)  # Updated PID gains
    motor_2.set_velocity_pid_gains(10, 0, 0)  # Updated PID gains
    
    # Ensure motors stay still during initialization
    motor_1.velocity_command = 0
    motor_2.velocity_command = 0
    time.sleep(2.0)  # Allow encoders to stabilize
    
    # Normalize the initial position to start at 0
    initial_position_1 = motor_1.position
    initial_position_2 = motor_2.position
    pos_target = initial_position_1  # Start at the initial position to prevent shifting
    print(f"Initial position offsets set to: Motor 1: {initial_position_1}, Motor 2: {initial_position_2}")
    
    # Start a separate thread for user input
    input_thread = threading.Thread(target=update_target, daemon=True)
    input_thread.start()
    
    print_counter = 0
    
    while True:
        # Read current positions and normalize them
        pos_current_1 = motor_1.position
        pos_current_2 = motor_2.position
        
        # Compute position errors with dead band
        pos_error_1 = pos_target - pos_current_1
        pos_error_2 = pos_target - pos_current_2
        
        if abs(pos_error_1) < 0.2:
            pos_error_1 = 0
        if abs(pos_error_2) < 0.2:
            pos_error_2 = 0
        
        # Compute velocity setpoints
        vel_setpoint_1 = Kp_pos * pos_error_1
        vel_setpoint_2 = Kp_pos * pos_error_2
        
        # Send velocity commands to the velocity PID controllers
        motor_1.velocity_command = vel_setpoint_1
        motor_2.velocity_command = vel_setpoint_2
        
        # Print debug information
        if (print_counter%100 == 0):
            print(f"Target Pos: {pos_target} radians, Motor 1 Pos: {pos_current_1}, Motor 2 Pos: {pos_current_2}, Errors: ({pos_error_1}, {pos_error_2}), Vel Commands: ({vel_setpoint_1}, {vel_setpoint_2})")
        
        time.sleep(0.01)  # 10 ms loop
        print_counter += 1

if __name__ == "__main__":
    main()
