# Sectra Digital Pathology (DPAT) ImageAnalysis (IA) API - Software Development Kit (SDK)

## About
This repository provides examples on integrating with the Sectra IA-API using python code.

The `examples` folder provides two examples that are suitable to get started.
Coding style is intentionally minimalistic, aiming for quick and easy reading, as we expect downstream users to apply their own style and preferences.

The `python_modules` folder provides installable Python packages that are intended to be reused as-is.

## Python modules

### `sectra_dpat_downloader`

A small client and CLI for downloading whole slide images (WSI) and metadata, creating and updating analysis results, and setting quality control through the IA-API. Requires Sectra Pathology (DPAT) >= 4.1 (quality control requires >= 4.2).

See [`python_modules/sectra_dpat_downloader/README.md`](python_modules/sectra_dpat_downloader/README.md) for installation, configuration and full usage.

Quick start:

```python
from sectra_dpat_downloader import SectraDpatDownloader

client = SectraDpatDownloader.from_credentials(
    base_url="https://<host>/SectraPathologyServer/external/imageanalysis/v1",
    application_id="<application id>",
    username="<username>",
    password="<password>",
)

for image in client.get_images_in_case("<accession number>"):
    client.download_image_files(image.id, "<output folder>")
```

The package also installs a `sectra_dpat_downloader` CLI for downloading all images in a case:

```sh
sectra_dpat_downloader --help
```

## Contributing

We are open to accept contributions. This could be:

- typed clients (e.g. implementing the API specification as dataclasses)
- further examples (likely to be placed below a `contrib/` folder)

## Planned extensions

We plan on adding example code for integrating with IDS7 worklists by sending HL7v2 messages.

## Changelog

### 2026-06-16

- Add `sectra_dpat_downloader` Python module ( `python_modules/sectra_dpat_downloader` ) - client and CLI for downloading WSI images and metadata, managing analysis results, and setting quality control.

### 2024-11-20

- Add background image processing example ( `examples/python/ia_wholeslide` )
- Make the repository public

### 2024-06-13

- Update README - clarify planning

### 2024-01-05

- Added basic example `examples/python/ia_app_basic/` showing how an app can accept user input and return results for a specific sub-area of a WSI.
