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

images = client.get_images_in_case("accession number")

for image in images:
    image_metadata = client.get_image_metadata(image.id)
    image_label = client.get_image_label(image.id)
    image_files = client.download_image_files(image.id, "output path")
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