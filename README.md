# O.T.I.S. - Observer Tracking Interactive Scripting

### What it does
Robocam provides a framework for making interactive computer vision models and writing scripted encounters with 
participants using them. It solves one of the major hurdles to making realistic viewing experiences for humans by 
allowing for a hi-definition real-time camera feed even when the models being used don't update quickly enough. It 
accomplishes this by using the python multiprocessing module to run the camera process separately from the computer
vision model. 

The key is that when looking at themselves on a large scene, people are more focused on whether they themselves are 
choppy, which they won't be at 30 fps. So, even if the bounding boxes in the overlay are only updating at 10 fps, most
viewers won't notice. 

Robocam also provides tools to make it easy to manage the fact that the models and the camera are running 
asynchronously. These include a SharedDataContainer object to quickly create and share buffers between the processes. 
In addition to managing the shared memory, robocam  has extensive shape and text writer asset classes and timer classes 
to ensure that the experience runs at the same speed regardless of camera frame rate or model update speed. 

Finally, robocam also includes a Servo package for controlling a pan-tilt camera with a PID (proportional integrate 
derivative) controller. 


### Dependencies
- python 3
- numpy
- cv2 (pip install opencv-python)
- optional: face_recognition (pip install face_recognition)
- optional: pyserial (pip install pyserial)

face_recognition isn't strictly necessary, but robocam does require a backend for computer vision (i.e. TensorFlow, 
OpenVino, etc). face_recognition is the easiest to use out-of-the-box, and I use it in some of my examples. 

pyserial is required if you want to use the servo package with an arduino as the arduino requires serial port 
communications. 


### Disclaimer
This is nowhere near being ready for release. I've only tested this on Python 3.8 and ubuntu 20 and change it daily. 
I am only making it not-private as part of my application to the PATH-AI residency. 
