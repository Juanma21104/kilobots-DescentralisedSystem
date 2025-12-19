# --- Parameters ---
KILOBOTS_X = 10 # Number of kilobots in X direction
KILOBOTS_Y = 10 # Number of kilobots in Y direction
GRID_SIZE = 60   # Size of each grid cell
IR_ERROR = 0.02 # Error in IR 2%
FAILURE_PROB = 0.001 # Probability of kilobot failure 0.1%
LOST_MESSAGE_PROB = 0.10 # Probability of lost message 10%
SEPARATION = 1  # Separation between kilobots in grid cells

R3_ANIMATION = "diagonal_wave" # Selected animation for routine 3
                  # Options: "diagonal_wave", "wasp", "smiley_face"

# --- Robot's states ---
class State:
    # Routine R1
    SR1A_ID_ASSIGNMENT = 0  
    SR1B_NEIGHBOR_LIST = 1  
    SR1C_ROLE_ID = 2
    SR1C_SET_ROLE = 3

    # Routine R2
    SR2A_ORIGIN_ASSIGNMENT = 4
    SR2A_SET_ORIGIN = 5
    SR2A_ORIGIN_SET_POSITION = 6
    SR2B_SET_REC_DIMENSION = 7
    SR2B_SET_RELATIVE_POS = 8
    SR2C_SET_GLOBAL_POS = 9

    # Routine R3
    SET_ANIMATION_SINCRONIZATION = 10
    SET_ROLE_COLOR = 11