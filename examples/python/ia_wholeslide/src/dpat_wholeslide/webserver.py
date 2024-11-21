import json
import traceback
import hashlib

from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify

from dpat_wholeslide.version import (
    __version__,
    SECTRA_IA_API_MIN_VERSION,
)
from dpat_wholeslide.utils import requests_session_from_callbackinfo

app = Flask(__name__)

APP_NAME = "demo-wholeslide"
APP_MANUFACTURER = "Sectra (demo)"
BIND_PORT = 5006

# -------- Utils --------

def json_resp(data):
    """serialize response data to JSON and add appropriate IA-api headers"""
    resp = jsonify(data)
    resp.headers.set("X-Sectra-ApiVersion", SECTRA_IA_API_MIN_VERSION)
    resp.headers.set("X-Sectra-SoftwareVersion", __version__)
    return resp

# -----------------------

@app.route("/", methods=["GET"])
def index():
    """
    Just a hello world page. The json is not part of the Sectra API.
    Useful for debugging a running service.
    """
    return json_resp(
        [
            {
                "name": APP_NAME,
                "version": __version__,
                "route": "/dpat_ia_app_demo/wholeslide",
                "sectra-apiversion": SECTRA_IA_API_MIN_VERSION,
            }
        ]
    )


# IA-API Implementation
# =====================

@app.route("/dpat_ia_app_demo/wholeslide/info", methods=["GET"])
def app_return_info():
    """
    route returning application info according to the DPAT IA API specification
    """
    data = {
        "apiVersion": SECTRA_IA_API_MIN_VERSION,
        "softwareVersion": __version__
    }
    return json_resp(data)

@app.route("/dpat_ia_app_demo/wholeslide", methods=["GET"])
def app_return_registerinfo():
    """
    route for user-assisted registration in the SectraPathologyImport/config UI

    This URL is what should go into the configure URL
    """
    hostname = f"127.0.0.1:{BIND_PORT}"
    if "Host" in request.headers:
        # return whatever hostname the requesting client sent to us
        # so if the user types in http://some-hostname/dpat_ia_app_demo/wholeslide
        # we return that same hostname
        hostname = request.headers["Host"]

    # NOTE: as of DPAT 3.4 / IA-API v1.8 this will prepopulate all fields in the registration
    #       **except** Image Notifications. So if you need Notifications you must tell the admin who configs the application
    #       to enable it (click the checkbox when registering).
    data = {
        "applicationId": APP_NAME,
        "displayName": APP_NAME,
        "url": f"http://{hostname}/dpat_ia_app_demo/wholeslide",
        "manufacturer": APP_MANUFACTURER,
        "inputTemplate": {"type": "wholeSlide"},
        "context": {},
    }
    return json_resp(data)


@app.route("/dpat_ia_app_demo/wholeslide", methods=["POST"])
def app_on_userinput():
    """
    Dispatch (routing) for user operations.

    This route is called when the app is activated by the user through the right-click context menu
    """
    response = {}
    data = request.get_json()

    # data['action'] :: create, modify, delete, cancel
    if data["action"] == "create":
        # called when user selects this app from interactive menu
        return app_add_wsi_to_processing_queue(data)
    elif data["action"] == "modify":
        # this is never called for our app since we dont return modifiable results
        pass
    elif data["action"] == "delete":
        # called when user deletes annotation (result) created by this app
        return app_delete(data)
    elif data["action"] == "cancel":
        return json_resp([])
    return json_resp(response)


@app.route("/dpat_ia_app_demo/wholeslide/imagenotification", methods=["POST"])
def app_on_imagenotification():
    data = request.get_json()
    app_add_wsi_to_processing_queue(data)
    # specification says we should return 200, empty
    return json_resp({})

# =========================================

def app_add_wsi_to_processing_queue(data):
    """
    request processing of one WSI.

    persist basic metadata about the WSI and the auth token to disk, so that workers can process it further in the background
    (see worker.py)
    """
    slide_id = data["slideId"]

    # fetch basic slide metadata
    api = requests_session_from_callbackinfo(data['callbackInfo'])
    r = api.get(f"slides/{slide_id}/info?scope=extended&includePHI=true")
    r.raise_for_status() # raise on error
    metadata = r.json()

    # persist user request in a file-based queue
    # in this example we use PHI data since it makes the app easier to debug/test -- because it gives
    # stable human-readble identities. However,
    # for production apps we strongly suggest only using <slide_id>
    case_name = metadata["accessionNumber"]
    block_name = metadata["block"]["displayName"]
    stain_name = metadata["staining"]["displayName"]
    stable_slide_id = hashlib.sha1(f"{metadata['seriesInstanceUid']}".encode("UTF-8")).hexdigest()[:10]

    # write metadata to a requests folder
    data_folder = Path(f"./data/requests/{case_name}/{block_name}-{stain_name}-{stable_slide_id}")
    data_folder.mkdir(parents=True, exist_ok=True)

    metadata_filename = data_folder/"metadata.json"
    with open(metadata_filename, 'w') as file:
        json.dump(metadata, file)

    save_filename = data_folder/f"request_user-{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    with open(save_filename, 'w') as file:
        json.dump(data, file)

    # also write a file in a flat queue folder, this folder will represent
    # the "active" queue and the data folder can be a larger repository of all requests
    queue_folder = Path("./data/queue")
    queue_folder.mkdir(parents=True, exist_ok=True)
    slide_queue_file = queue_folder/f"{case_name}-{block_name}-{stain_name}-{stable_slide_id}.txt"
    slide_queue_file.write_text(f"../../{save_filename}\n") # persist a "link" to the most recent metadata


    # prepare to store a progress label visible to users
    text = "analysis queued"
    max_y = metadata["imageSize"]["height"] / metadata["imageSize"]["width"]
    store_data = {
        "slideId": data["slideId"],
        "displayResult": text,  # text as shown in the annotation list (L)
        "displayProperties": {
            # table-style properties shown when the annotation is selected
            "Progress": "0 %"
        },
        "applicationVersion": __version__,
        "data": {
            "context": {},
            "result": {
                "type": "primitive",
                "content": {
                    "style": {"fillStyle": None, "size": None, "strokeStyle": "#FFA500"},
                    "polygons": [{"points": [{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 0.0}, {"x": 1.0, "y": max_y}, {"x": 0.0, "y": max_y}]}],
                    "labels": [
                        # place label at the top center
                        {"location": {"x": 0.5, "y": 0.0}, "label": text}
                    ],
                },
            }
        },
    }

    # check if there is already an app result from our app for this slide
    # since apps cannot DELETE their own results, we modify the existing one to avoid
    # creating a new one every time
    r = api.get(f"applications/{data['applicationId']}/results/slide/{data['slideId']}")
    r.raise_for_status()
    existing_annots = r.json()
    if len(existing_annots) > 0:
        latest_annot = existing_annots[-1]
        latest_annot.update(store_data)
        response = api.put(f"applications/{data['applicationId']}/results/{latest_annot['id']}", json=latest_annot)
    else:
        response = api.post(f"applications/{data['applicationId']}/results/", json=store_data)
    response.raise_for_status()
    # the response we get back is in a suitable format for passing back to the caller
    return json_resp(response.json())


def app_delete(data):
    """result has been deleted by the user, and our app is informed"""
    # do not intervene (will get the result deleted)
    return json_resp({})


# ============================================================
# below code is to support running this through ./webserver.py
# ============================================================


# set default exception handler
def defaultHandler(e):
    code = 500
    if hasattr(e, "code"):
        code = e.code
    print("--- error ---")
    print("ERROR:", str(e))
    traceback.print_tb(e.__traceback__)
    return json.dumps({"error": str(e)}), code


app.config["TRAP_HTTP_EXCEPTIONS"] = True
app.register_error_handler(Exception, defaultHandler)

if __name__ == "__main__":
    app.run(port=BIND_PORT, debug=True)
