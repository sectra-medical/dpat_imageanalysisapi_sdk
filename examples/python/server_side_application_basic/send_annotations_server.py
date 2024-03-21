from flask import Flask, request, jsonify
import json
import pandas as pd
import requests
import os

from requests_toolbelt.multipart import decoder
from cgi import parse_header

def download_picture(outputPath,callbackUrl, slideId, header,anonym_name):
    """
    Download image from Sectra into the specified path with specified name.
    """
    folder_path = os.path.normpath(os.path.join(outputPath, anonym_name))
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
        print(f"Directory '{folder_path}' created successfully.")
    else:
        print(f"Directory '{folder_path}' already exists. Image not downloaded.")
        return os.path.normpath(os.path.join(outputPath,anonym_name))
    pull_dcm = requests.get(url=callbackUrl + "/slides/" + slideId + "/files", verify=False, headers=header, stream=True) #CAVE: downloaded images are NOT anonymized
    decoder_mime = decoder.MultipartDecoder.from_response(pull_dcm)
    for part in decoder_mime.parts:
        _, dict = parse_header(str(part.headers[b"content-disposition"]))
        filename, size = str.strip(dict["filename"], "'\""), len(part.content)
        with open(os.path.normpath(os.path.join(outputPath,anonym_name,filename)), "wb") as file:
            file.write(part.content)
    return os.path.normpath(os.path.join(outputPath,anonym_name))

def download_info(callbackUrl, slideId, header):
    """
    Download slide information and returns a json of the response.
    """
    pull_info = requests.get(url=callbackUrl + "/slides/" + slideId+"/info?scope=extended&includePHI=true", verify=False, headers=header, stream=True)
    return pull_info.json()

def unnormalize_point_coordinates(points, slide_width):
    """
    Multiply points coordinates by image width to get level 0 coordinates from Sectra coordinates.
    """
    return [{"x": point["x"] * slide_width, "y": point["y"] * slide_width} for point in points]


IP = "<IP>"

app = Flask(__name__)

@app.route('/send_annotation', methods=['GET'])
def handle_annotation_get_request():
    registration_response = jsonify({
    "applicationId": "sendAnnotations",
    "displayName": "Send annotations",
    "manufacturer": "HUG",
    "url": "http://<IP>:5000/send_annotation",
    "inputTemplate": {
        "type": "taggedPolygon",
        "content": {
            "tags": [
                "Tag1",
                "Tag2",
            ]
        }
    },
    })
    return registration_response


@app.route('/send_annotation/info', methods=['GET'])
def handle_annotation_get_info_request():
    info = jsonify({
    "apiVersion": "1.6",
    "softwareVersion": "1.0"
    })
    return info


@app.route('/send_annotation', methods=['POST'])
def handle_annotation_post_request():
    csv_file_path = "annotations.xlsx"
    images_path = "annotated_slides"
    data = request.json
  
    action = data["action"]

    #only run on initial app invocation
    if action == "create":
        if not os.path.exists(images_path):
            os.mkdir(images_path)
            print(f"Directory '{images_path}' created successfully.")
        else:
            print(f"Directory '{images_path}' already exists.")
        
        slideId = data["slideId"]
        token = data["callbackInfo"]["token"]
        header = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
        url = data["callbackInfo"]["url"]
        info = download_info(url, slideId, header)
        slide_name = info["lisSlideId"]
        slide_width = info["imageSize"]["width"]

        points = data["input"]["content"]["polygon"]["points"]
        unnormalized_points = unnormalize_point_coordinates(points, slide_width)

        tagIndex = data["input"]["content"]["tagIndex"]
        tags = data["input"]["content"]["tags"]
        tag = tags[tagIndex]

        try:
            df = pd.read_excel(csv_file_path)
        except FileNotFoundError:
            df = pd.DataFrame(columns=["slide_name", "slide_id", "points", "unnormalized_points", "tag"])

        new_slide = pd.Series({
            "slide_name": slide_name,
            "slide_id": slideId,
            "points": points,
            "unnormalized_points": unnormalized_points,
            "tag": tag,
        })


        df = pd.concat([df, new_slide.to_frame().T], ignore_index=True)

        df.to_excel(csv_file_path, index=False)

        download_picture(images_path,url, slideId, header,slide_name)

        payload = {
            "slideId": slideId,
            "displayResult": tag,
            "data": {
                "context": None,
                "result": {
                    "type": "primitive",
                    "content": [
                        {
                            "polygons": [
                                {"points": points}
                            ],
                            "style": {
                                "fillStyle": None,
                                "size": 3,
                                "strokeStyle": "#006400"
                            }
                        }
                    ]
                }
            }
        }


        payload = json.dumps(payload)
        header = {'Authorization': 'Bearer ' + token, 'X-Sectra-ApiVersion': '1.6', 'Content-Type': 'application/json'}

        requests.post(url + "/applications/<applicationId>/results", data=payload, verify=False, stream=True,
                 headers=header)

    return '', 200


if __name__ == '__main__':
    app.run(host = IP)









