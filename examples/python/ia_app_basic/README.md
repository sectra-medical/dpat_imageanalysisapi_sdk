# Sectra DPAT IA-API Example: Basic App

## About
A very simple Sectra Image Analysis API (IA-API) implementation for a Server Side App.

The example is extremely barebone, with the goal to get you started and see that you manage to get the Sectra DPAT - App network connections functioning.

For a more realistic implementation where WSI processing is done in longer-running background jobs, see `../ia_wholeslide`

### Demo Application function

- Input: User draws a polygon around a region of interest ( taggedPolygon, see `webserver.py:app_return_registerinfo` )

- Output: a graphical primitive, or a "patch gallery" (see `webserver.py:DEMO_TYPE` and `webserver.py:app_on_userinput` )

**Screenshot**

![pcad_demo_2024-11-21_15-48-thumbnail](https://github.com/user-attachments/assets/51c2d8d6-a549-411a-bc56-38d866e80d60)

Screenshot shows an example patch gallery server side app in Sectra PACS. The featured slide is from the AIDA-DRBR dataset, see https://doi.org/10.23698/aida/drbr - used with permission.

### Development notes
Uses a simple flask server for responding to IA-API requests and a requests-based client for outgoing communications with the IA-API..

For simplicity, uses no async libraries.

For load-scaling, simply run with number of workers processes corresponding to expected max number of simultaneous users. Tools such as gunicorn or a similar pre-forking worker server is recommended to spawn the workers.

Should have no trouble scaling as long as number of max simultaneous users are below 1000 or so.

## Usage

In order to try this out you'll need to

1. Get the server within this folder running (see Install and Run)
2. Configure Sectra DPAT adding the URL of the server to the list of configured IA-Apps (see Configuring the Sectra DPAT Server)

### Install and run

#### Prerequisites
We use astral `uv` for python dependency management. Please install it first. See https://docs.astral.sh/uv/ for more install options.

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Starting

Start the webserver:

```
./flask_run.sh
```

### Configuring the Sectra DPAT Server

Running this demo starts a web server on 0.0.0.0 (all local ips) listening on port 5001.

You need to configure the Sectra Pathology Server (SPS) to call this server. This involves:

1. Ensuring that the SPS can reach this host over the network (ensure there is a route and that firewall rules allow it)
2. Registering the IA-API app in the configuration interface (see chapter 7 in the System Administrator Manual)
  - in brief: goto https://<pathologyserver>/sectrapathologyimport/config
  - log in, click Image Analysis Applications
  - Under Server Side Applications, click 'register new'
  - Enter the URL where your started web server (this repository) is running, as reachable from the pathology server. Example: `http://my-ia-app-server:5001/iademo`
  - Press 'Retrieve registration Info'
  - The fields should be populated, press *Save*
  - Per default, the app is disabled. Click the 'disabled' button to toggle it to enabled.

If succesful, you should now be able to right-click in any Pathology Image and select your new IA-APP (you might need to refresh any running sessions).

**Screenshot of configuration where app is running on the same machine as the server**

![edit_thumbnail](https://github.com/user-attachments/assets/4e10cb17-c7d9-462a-bc2c-810fc916770e)



## Tested with

- DPAT 3.4 on 2024-01-05
- DPAT 4.1 on 2024-11-21
