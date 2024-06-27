DICOM examples
========

## About
This is a demo repository showing examples of manipulating DICOM images and sending results to the Sectra viewer.

Author: Nicolas Brandt nicolas.brandt@hcuge.ch

## send_cstore.py

Script that takes as input a DICOM file and sends it to a Sectra application entity to be displayed in the Sectra viewer.
This can be used for example to display results of analysis as an image next to the analyzed slide.
For presentation context, the script uses the VLWholeSlideMicroscopyImageStorage SOP class with JPEGBaseline transfer syntax - these may need to be adjusted depending on the DICOM image that is to be sent.
Note that this will only send a single DICOM file and that the appropriate metadata needs to be presented in the DICOM image for the image to be displayed at the correct location (i.e. Container Identifier or other).
Note as well that not all DICOM images can be displayed in the Sectra viewer (see conformance statement document).


### Install and run

Requirements can be installed using:

```
pip install -r requirements.txt
```

The communicating application entities (i.e. client and Sectra server) need to be configured before using the script.

To run the script then use:

```
python send_cstore.py /path/to/dicom/file.dcm
```


## Tested with

- DPAT 3.2 on 2024-06-27
