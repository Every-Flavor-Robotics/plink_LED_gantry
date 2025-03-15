; Begin test
G1 X0 Y0        ; Move to the origin
M150 P0 R255 G0 B0 I1.0  ; Set all LEDs to red at full brightness
G1 X50 Y50      ; Move to a new position
M150 P1 R0 G255 B0 I0.5  ; Set LED 1 to green at half brightness
G4 P1000         ; Pause for 1 second to visually check LED 1

G1 X100 Y50     ; Move to another position

; End of test
M150 P0 R0 G0 B0 I1.0  ; Turn off all LEDs at full brightness
G1 X0 Y0           ; Return to origin position
