# Map-Print-O-Matic

Exposing a web API that returns a ready-to-print PDF

### Installation

**Setting up Python and OpenCV**

This is by far the biggest hassle. Once it is done, however, it never needs to
be done again. These instructions work on Ubuntu 12.04. You’ll probably need to
modify them to suit your particular environment. These directions also assume
you have [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/) 
setup as well.

```bash 
$ mkvirtualenv printmatic
$ pip install numpy
$ sudo apt-get install cmake libgtk2.0-dev pkg-config libavcodec-dev \
  libavformat-dev libswscale-dev libamd2.2.0 libblas3gf libc6 libgcc1 \
  libgfortran3 liblapack3gf libumfpack5.4.0 libstdc++6 build-essential \
  gfortran libatlas-dev libatlas-base-dev libblas-dev liblapack-dev libjpeg-dev \
  libpng-dev libtiff-dev libjasper-dev
$ wget -O opencv-2.4.9.zip http://downloads.sourceforge.net/project/opencvlibrary/opencv-unix/2.4.9/opencv-2.4.9.zip?r=http%3A%2F%2Fopencv.org%2Fdownloads.html&ts=1403558615&use_mirror=softlayer-dal
$ mkdir src && mv opencv-2.4.9.zip src && cd src
$ unzip opencv-2.4.9.zip
$ cd opencv-2.4.5/
$ mkdir release
$ cd release
$ cmake -DMAKE_BUILD_TYPE=RELEASE -DCMAKE_INSTALL_PREFIX=$VIRTUAL_ENV/local/ \
  -DPYTHON_EXECUTABLE=$VIRTUAL_ENV/bin/python \
  -DPYTHON_PACKAGES_PATH=$VIRTUAL_ENV/lib/python2.7/site-packages \
  -DINSTALL_PYTHON_EXAMPLES=ON ..
$ make -j8 # Set the number here to the number of processing cores you have
$ make install
```
