import time
import math
import threading
from motorgo import BrakeMode, ControlMode, Plink
from gcode_parser import GCodeParser
from control_neopixel import setup_pixels, set_led_color, fill_all_leds

# === CONSTANTS ===
Kp_pos = 5
Kp_pos_Y = 5
LEAD_MM = 8.0

# === GLOBAL STATE ===
pos_target_X = 0
pos_target_Y = 0
led_strip = None
num_leds = 8  # Set this to match your strip length
pos_lock = threading.Lock()

# === UTILS ===
def mm_to_radians(mm):
    return (mm * 2 * math.pi) / LEAD_MM

# === MOTOR SETUP ===
def init_motors():
    plink = Plink()
    plink.power_supply_voltage = 12.0

    motors = {
        'X1': plink.channel1,
        'X2': plink.channel2,
        'Y': plink.channel3
    }

    for motor in motors.values():
        motor.motor_voltage_limit = 12.0
        motor.control_mode = ControlMode.VELOCITY

    plink.connect()

    motors['X1'].set_velocity_pid_gains(5, 0, 0)
    motors['X2'].set_velocity_pid_gains(5, 0, 0)
    motors['Y'].set_velocity_pid_gains(10, 0, 0)

    for motor in motors.values():
        motor.velocity_command = 0

    time.sleep(2)

    initial_positions = {axis: motor.position for axis, motor in motors.items()}
    print(f"Initial positions: {initial_positions}")

    return plink, motors, initial_positions

# === MOTOR CONTROL LOOP ===
def control_loop(motors, initial_positions):
    global pos_target_X, pos_target_Y

    while True:
        with pos_lock:
            target_x = pos_target_X
            target_y = pos_target_Y

        current_positions = {axis: motor.position for axis, motor in motors.items()}

        pos_error_X1 = target_x - current_positions['X1']
        pos_error_X2 = target_x - current_positions['X2']
        pos_error_Y = target_y - current_positions['Y']

        vel_X1 = Kp_pos * pos_error_X1
        vel_X2 = Kp_pos * pos_error_X2
        vel_Y = Kp_pos_Y * pos_error_Y

        motors['X1'].velocity_command = vel_X1
        motors['X2'].velocity_command = vel_X2
        motors['Y'].velocity_command = vel_Y

        time.sleep(0.01)

# === GCODE COMMAND CALLBACKS ===
def handle_G1(command, params):
    """Move command (G1) - Sets target position."""
    global pos_target_X, pos_target_Y

    x = float(params.get("X", pos_target_X * LEAD_MM / (2 * math.pi)))
    y = float(params.get("Y", pos_target_Y * LEAD_MM / (2 * math.pi)))

    with pos_lock:
        pos_target_X = mm_to_radians(x)
        pos_target_Y = mm_to_radians(y)

    print(f"Move to X={x:.1f}mm Y={y:.1f}mm (radians X={pos_target_X:.3f}, Y={pos_target_Y:.3f})")

def handle_M150(command, params, pixels):
    """Handle LED color command (M150)."""
    def safe_int(value, default=0):
        try:
            return int(value)
        except (ValueError, TypeError):
            print(f"⚠️ Invalid value '{value}' for M150 param. Using default={default}")
            return default

    def safe_float(value, default=1.0):
        try:
            return float(value)
        except (ValueError, TypeError):
            print(f"⚠️ Invalid value '{value}' for M150 param. Using default={default}")
            return default

    # Parse parameters
    led_index = safe_int(params.get("P", 0))  # LED index (P parameter)
    r = safe_int(params.get("R", 0))  # Red component
    g = safe_int(params.get("G", 0))  # Green component
    b = safe_int(params.get("B", 0))  # Blue component
    brightness = safe_float(params.get("I", 1.0))  # Brightness (I parameter)

    print(f"✅ M150 command: Set LED {led_index} to R={r}, G={g}, B={b}, Brightness={brightness}")

    # If LED index is 0, set all LEDs to the same color
    if led_index == 0:
        pixels.fill((int(r * brightness), int(g * brightness), int(b * brightness)))
    elif 1 <= led_index < 8:
        # For any index from 1 to 7 (8 LEDs in total), set the specific LED
         pixels[led_index - 1] = (int(r * brightness), int(g * brightness), int(b * brightness))
    else:
        print(f"⚠️ LED index {led_index} out of range! Valid range is 0-7.")

# In main.py
def m150_callback_wrapper(command, params):
    # Call the actual M150 handler with the pixels object
    handle_M150(command, params, led_strip)




# === PARSE AND RUN GCODE ===
def run_gcode_file(filename, parser, pixels):
    parser = GCodeParser(failure_mode="ignore")

    parser.register_callback("G1", handle_G1)
    parser.register_callback("M150", lambda command, params: handle_M150(command, params, pixels))

    with open(filename, 'r') as f:
        lines = f.readlines()

    for line in lines:
        parser.parse_line(line.strip())
        time.sleep(0.1)  # Tiny delay to allow motion to process (can tune this)

# === MAIN ENTRY ===
def main(gcode_file):
    global led_strip

    plink, motors, initial_positions = init_motors()

    pixels = setup_pixels(num_leds)

    parser = GCodeParser(failure_mode="error")
    # Register the M150 callback with the parser, passing the pixels object.
    parser.register_callback("M150", lambda command, params: handle_M150(command, params, pixels))

    control_thread = threading.Thread(target=control_loop, args=(motors, initial_positions), daemon=True)
    control_thread.start()

    run_gcode_file(gcode_file, parser, pixels)

    print("GCode execution finished. Holding position.")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <gcode_file>")
        sys.exit(1)

    main(sys.argv[1])
