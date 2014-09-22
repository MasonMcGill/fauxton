Fauxton
=======

![Left to right: optical image, surface normal map, depth map.](documentation/sphinx/home_page.png)

Fauxton is a software library designed to leverage computer graphics technology for computer vision applications. It provides simple interfaces to the [Blender](http://www.blender.org/) animation system and the [Open Shading Language](http://www.openshading.com/). Fauxton supports reading and writing Blender scenes, photorealistic rendering, and precise, automated annotation. It also provides a mechanism for serializing instances of user-defined resource types via Blender's native format.

Installation
------------
Fauxton depends on Blender 2.71+, [NumPy](http://www.numpy.org/) (for array handling), and [OpenCV](http://opencv.org/) (for transferring HDR images between processes). To install these dependencies on Ubuntu or Debian Linux:

    sudo apt-add-repository ppa:irie/blender
    sudo apt-get update
    sudo apt-get install blender python-numpy python-opencv

Fauxton itself can be installed by copying the source files into your site-packages directory. To install Fauxton on Ubuntu or Debian Linux:

    wget -q https://github.com/MasonMcGill/fauxton/archive/master.zip
    unzip master.zip -d master
    sudo mv master/fauxton-master/fauxton /usr/lib/python2.7/dist-packages
    rm -rf master.zip master

Documentation
-------------
Examples and API documentation can be accessed by opening *documentation/html/index.html*.
