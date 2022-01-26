# This project is really called O.t.i.s
## Observer Tracking Interation System
### Dependencies:
- python 3
- numpy
- cv2 (pip install opencv-python)
- optional: face_recognition (pip install face_recognition)

face_recognition isn't strictly necessary, but Otis does require an external 
package (i.e. TensorFlow, OpenVino, etc) for computer vision. face_recognition 
is the easiest to use out-of-the-box and I use it in some of my examples. So, 
get it. It's really easy to use. 

### There are three examples:
- camtest - tests the webcam works and shows its fps
- otistypes - otis will type out an introduction
- bboxes - example of using the multiprocessing module to put bounding boxes on
    faces in your webcam

### Examples can be run without installing this package:
- download the package
- in the command line:
  + $ cd path_to_outside_directory
  + $ python -m robocam.examples.otistypes
- you can see the examples' options via: 
  + $ python -m robocam.examples.bboxes --help

### Disclaimer
I've only tested this on Python 3.8 and ubuntu 20 
