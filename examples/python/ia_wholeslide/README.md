# Sectra DPAT IA-API Example: Background Processing

## About
Example of a fairly robust Sectra Image Analysis API (IA-API) implementation for a Server Side App.

The example consists of a `webserver.py` and workers started through `worker.py`

![Screenshot of app](https://github.com/user-attachments/assets/643ee890-26de-4662-962a-8b5f32625431)


### Demo Application function
The *webserver* implements the DPAT IA-API and will respond to user manually triggering analysis as well as automatic image notifications sent on image import.

Upon receiving a request, the webserver will immediately send an "in progress" result back which is visualized on the slide to the user (in the manual scenario) or to any user that opens the image (so it works for image notification requests as well).

The webserver writes a request to disk-based queue. If at least one `worker.py` is running, it will process these requests by

- Storing slide and case metadata
- Downloading and storing a thumbnail of the WSI and the slide label image
- Downloading the WSI file(s)
- Running a dummy processing job (time.sleep)
- Changing the in-progress result to the real proper result

During the above operations, the in-progress result is updated to reflect processing status to any user viewing the slide.

In order to process more requests at once, start more `worker.py` processes. To run them on multiple servers, ensure the queue directory is on a *samba* cifs fileshare (samba supports flock() needed for the queue locking).

Summary:

- Input: Image Notification push request, or user-triggered by selecting the app in the right-click context menu of a slide.
- Output: a graphical primitive (a square with a dummy computed answer)

### Development notes
Uses a simple flask server for responding to IA-API requests and a requests-based client for outgoing communications with the IA-API..

For simplicity, uses no async libraries.

For load-scaling, you need to mind incoming web request scaling and background workers.

For scaling the webserver, simply run with number of webserver processes corresponding to expected max number of simultaneous users. Tools such as gunicorn or a similar pre-forking server is recommended to spawn the webserver workers.
Should have no trouble scaling as long as number of max simultaneous users are below 1000 or so.

For worker scaling, run a number of workers corresponding so that compute resources on your node is maximized. If more are needed,
move the queue directory to a fileshare so that multiple machines can spawn worker processes and read it.

## Usage

In order to try this out you'll need to

1. Get the server and worker within this folder running (see Install and Run)
2. Configure Sectra DPAT adding the URL of the server to the list of configured IA-Apps (see Configuring the Sectra DPAT Server)

### Install and run

#### Prerequisites
We use astral `uv` for python dependency management. Please install it first. See https://docs.astral.sh/uv/ for more install options.

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Since the code uses file-based locks, **running multiple workers is only supported on Linux/POSIX-systems**.

#### Starting
Start the webserver:

```
./flask_run.sh
```

Starting one background worker process:

```
./worker_run.sh
```

### Configuring the Sectra DPAT Server

The webserver starts on 0.0.0.0 (all local ips) listening on port 5006.

You need to configure the Sectra Pathology Server (SPS) to call this server. This involves:

1. Ensuring that the SPS can reach this host over the network (ensure there is a route and that firewall rules allow it)
2. Registering the IA-API app in the configuration interface (see chapter 7 in the System Administrator Manual)
  - in brief: goto https://<pathologyserver>/sectrapathologyimport/config
  - log in, click Image Analysis Applications
  - Under Server Side Applications, click 'register new'
  - Enter the URL where your started web server (this repository) is running, as reachable from the pathology server. Example: `http://my-ia-app-server:5006/dpat_ia_app_demo/wholeslide`
  - Press 'Retrieve registration Info'
  - If you want to try Image Notifications, switch it to Enabled
    - NOTE! The app will receive notifications for all imported WSI and currently does not reject any based on metadata. Since the app downloads the WSI, you will receive a copy of all WSI on your app server.
  - The fields should be populated, press *Save*
  - Per default, the app is disabled. Click the 'disabled' button to toggle it to enabled.

If succesful, you should now be able to right-click in any Pathology Image and select your new IA-APP (you might need to refresh any running sessions).

### Development and Testing

You can manually (re)-process a single slide using the worker CLI.

```
$ python ./src/dpat_wholeslide/worker.py --help

Usage: worker.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  process  process single slide
  watch    start monitoring for WSI processing requests
```

Actually, the `worker_run.sh` script mentioned above just calls the `watch` subcommand of the worker cli.

The `webserver.py` process will create "slide folders" within `./data/requests` when a user calls the app. The watch process
monitors the folder for such files and automatically processes them. However, you can also run manually using the same info,
which is useful while you are developing your analysis code.

Example:
  - Only start the webserver, do not start any workers
  - Go to a slide and trigger your configured app
  - Note that a folder has been created below `./data/requests`, e.g. `./data/requests/AI-DRBR-290/A-HE-9adf3d8c20`
  - Now trigger processing on this folder:
    - Execute `uv run -- python ./src/dpat_wholeslide/worker.py ./data/requests/AI-DRBR-290/A-HE-9adf3d8c20`
  - Investigate the slide folder now and you'll note that it has the following files
    - `metadata.json` -- persisted metadata about the slide being processed
    - `thumbnail.jpg` -- a thumbnail of the slide
    - `label.jpg` -- the slide label image (if available, not all WSI have them)
    - a folder `wsi_files/` -- containing the entire WSI

## Changes needed to use in production

This example code is intended to get you started. Hence it avoids a few things you would need to do when using it for production

We suggest you at least:

- Ensure you scale webserver workers using a WSGI runner like gunicorn
- Ensure you clean up WSI files and metadata after some suitable period in your worker watch loop

## Tested with

- DPAT 3.4 on 2024-01-05
- DPAT 4.1 on 2024-11-21
