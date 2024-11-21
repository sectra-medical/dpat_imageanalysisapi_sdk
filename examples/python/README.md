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

The basic app is a very minimal example to demonstrate how the user might interact with your app and the different result types available.

See the README in [ia_app_basic](https://github.com/sectra-medical/dpat_imageanalysisapi_sdk/blob/main/examples/python/ia_app_basic/README.md) for more detailed instructions, TLDR:

```
cd examples/python/ia_app_basic
./flask_run.sh
```

See the README linked above for how to configure the Sectra DPAT module to connect. 

Once you have succesfully got this basic app working inside the Sectra Pathology module, we strongly suggest you proceed with adopting the practices in the second example below.

## 2. Realistic example - background processing
Since WSI are huge, they take time processing. This means you will need to answer the user request quickly and then submit the slide for background processing.

After getting familiar with the basic app, see [ia_wholeslide](https://github.com/sectra-medical/dpat_imageanalysisapi_sdk/blob/main/examples/python/ia_wholeslide/README.md) for a more realistic example.

