; Begin test
G1 X0 Y0        ; Move to the origin
M150 P0 R255 G0 B0 I1.0  ; Set all LEDs to red at full brightness
G1 X50 Y50      ; Move to a new position
M150 P1 R0 G255 B0 I0.5  ; Set LED 1 to green at half brightness
G4 P1000         ; Pause for 1 second to visually check LED 1

G1 X100 Y50     ; Move to another position
M150 P2 R0 G0 B255 I1.0  ; Set LED 2 to blue at full brightness
G4 P1000         ; Pause for 1 second to visually check LED 2

G1 X100 Y100    ; Move to another position
M150 P3 R255 G255 B0 I0.7  ; Set LED 3 to yellow at 70% brightness
G4 P1000         ; Pause for 1 second to visually check LED 3

G1 X150 Y150    ; Move to another position
M150 P0 R0 G255 B255 I0.8  ; Set all LEDs to purple at 80% brightness
G4 P1000         ; Pause for 1 second to visually check all LEDs

G1 X200 Y200    ; Move to another position
M150 P0 R0 G0 B0 I1.0  ; Turn off all LEDs (black) at full brightness
G4 P1000         ; Pause for 1 second to visually check all LEDs off

G1 X250 Y250    ; Move to a new position
M150 P4 R255 G255 B255 I1.0  ; Set LED 4 to white at full brightness
G4 P1000         ; Pause for 1 second to visually check LED 4

G1 X300 Y300    ; Move to another position
M150 P5 R255 G0 B255 I1.0  ; Set LED 5 to magenta at full brightness
G4 P1000         ; Pause for 1 second to visually check LED 5

M150 P0 R255 G0 B0 I0.3  ; Set all LEDs to red at 30% brightness
G4 P1000         ; Pause for 1 second to visually check all LEDs at 30% brightness
G1 X350 Y350    ; Move to another position
M150 P0 R255 G255 B255 I0.5  ; Set all LEDs to white at 50% brightness
G4 P1000         ; Pause for 1 second to visually check all LEDs at 50% brightness

G1 X400 Y400    ; Move to another position
M150 P0 R0 G255 B255 I0.9  ; Set all LEDs to cyan at 90% brightness
G4 P1000         ; Pause for 1 second to visually check all LEDs at 90% brightness

; End of test
M150 P0 R0 G0 B0 I1.0  ; Turn off all LEDs at full brightness
G1 X0 Y0           ; Return to origin position
M30                ; End of program
