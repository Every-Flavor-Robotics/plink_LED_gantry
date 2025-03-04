import time
import board
import neopixel

def setup_pixels(num_leds):
    # Set up NeoPixel strip (Adjust pin and number of LEDs)
    pin = board.D21  # Use GPIO18 (or whichever GPIO you set up for the strip)
    pixels = neopixel.NeoPixel(pin, num_leds, brightness=1.0, auto_write=False)
    print(f"Pixel strip with {num_leds} LEDs initialized.")
    return pixels

def set_led_color(pixels, led_index, brightness, color):
    if 0 <= led_index < len(pixels):
        r, g, b = color
        pixels[led_index] = (int(r * brightness), int(g * brightness), int(b * brightness))
        pixels.show()
    else:
        print(f"LED index {led_index} out of range.")

def fill_all_leds(pixels, brightness, color):
    """Set all LEDs to the same color and brightness."""
    if brightness < 0 or brightness > 100:
        print("Brightness must be between 0 and 100.")
        return

    # Apply brightness to the color
    scaled_color = tuple(int(c * (brightness / 100)) for c in color)
    pixels.fill(scaled_color)
    print(f"All LEDs set to {scaled_color} with {brightness}% brightness.")
    
    # Update the pixels
    pixels.show()



# Example usage
if __name__ == "__main__":
    # Main code for testing
    pixels = setup_pixels(8)  # Initialize 8 LEDs

    # Set LED 5 to red at 50% brightness
    set_led_color(pixels, 5, 50, (255, 0, 0))

    # Set all LEDs to blue at 75% brightness
    fill_all_leds(pixels, 75, (0, 0, 255))
