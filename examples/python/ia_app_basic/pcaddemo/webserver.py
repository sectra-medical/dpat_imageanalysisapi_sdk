import os
import json
import traceback
from functools import reduce

from flask import Flask, request, jsonify

from pcaddemo.version import (
    __version__,
    SECTRA_IA_API_MIN_VERSION,
    SECTRA_IA_API_MAX_VERSION,
)
from pcaddemo.geometry import sectra_polygon_to_shapely, random_point_in_polygon
from pcaddemo.analysisapi import AnalysisApi

app = Flask(__name__)

APP_NAME = "ImageAnalysisDemo"
APP_MANUFACTURER = "Sectra (demo)"
BIND_PORT = 5005


def json_resp(data):
    """serialize data to JSON and add appropriate IA-api headers"""
    resp = jsonify(data)
    resp.headers.set("X-Sectra-ApiVersion", SECTRA_IA_API_MIN_VERSION)
    resp.headers.set("X-Sectra-SoftwareVersion", __version__)
    return resp


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
                "route": "/iademo",
                "sectra-apiversion": SECTRA_IA_API_MIN_VERSION,
            }
        ]
    )


# IA-API Implementation
# =====================


@app.route("/iademo", methods=["GET"])
def app_return_registerinfo():
    """
    route for user-assisted registration in the SectraPathologyImport/config UI

    This URL is what should go into the configure URL
    """
    hostname = f"127.0.0.1:{BIND_PORT}"
    if "Host" in request.headers:
        hostname = request.headers["Host"]

    # NOTE: as of DPAT 3.4 / IA-API v1.8 this will prepopulate all fields in the registration
    #       except Image Notifications. So if you need Notifications you must tell the admin who configs the application
    #       to enable it.
    data = {
        "applicationId": APP_NAME,
        "displayName": APP_NAME,
        "url": f"http://{hostname}/iademo",
        "manufacturer": APP_MANUFACTURER,
        "inputTemplate": {"type": "taggedPolygon", "content": {"tags": []}},
        "context": {"gallery": False},
    }
    return json_resp(data)


@app.route("/iademo", methods=["POST"])
def app_on_userinput():
    """
    Dispatch (routing) for user operations.

    This route is called when the app is activated by the user
    who then draws (creates), modifies or deletes an area (taggedPolygon)

    Additionally, the same route is called when the user clicks buttons
    in the patchCollection-type result.
    """
    response = {}
    data = request.get_json()

    save_filename = f"./debug/userinput_{data['action']}_tmp.json"
    with open(save_filename, "w") as file:
        json.dump(data, file)

    # data['action'] :: create, modify, delete, cancel
    if data["action"] == "create":
        use_patch_gallery = "gallery" in data["context"] and data["context"]["gallery"]
        if use_patch_gallery:
            return app_create_patchCollection(data)
        else:
            return app_create_primitiveArea(data)
    elif data["action"] == "modify":
        for button in data["input"]["data"]["result"]["content"]["actions"]:
            if button["state"] == 1:
                # this is a button press
                button["state"] = 0  # reset the button so dispatch doesn't need to know
                return app_modify_button(button["id"], data)
        # user modified a previously created result
        return app_modify(data)
    elif data["action"] == "delete":
        return app_delete(data)
    elif data["action"] == "cancel":
        return json_resp([])
    return json_resp(response)


def app_create_primitiveArea(data):
    """
    user wants a result for a given input area

    this demo implementation simply returns the input geometry with a label attached
    """
    # this demo app supports being configured as either type: multiArea or type: taggedPolygon
    input_polygons = []
    if data["input"]["type"] == "taggedPolygon":
        input_polygons = [data["input"]["content"]["polygon"]]
    elif data["input"]["type"] == "multiArea":
        input_polygons = data["input"]["content"]["polygons"]

    # determine suitable label placement (choose uppermost point in polygon)
    all_points = [pt for polyg in input_polygons for pt in polyg["points"]]
    min_y_pt = reduce(lambda pt1, pt2: pt2 if pt2["y"] < pt1["y"] else pt1, all_points)

    text = "0 demo-positive cells found."

    response_result = {
        "type": "primitive",
        "content": {
            "style": {"fillStyle": None, "size": None, "strokeStyle": "#FFA500"},
            "polygons": input_polygons,  # same area as user input,
            "labels": [{"location": min_y_pt, "label": text}],
        },
    }

    # note : result returned must have database id, so we are responsible for storing this to server
    server_api = AnalysisApi(
        data["callbackInfo"]["url"],
        data["applicationId"],
        token=data["callbackInfo"]["token"],
        api_version=SECTRA_IA_API_MIN_VERSION,
    )
    store_data = {
        "slideId": data["slideId"],
        "displayResult": text,  # text as shown in the annotation list (L)
        "displayProperties": {"Cell Count": "0 cells"},
        "applicationVersion": __version__,
        "data": {"context": None, "result": response_result},
    }
    response = server_api.store_result(store_data)
    # the response we get back is in a suitable format for passing back to the caller
    return json_resp(response)


def app_create_patchCollection(data):
    """
    user wants a result for a given input area

    this demo implementation returns a patch gallery with 10 random points
    """
    input_polygon = data["input"]["content"]["polygon"]
    plg = sectra_polygon_to_shapely(input_polygon)
    random_points = [random_point_in_polygon(plg) for _x in range(0, 10)]
    patches = [
        # tag: 0 is "A" (index into tags definition below)
        # sortKeyValue determines the order of patches in the UI
        {"tag": 0, "position": {"x": p.x, "y": p.y}, "sortKeyValue": 1.0}
        for p in random_points
    ]

    response_result = {
        "type": "patchCollection",
        "content": {
            "polygons": [input_polygon],
            "patches": patches,
            "tags": ["A", "B", "C"],  # these are the categories the user can change
            "description": "App Description",
            "magnification": 10,  # zoom level to get the patch in
            "patchSize": 64,  # size in pixels of each patch
            "statuses": {"allowVerify": {"value": True, "message": "allowed."}},
            "actions": [
                # these are buttons user can click
                {"id": "mycmd", "state": 0, "name": "MyCmd", "tooltip": "execute MyCmd"}
            ],
        },
    }
    # note : patchCollection result returned must have database id,
    #        so must store this to server
    server_api = AnalysisApi(
        data["callbackInfo"]["url"],
        data["applicationId"],
        token=data["callbackInfo"]["token"],
        api_version=SECTRA_IA_API_MIN_VERSION,
    )
    store_data = {
        "slideId": data["slideId"],
        "displayResult": "myText",
        "displayProperties": {"Cell Ratios": "10/0/0 (A/B/C)"},
        "resultVersion": "1.0",
        "data": {"context": None, "result": response_result},
    }
    response = server_api.store_result(store_data)
    return json_resp(response)


def app_modify(data):
    """result has been modified by user"""
    # just store the updated result on the server and send back to user
    server_api = AnalysisApi(
        data["callbackInfo"]["url"],
        data["applicationId"],
        token=data["callbackInfo"]["token"],
        api_version=SECTRA_IA_API_MIN_VERSION,
    )
    response = server_api.update_result(data["input"])
    return json_resp(response)


def app_modify_button(button_id, data):
    """when button in patch gallery is pressed by user"""
    print("button-press", button_id)
    return json_resp(data["input"])


def app_delete(data):
    """result has been deleted by the user, and our app is informed"""
    # do not intervene (will get the result deleted)
    # TODO: server does not like empty response any more?
    return json_resp({})


# easy test and run setup
# =======================


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
