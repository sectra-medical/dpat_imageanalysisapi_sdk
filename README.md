# Sectra Digital Pathology (DPAT) ImageAnalysis (IA) API - Software Development Kit (SDK)

## About
This repository provides examples on integrating with the Sectra IA-API using python code.

The `examples` folder provides two examples that are suitable to get started.
Coding style is intentionally minimalistic, aiming for quick and easy reading, as we expect downstream users to apply their own style and preferences.

## Contributing

We are open to accept contributions. This could be:

- typed clients (e.g. implementing the API specification as dataclasses)
- further examples (likely to be placed below a `contrib/` folder)

## Planned extensions

We plan on adding example code for integrating with IDS7 worklists by sending HL7v2 messages.

## Changelog

### 2024-11-20

- Add background image processing example ( `examples/python/ia_wholeslide` )
- Make the repository public

### 2024-06-13

- Update README - clarify planning

### 2024-01-05

- Added basic example `examples/python/ia_app_basic/` showing how an app can accept user input and return results for a specific sub-area of a WSI.
