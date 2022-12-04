"""
It's often easier to break up the various processes into separate processes

main.py is the one that sets up shared data and starts processes
camera_process.py manages what happens on the screen and manages the communication between the other processes
cv_model_process.py runs the vision models for finding faces and recognizing them
servo_process moves the servos
"""