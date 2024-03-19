from flask import Flask, request, jsonify
import json
import pandas as pd
import requests

# launches server-side application to save tokens for API interaction, using PC IP and default 5000 port. The slide name, slide id
# callback url and token generated are saved in an excel sheet.

def download_info(callbackUrl, slideId, header):
    """
    Download slide information and returns a json of the response.
    """
    pull_info = requests.get(url=callbackUrl + "/slides/" + slideId+"/info?scope=extended&includePHI=true", verify=False, headers=header, stream=True)
    return pull_info.json()

IP = "<IP>"
token_file = "tokens.xlsx"


app = Flask(__name__)

@app.route('/Get_token', methods=['GET'])
def handle_get_token_get_request():
    registration_response = jsonify({
    "applicationId": "<applicationId>",
    "displayName": "Get token",
    "manufacturer": "HUG",
    "url": "http://<IP>:5000/Get_token",
    "inputTemplate":{"type":"wholeSlide"}
    })
    return registration_response

# should return info according to API documentation
@app.route('/Get_token/info', methods=['GET'])
def handle_get_token_get_info_request():
    info = jsonify({
    "apiVersion": "1.7",
    "softwareVersion": "1.0"
    })
    return info

@app.route('/Get_token', methods=['POST'])
def handle_get_token_post_request():
    data = request.json 
    
    slideId = data["slideId"]
    token = data["callbackInfo"]["token"]
    header = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    url = data["callbackInfo"]["url"]
    info = download_info(url, slideId, header)
    slideName = info["lisSlideId"]
    
    try:
        df = pd.read_excel(token_file)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["slide_name",  "slide_id",
                                   "url", "token"])

    new_slide = pd.Series({
    "slide_name": slideName,
    "slide_id": slideId,
    "url": url,
    "token": token
    })
    
    df = pd.concat([df, new_slide.to_frame().T], ignore_index=True)    

    df.to_excel(token_file, index=False)

    return '', 200

if __name__ == '__main__':
    app.run(host = IP)



