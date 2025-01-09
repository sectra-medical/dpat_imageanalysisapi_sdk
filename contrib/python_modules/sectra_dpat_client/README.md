# Python Client for Sectra DPAT PACS

## Introduction

This python package aims to facilite the development of AI applications integrated in Sectra DPAT PACS.

Please note that for now, not every feature is implemented but the package can easily be enriched:

* Some endpoints are missing (e.g., slide downloading)
* QIDO client is pretty basic

### What it implements

* A client for the DPAT IA-API ("AI") API (`DPATAIClient`)
* A client for the DICOMWEB QIDO API (`DPATQidoClient`)
* A set of pydantic models to encapsulate and validate data sent and received from DPAT


### What it does not implement, but might, at some point

* A server to receive analysis requests from DPAT

## Installation

To install sectra_dpat_client (until it is published in pypi):

```pip install .```

To install sectra_dpat_client with development dependencies (linting and formating, see below):

```pip install ./[dev]```

## Usage

Before using the client, make sure you have access to a valid authentication token, sent in the analysis requests.

### Example 1: Retrieve image information

```python
from sectra_dpat_client.ai import DPATAIClient

# Callback info, sent by DPAT in the request
callback_url = "https://sectrapacs.com"
callback_token = "abc"

# Slide id, sent by DPAT in the request
slide_id = "blabla"

client = DPATAIClient(
    url=callback_url,
    token=callback_token
)

# Returns the image info with extended and personal health information data
image_info = client.get_image_info(slide_id, extended=True, phi=True)
```

### Example 2: Returning basic results

The following code creates a result payload that can be sent as response to display a frame on the whole slide and a label telling the user that the analysis is pending.

```python
from sectra_dpat_client.ai import (
    ResultContent,
    ResultType,
    PrimitiveItem,
    Style,
    Polygon,
    Point,
    Label,
    Result
)

# Slide id, sent by DPAT in the request
slide_id = "blabla"

data = ResultContent(
    type=ResultType.PRIMITIVES,
    content=[
        PrimitiveItem(
            style=Style(
                strokeStyle="#000000",
            ),
            polygons=[
                Polygon(
                    points=[
                        Point(x=0.0, y=0.0),
                        Point(x=1.0, y=0.0),
                        Point(x=1.0, y=1.0),
                        Point(x=0.0, y=1.0),
                    ]
                )
            ],
            labels=[
                Label(
                    location=Point(x=0.00, y=0.0),
                    label="Analysis running",
                )
            ],
        )
    ],
)

result = Result(
    slideId=slide_id,
    displayResult="Analysis running",
    applicationVersion="1.0.0",
    data=data
)
```

### Example 3: Retrieving patient, request and exam id

```python
from sectra_dpat_client.ai import DPATAIClient
from sectra_dpat_client.qido import DPATQidoClient, DicomCodes

# Callback info, sent by DPAT in the request
callback_url = "https://sectrapacs.com"
callback_token = "abc"

# Slide id, sent by DPAT in the request
slide_id = "blabla"

ai_client = DPATAIClient(
    url=callback_url,
    token=callback_token
)

# Returns the image info with extended and personal health information data
image_info = client.get_image_info(slide_id, extended=True, phi=True)

# Instanciates QIDO client with provided url, username and password
qido_client = DPATQidoClient(qido_url, qido_username, qido_password)

# Retrieve study from QIDO API
study = qido_client.find_one_study(studyInstanceUid=data.study_id)

# Retrieve patient, request and exam id from the response
patient_id = study.get_value_as_string(DicomCodes.PATIENT_ID)
request_id = study.get_value_as_string(DicomCodes.REQUEST_ID)
exam_id = study.get_value_as_string(DicomCodes.EXAM_ID)
```

### Error handling and retries

Any request to the DPAT server is retried 5 times with exponential delays if there is a connection error. Any other error is not handled by the clients.

Clients raise `DPATRequestError` if the DPAT server returns an error status code (e.g., 400, 404, 500, etc.). The error includes the returned status code, text and the requested path.

## Code quality

Code quality is ensured with the following tools:

* flake8 for formating
* mypy for static typing analysis
* bandit for security
* black for formating
* isort for imports order

One can format the code using the following command:

```make format```

One can lint the code using the following command:

```make lint```


## What's next?

* HL7 API client
* More detailed data validation (e.g., min and max lengths of arrays)
* Missing DPAT endpoints
