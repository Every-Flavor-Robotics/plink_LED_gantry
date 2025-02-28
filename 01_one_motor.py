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
initial_position = None

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
    global pos_target, initial_position
    plink = Plink()
    plink.power_supply_voltage = 12.0  # Updated power supply voltage
    
    motor = plink.channel1
    motor.motor_voltage_limit = 12.0  # Updated motor voltage limit
    
    plink.connect()
    
    motor.control_mode = ControlMode.VELOCITY
    motor.set_velocity_pid_gains(10, 0, 0)  # Updated PID gains
    
    # Ensure motor stays still during initialization
    motor.velocity_command = 0
    time.sleep(2)  # Allow encoder to stabilize
    
    # Normalize the initial position to start at 0
    initial_position = motor.position
    pos_target = initial_position  # Start at the initial position to prevent shifting
    print(f"Initial position offset set to: {initial_position}")
    # additional steps to keep it from jumping on startup 

    
    # Start a separate thread for user input
    input_thread = threading.Thread(target=update_target, daemon=True)
    input_thread.start()
    
    print(f"First error calculation: {pos_target - (motor.position - initial_position)}")
    
    '''
    print("--------------debug-----------------")
    print(f"pos_target: {pos_target}")
    print(f"motor.position: {motor.position}")
    print(f"initial position: {initial_position}")
    print("--------------debug-----------------")
    '''

    print_counter = 0

    while True:
        # Read current position and normalize it
        pos_current = motor.position
        
        # Compute position error with dead band
        pos_error = pos_target - pos_current
        if abs(pos_error) < 0.2:
            pos_error = 0
        
        # Compute velocity setpoint
        vel_setpoint = Kp_pos * pos_error
        
        # Send velocity command to the velocity PID controller
        motor.velocity_command = vel_setpoint
        
        # Print debug information
        if (print_counter%100 == 0):
            # print(f"Target Pos: {pos_target} radians, Current Pos: {pos_current}, Error: {pos_error}, Vel Command: {vel_setpoint}")
            pass 

        time.sleep(0.01)  # 10 ms loop
        print_counter += 1

if __name__ == "__main__":
    main()
