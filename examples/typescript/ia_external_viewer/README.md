# Sectra DPAT IA-API Example: External Viewer

## About

Example of an external launch application that provides a simple WSI viewer. Intended to be use as a starting point for implementing custom viewers of results.

### Application function

An external launch application opens up in a web browser towards the specified url. The `launchUrl` query parameter contains a url that can be used to initate the IA-API communication. The example application consistst of a front end and a back end.

#### Front end

The front end is a Typescript React application:

- The IA-API is implemented in the `ImageAnalysisApiClient`.
- Images are rendered using OpenSeadragon.
- A simple thumbnail galery is used to navigate between slides in a case.
- Due to CORS, IA-API requests are not made directly to the DPAT server (as specified in the `launchUrl`) but instead towards the back end server, which proxies the requests.

#### Back end

The back end is a Python FastApi application. It proxies the requests from the front end to the DPAT server. After a succesfull launch request, the access token and callback url is stored in cookies for later requests.

## Configuration

### Add a image analysis external launch application

At `https:\\<dpat host>/SectraPathologyImport/config/externalapps` register a new `External Launch Application`. Give it the `Application Id` `dpat-ia-api-external-viewer` and `Display Name` `External Viewer`. Provide a value for the `Manufacturer`. Other settings can be left at default.

### Add an external launch command

In `Enterprise manager`, navigate to `Computers` and select either the `Default Computer Group` or the computer group you want the application to be avaiable for. Open `Properties` and the `External Applications` tab and create a new `External Launch Command`. Give the application a name and optionally a label. Select `Navigate to web adress in a browser` as `Action`. Set the url to the server serving the front end as `Link`. As `String appended to the link, when clicked` enter `?launchUrl=https%%3A%%2F%%2F<dpat host>%%2FSectraPathologyServer%%2Fexternal%%2Fimageanalysis%%2Fv1%%2Flaunchdata%%3FrequestId%%3D%acc_no%%%26sessionToken%%3D%user_session%`. Select the `Accession Number Groups` and `Medical Record Number Groups` the application should be usable for.

In IDS7, add a button to the application in the toolbar by right clicking on the toolbar and clicking `Add` on your application.

## Usage

See the README.md for the frontend and backend for how to start the viewer. Note that the documented way of running the application is not suitable for deployment.

Once started you can launch the viewer using the application button in IDS7.

