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

### ScreenAssets


- otis provides 3 basic **ShapeAsset** classes: **Line**, **Circle**, **Rectangle**. Each is based on the underlying cv2 drawing functions. 
On a basic level, these objects provide a container to storing the inputs of each respective cv2 function. However, they
also add otis's much easier to use coordinate system (see below) as well as a more straightforward framework for updating 
the position as well as other attributes of each shape (i.e. color, size, etc).

- otis also provides an extendable **ComplexShape** class, which can combine multiple basic shapes into a single object, 
such as **CrossHairs**.

### TextWriters
- otis has two powerful text classes: **TextWriter** and **TypeWriter**:

    - **TextWriter** is a multiline text writer built on the cv2.putText function. It adds justification, automatic line breaking 
based on either maximum line length or desire number of lines, fast additions of underlines and borders, automatic calculation 
of the text hitbox sizes, and a relative anchor system that 
allows the user to specify how they want to define the location of the text. For instance, cv2 always defined text from the 
bottom left starting point. However, in many applications it's considerably more convenient to define the location of the text
from the center point. Particularly, if the text is moving or attached to another asset, such as a bounding box. 

**TypeWriter** expands the TextWriter class so that the text is typed. The speed is user defined with key presses either 
occurring at constant intervals or stochastically over a user defined range. 

### ImageAssets

**ImageAsset** provide asset functionality to images. The user can either import an image from a .jpg file or define 
an image taken from either the current or past frame. 

### AssetHolders

otis provides three **AssetHolder** classes to extend the functionality of **ScreenAssets**

- **AssetBounders** add bounding box behavior to any the screen assets

- The **AssetMover** class provides movement, collision tracking, and basic physics (i.e. gravity, elasticity, etc) to 
ScreenAssets
AssetGroups
- The **AssetGroup** is an extendable multi-asset container class to allow grouping and common movement of multiple Screen Assets.

## Helpers

### Asynchronous Timer Objects
### Multiprocessing Tools
### Coordinate Tools
