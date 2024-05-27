# OutFox
This is a volunteer project to help save the endangered Bell turtle species. I'm assisting the "Turtles Forever" project team in developing a fox (and dogs) detection and scaring system that uses Artificial Intelligence (AI) to identify the preditors and ward them off. The main preditor causing the damage has been foxes that are not native to Australia and are destroying the turtle nests.

This is the working prototype (PCB not validated) for the solution. It uses MobileNet AI model as it already detects many species of foxes, dogs and wolves.

*Any assistance in this project is welcome!!!*

## Articles About the Project
https://www.abc.net.au/news/2018-03-07/turtle-hatchlings-offer-hope-endangered-bells-turtle/9522182
https://northerntablelands.lls.nsw.gov.au/resource-hub/media-releases/2016/work-begins-on-bells-turtle-recovery-project

Fox and other nuisance animal detection and frightening device. Uses cameras and AI to detect and identify only the nuisance animals.
![OutFox Control Board](/images/OutFox.png)

*This is a Work in Progress*
# Notes for using the Seeed Studio MAIX Bit and the Kendryte K210

## Sipeed MAix BiT for RISC-V AI+IoT
The core of the system is the Sipeed BiT board with camera available from Seeed. 
https://www.seeedstudio.com/Sipeed-MAix-BiT-for-RISC-V-AI-IoT-p-2872.html

This board uses a Kendryte K210 Neural Accellerator for at the edge AI. The board consumes less than 1 Watt of power.

If using this board and camera for night vision using the IR LEDs you'll need to unscrew the lense from the camera and remove the small square IR filter from the back of the lense.

The documentation for this processor is available here:
https://maixpy.sipeed.com/en/

## SiSpeed Downloads
http://dl.sipeed.com/MAIX/
https://github.com/sipeed

## Uploading files and firmware
Use uPyLoader for uploading files and executing script
Use kloader_windows for uploading firmware

The details of obtaining and using these tools is available from the Sipeed website:

https://maixpy.sipeed.com/en/get_started/upload_script.html

## MaixPy Firmware
Builds:   http://dl.sipeed.com/MAIX/MaixPy/release/master/
GitHub: https://github.com/sipeed/MaixPy/releases

## Train, Convert and Run Models for MaixPy 
The following article explains how to train, convert and run AI modules on the MAix BiT and other modules using the Kendryte K210 processor.
https://bbs.sipeed.com/t/topic/682

### Package Kfpkg files
http://blog.sipeed.com/p/390.html
**Note 1:** *SD library does not support long file names.*
**Note 2:** *name.kmodel files are in the zipped file name.kfpkg*

kfpkg files are zipped files containing the following files:

	model.kmodel file that is the inference model
	flash-list.json file that tells the loaded where to put the model in flash memory
	
A typical kfpkg flash-list.json file is below where facedetect.kmodel is the name of the kmodel file:
'''json
{
    "version": "0.1.0",
     "files": [
        {
            "address": 0x00300000,
            "bin": "facedetect.kmodel",
            "sha256Prefix": false
        }
    ]
}
'''
