import json
import os
import shutil
import subprocess
from cgi import parse_header

import pandas as pd
import requests
from flask import Flask, request, jsonify
from requests_toolbelt.multipart import decoder
from utils import download_info, download_image, remove_folders

# TODO: change IP
IP = "<IP>"
APPLICATION_ID = "Feedback"

app = Flask(__name__)


@app.route('/feedback', methods=['GET'])
def handle_feedback_get_request():
    registration_response = jsonify({
        "applicationId": f"{APPLICATION_ID}",
        "displayName": "Feedback",
        "manufacturer": "HUG",
        "url": f"http://{IP}:5000/feedback",
        "inputTemplate": {"type": "wholeSlide"}
    })
    return registration_response


# should return info according to API doc
@app.route('/feedback/info', methods=['GET'])
def handle_feedback_get_info_request():
    info = jsonify({
        "apiVersion": "1.6",
        "softwareVersion": "1.0"
    })
    return info


# how user input are sent via sectra
@app.route('/feedback', methods=['POST'])
def handle_feedback_post_request():
    try:
        description = "Drag the patches to the appropriate category or select another category in the center of the viewer. Click on send feedback to send results."
        feedback_path = "feedback"
        data = request.json  # Get JSON data from the request

        action = data["action"]
        slideId = data["slideId"]
        token = data["callbackInfo"]["token"]
        header = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
        url = data["callbackInfo"]["url"]
        info = download_info(url, slideId, header)
        slideName = info["lisSlideId"]
        slideWidth = info["imageSize"]["width"]
        slideHeight = info["imageSize"]["height"]

        # verify that slide results are present
        if not os.path.isdir(f"{feedback_path}\\{slideName}"):
            return "Slide results folder not present.", 400

        feedback_csv = f"{feedback_path}\\{slideName}\\results\\{slideName}_patches.csv"

        if action != "cancel":
            df_feedback = pd.read_csv(feedback_csv)

            patches = []

            for index, row in df_feedback.iterrows():
                patch = {
                    "tag": row["tag"],
                    "position": {
                        "x": row["patch_center_x"],
                        "y": row["patch_center_y"]
                    },
                    "sortKeyValue": row["sort_key"]
                }
                patches.append(patch)

            # json for preprocessed result
            payload = {
                "slideId": slideId,
                "displayResult": "Analysis results",
                "data": {
                    "context": None,
                    "result": {
                        "type": "patchCollection",
                        "content": {
                            "description": description,
                            # polygon to be sent with gallery view result
                            "polygons": [
                                {
                                    "points": [
                                        {
                                            "x": 0,
                                            "y": 0
                                        },
                                        {
                                            "x": slideWidth,
                                            "y": 0
                                        },
                                        {
                                            "x": slideWidth,
                                            "y": slideHeight
                                        },
                                        {
                                            "x": 0,
                                            "y": slideHeight
                                        }
                                    ]
                                }
                            ],
                            "patches": patches,
                            "actions": [
                                {
                                    "id": "sendfeedback",
                                    "state": 0,
                                    "name": "Send feedback results",
                                    "tooltip": "Send feedback for predicted patches"
                                }
                            ],
                            "tags": [
                                "Positive",
                                "Negative",
                                "Positive (feedback)",
                                "Negative (feedback)"
                            ],
                            "patchSize": 100,
                            "magnification": 10,
                            "statuses": {
                                "allowVerify": {
                                    "value": True,
                                    "message": "Send feedback"
                                }
                            }
                        }
                    }
                }
            }

            header = {'Authorization': 'Bearer ' + token, 'X-Sectra-ApiVersion': '1.6',
                      'Content-Type': 'application/json'}
            # initial invocation
            if action == "create":
                payload_json = json.dumps(payload)
                response = requests.post(url + f"/applications/{APPLICATION_ID}/results", data=payload_json,
                                         verify=False,
                                         stream=True,
                                         headers=header)
                return response.json(), 200, header
            # update patch category and save feedback results via button
            elif action == "modify":
                # first button is saving feedback results
                if data['input']['data']['result']['content']['actions'][0]['state'] == 1:
                    for fn in ["TP", "FP", "FN", "TN"]:
                        #                     remove if already present
                        if os.path.isdir(f"{feedback_path}\\{slideName}\\{fn}"):
                            remove_folders(f"{feedback_path}\\{slideName}\\{fn}")
                        os.mkdir(f"{feedback_path}\\{slideName}\\{fn}")

                    new_patches = data['input']['data']['result']['content']['patches']
                    # move patches to appropriate feedback folder
                    for (_, patch), new_patch in zip(df_feedback.iterrows(), new_patches):
                        if patch['tag'] != new_patch['tag']:
                            img_name = os.path.basename(patch['img_name'])
                            # TP
                            if patch['label'] == 1 and new_patch['tag'] == 2:
                                shutil.copy(f"{feedback_path}\\{slideName}\\results\\{img_name}",
                                            f"{feedback_path}\\{slideName}\\TP\\{img_name}")
                            # FP
                            if patch['label'] == 1 and new_patch['tag'] == 3:
                                shutil.copy(f"{feedback_path}\\{slideName}\\results\\{img_name}",
                                            f"{feedback_path}\\{slideName}\\FP\\{img_name}")
                            # FN
                            if patch['label'] == 0 and new_patch['tag'] == 2:
                                shutil.copy(f"{feedback_path}\\{slideName}\\results\\{img_name}",
                                            f"{feedback_path}\\{slideName}\\FN\\{img_name}")
                            # TN
                            if patch['label'] == 0 and new_patch['tag'] == 3:
                                shutil.copy(f"{feedback_path}\\{slideName}\\results\\{img_name}",
                                            f"{feedback_path}\\{slideName}\\TN\\{img_name}")

                # update data and add Id for modify result
                newData = data['input']['data']
                resultId = data['input']['id']
                versionId = data['input']['versionId']
                payload["versionId"] = versionId
                payload["data"] = newData
                payload_json = json.dumps(payload)
                response = requests.put(url + f"/applications/{APPLICATION_ID}/results/" + str(resultId),
                                        data=payload_json,
                                        verify=False, stream=True,
                                        headers=header)
                return response.json(), 200, header
        return '', 200
    except Exception as e:
        return f"Error handling feedback for slide {slideName}: {e}", 400


if __name__ == '__main__':
    app.run(host=IP)
