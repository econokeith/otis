# O.T.I.S. - Observer Tracking Interactive Scripting

  ![meet otis](./readme_gifs/helloKeith540.gif)


(view full video on Vimeo, [here](https://vimeo.com/786671400))

## What does OTIS do?

OTIS provides a framework for making interactive computer vision models and writing scripted encounters for participant 
observers. It solves one of the major hurdles to making realistic viewing experiences for humans by allowing for a 
hi-definition real-time camera feed even when the models being used don't update quickly enough. It accomplishes this by 
using the python multiprocessing module to run the camera/display process separately from the computer vision model.

The key is that when looking at themselves on a large scene, people are more focused on whether they themselves are 
choppy, which they won't be at 30 fps. So, even if the bounding boxes in the overlay are only updating at 10 fps, most 
viewers won't notice.

OTIS provides tools to make it easy to manage the fact that the models and the camera are running asynchronously. 
These include a SharedDataContainer object to quickly create and share buffers between the processes. It also includes a 
rich collection of Timer classes to ensure that the experience runs at the same speed regardless of camera frame rate or 
model update speed.

OTIS is also designed to make the process of iteration in the creation of interactive scripts quick and easy. Written on 
top of open-cv's image writing library, it adds hundreds of convenience classes and functions to allow placement, movement, 
event handling, collision handling, and interaction amongst onscreen assets.

### Dependencies
- python 3
- numpy
- cv2 (pip install opencv-python)
- optional: face_recognition (pip install face_recognition)

face_recognition isn't strictly necessary, but otis does require a computer vision backend (i.e. TensorFlow, 
OpenVino, etc) for face/object recognition and tracking. Each has pros and cons and the user is encouraged to use whichever 
they feel most comfortable with. However, face_recognition is the easiest to use out-of-the-box, and I use it in some of my examples. 

Also note that while OTIS works well with camera tracking, it does require additional servo controller software in order to 
work with either an Arduino or Raspberry Pi microcontroller. 

## Display Assets
### Shapes
 
- OTIS provides 3 basic **ShapeAsset** classes: **Line**, **Circle**, **Rectangle**. On a basic level, these objects provide
a container to storing the inputs of each respective cv2 function. However, they
also add otis's much easier to use coordinate system (see below) as well as a more straightforward framework for updating 
the position as well as other attributes of each shape (i.e. color, size, etc).

- otis also provides an extendable **ComplexShape** class, which can combine multiple basic shapes into a single object, 
such as **CrossHairs** or **CircleWithLineToCenter**

### TextWriters

- The **TextWriter** class is a multiline text writer built on the cv2.putText function. It adds justification, automatic line breaking 
based on either maximum line length or desire number of lines, fast additions of underlines and borders, automatic calculation 
of the text hitbox sizes, and a relative anchor system that 
allows the user to specify how they want to define the location of the text. For instance, cv2 always defined text from the 
bottom left starting point. However, in many applications it's considerably more convenient to define the location of the text
from the center point. Particularly, if the text is moving or attached to another asset, such as a bounding box. 

- The **TypeWriter** class expands TextWriter so that the text is typed. The speed is user defined with key presses either 
occurring at constant intervals or stochastically over a user defined range. 

### ImageAssets

**ImageAsset** provide asset functionality to images. The user can either import an image from a .jpg file or define 
an image taken from either the current or past frame. (examples shown below)

## Asset Holders

OTIS provides three asset holder classes that extend the functionality of the aforementioned display assets.

- The **AssetBounder** class adds bounding box behavior to any the of screen assets. Below an ImageAsset that reads from
the frame location of Taylor Swift's bounding box (when available) is used as a bounder.

![keith_and_taylor](./readme_gifs/keith_taylor540.gif)

(find code [here](https://github.com/econokeith/otis/blob/master/examples/taylor_and_me.py))

- The **AssetMover** class provides movement, collision tracking, and basic physics (i.e. gravity, elasticity, etc) to 
ScreenAssets

![bouncy_movers](./readme_gifs/bouncy_movers.gif)

(find code [here](https://github.com/econokeith/otis/blob/master/examples/bouncy_movers.py))

- The **AssetGroup** class is an extendable multi-asset container class to allow grouping and common movement of multiple Screen Assets.

