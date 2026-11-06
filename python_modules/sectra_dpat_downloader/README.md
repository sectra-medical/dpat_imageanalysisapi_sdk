# *Sectra DPAT downloader*

Simple client for downloading pathology images with Sectra Pathology Image Analysis API. Requires Sectra Pathology >4.1.

## Install

Using pip:

```shell
pip install .
```

## Configuration

An Image analysis application needs to be added at `host`/SectraPathologyImport/config/externalapps.

The user needs to have `Request Image Analysis Api Authentication Token` permission set in Enterprise manager.

## Usage

```python
from sectra_dpat_downloader import SectraDpatDownloader

client = SectraDpatDownloader.from_credentials(
    'base url', 'application id', 'user name', 'password'
)

api_info = client.get_api_info()  # api_version, software_version

images = client.get_images_in_case("accession number")
# Or, when only the id of one slide in the case is known:
images = client.get_images_in_case_of_slide("slide id")

for image in images:
    image_metadata = client.get_image_metadata(image.id)
    image_label = client.get_image_label(image.id)
    image_files = client.download_image_files(image.id, "output path")
```

Tiles are addressed as in the Deep Zoom (DZI) format, where level 0 is the image
as a single pixel and the full resolution is at
`ceil(log2(max(width, height)))` of the image size in the metadata:

```python
tile = client.get_tile(image.id, level, x, y, "jpg")
```

Results are stored per application. Attachments are declared in the result,
with state `new`, before they are uploaded; uploads larger than the chunk size
are sent in consecutive ranges:

```python
from sectra_dpat_downloader.result_models import Attachment, AttachmentState, Result

result = client.create_result(
    Result(
        slide_id=image.id,
        display_result="Result",
        application_version="1.0.0",
        attachments=[Attachment(name="data.bin", state=AttachmentState.NEW)],
    )
)
client.upload_result_attachment(str(result.id), "data.bin", "path/to/data.bin")
results = client.get_results_for_slide(image.id)
attachment = client.download_result_attachment(str(result.id), "data.bin", "output path")
```

To reuse an existing, configured HTTP client (for example a singleton managed
by a dependency injection container), construct the client directly with an
`HttpClient`:

```python
from sectra_dpat_downloader import SectraDpatDownloader
from sectra_dpat_downloader.http_client import HttpClient

http_client = HttpClient('base url', 'user name', 'password', 'application id')
client = SectraDpatDownloader(http_client, 'application id')
```

## CLI

```sh
sectra_dpat_downloader --help

Usage: sectra_dpat_downloader [OPTIONS]

  Download WSI images in exam from a server.

Options:
  --base-url TEXT                 Base URL of the server  [required]
  --application-id TEXT           Application ID for authentication
                                  [required]
  --username TEXT                 Username for authentication  [required]
  --password TEXT                 Password for authentication  [required]
  --accession-number TEXT         Accession number of exam  [required]
  --output-folder PATH            Folder to save the downloaded WSI image
                                  [required]
  --accession-number-issuer TEXT  Optional issuer of the accession number
  --metadata                      Include metadata for the downloaded images
  --threads INTEGER               Number of threads to use for downloading
                                  images
  --log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]
                                  Logging level
  --help                          Show this message and exit.
```

## Docker

A docker image can be built using the `Dockerfile`.

```sh
docker build -t sectra_dpat_downloader:latest .
```

The CLI is the entrypoint for the image.