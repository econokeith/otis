import numpy as np
######################## MAIN VARIABLES ################################################################################
dim = (1280, 720)
max_fps = 30
port = 0
max_faces = 10
use_servos = True
output_scale = 1.5
record_scale = .5
record = False
record_to = 'image_sprinkler.avi'
path_to_faces = './faces'


####################### VISION MODEL PROCESS VARIABLES #################################################################

######################## SERVO PROCESS VARIABLES #######################################################################

MAX_SERVO_UPDATES_PER_SECOND = 10
# _X_PID_VALUES = (.0001, .000000001, .00000001)
# Y_PID_VALUES = (.0001, .000000001, .00000001)
X_PID_VALUES = (1e-4, 1e-10, 2e-7)
Y_PID_VALUES = (5e-5 ,1e-10, 2e-7)
MINIMUM_MOVE_SIZE_PIXELS = 20
SERVO_START = np.array((-.06, -.72))
KEYBOARD_MOVE_INCREMENT = -.01
STEPS_TO_RESET = 2