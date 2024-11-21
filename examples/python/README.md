# Sectra Digital Pathology ImageAnalysis (IA) API

## Getting started in python

This document outlines how we suggest you try the examples to get started using python.

### Prerequisites

- We assume you have a copy of the document *"Interface Specification: Pathology Image Analysis Application Interface, Sectra Digital Pathology Module"*. At the time of writing, the most recent version was *"Verion 4.1, August 2024"*.
  - This document describes all the REST endpoints and corresponding json schemas.
  - Contact Sectra support for a copy, see https://my.sectra.com/en-US/support-contact/

- You will need to have access to a Sectra PACS with the Digital Pathology module
  - We suggest you start testing in your testing Sectra PACS instance, if such an installatino is available to you.
    - You will need the appropriate permissions to add and configure IA Applications in that Sectra PACS, or be in contact with someone who has
  - For third party AI vendors, there is an online Sectra PACS available for a fee. Contact Sectra Support and request "discussing access to a test PACS for digital pathology AI vendors".

- You will need ensure TCP/IP connectivity between the Sectra PACS server and the machine running your IA-APP.
  - Both parties will initiate communications, so both servers need to be accessible to each other under appropiate DNS names.

- The python examples uses the `uv` package manager, see https://docs.astral.sh/uv/getting-started/installation/ for installation.

## 1. Starting the most basic app

See the README in `./ia_app_basic` for more detailed instructions, TLDR:

```
cd examples/python/ia_app_basic
./flask_run.sh
```

This starts a webserver listening on 0.0.0.0:5005 (all ips, port 5005) on the machine you started it on.

Next, you will need to register this with the Sectra PACS DPAT Server. For more detailed instructions, refer to Chapter 7 in the *System Administrator Manual*.

- Go to https://<pathologyserver>/sectrapathologyimport/config
  - log in, click Image Analysis Applications
  - Under Server Side Applications, click 'register new'
  - Enter the URL where your started web server (this repository) is running, as reachable from the pathology server.
    - Example: `http://my-ia-app-server:5001/iademo`
    - NOTE! Ensuring connectivity can take some work in most hospital environments.
  - Press 'Retrieve registration Info'
  - The fields should be populated, press *Save*
  - Per default, the app is disabled. Click the 'disabled' button to toggle it to enabled.

If succesful, you should now be able to right-click in any Pathology Image and select your new IA-APP (you might need to refresh any running sessions).

TODO: screenshot here of succesful operation
TODO: screenshot of configuration UI

## 2. A more realistic example

TODO: Writeme


