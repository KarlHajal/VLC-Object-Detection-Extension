 # VLC Object Detection Extension
![alt text](https://github.com/KarlHajal/VLC-Object-Detection-Add-On/raw/master/extension/object_detector_data/logo.png "Logo")
 ### Description
 ***
 VLC extension that allows users to search for frames containing a certain object. 
 It currently only works on Linux.

### Installation
***
1. Install Tensorflow and its dependencies (https://www.tensorflow.org/install/).
2. Assuming VLC is already installed, clone this repository and copy the files present in the 'extensions' directory to the '~/.local/share/vlc/lua/extensions/' directory.
3. The extension should be accessible from VLC at this point. The first time the script is executed, the COCO model will be downloaded, completing the installation. 
I would suggest running VLC from a terminal so that what is happening becomes apparent through output messages.

### Issues
***
Searching for an object can be a very lengthy operation. As a result VLC might prompt that the process is not responding and offer to kill it. Again, I would suggest running VLC from a terminal to be able to see that the search is indeed ongoing.

### Screenshots
***

#### Initial/Reset State
![alt text](https://github.com/KarlHajal/VLC-Object-Detection-Add-On/raw/master/screenshots/initial_state.png "Initial State")

#### Objects Found
When the first frame containing the object is found, it is displayed to the user along with the time at which it was found, and the ability to jump to the corresponding frame within the video file.
![alt text](https://github.com/KarlHajal/VLC-Object-Detection-Add-On/raw/master/screenshots/object_found_1.png "Object Found 1")

![alt text](https://github.com/KarlHajal/VLC-Object-Detection-Add-On/raw/master/screenshots/object_found_2.png "Object Found 2")

#### Error Message Displayed
In case the specified object wasn't found or there was an issue with the user input, a message is diplayed informing the user of what went wrong.
![alt text](https://github.com/KarlHajal/VLC-Object-Detection-Add-On/raw/master/screenshots/error_message.png "Error Message")
