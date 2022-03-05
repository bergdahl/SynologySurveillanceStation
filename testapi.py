import requests, json

# Synology API url
api_url = 'https://nas.local:5001/webapi/'
username = 'USERNAME'
password = 'PASSWORD!'
# Verify SSL certificate or not, default true 
verify_ssl = False
# Timeout in seconds, default 10
timeout = 10
SYNO_Errors = {
    100: "Unknown error",
    101: "Invalid parameters",
    102: "API does not exist",
    103: "Method does not exist",
    104: "This API version is not supported",
    105: "Insufficient user privilege",
    106: "Connection time out",
    107: "Multiple login detected"
}
SYNO_AUTH_Errors = {
    100: 'Unknown error.',
    101: 'The account parameter is not specified.',
    400: 'Invalid password.',
    401: 'Guest or disabled account.',
    402: 'Permission denied.',
    403: 'One time password not specified.',
    404: 'One time password authenticate failed.',
    405: 'App portal incorrect.',
    406: 'OTP code enforced.',
    407: 'Max Tries (if auto blocking is set to true).',
    408: 'Password Expired Can not Change.',
    409: 'Password Expired.',
    410: 'Password must change (when first time use or after reset password by admin).',
    411: 'Account Locked (when account max try exceed).'
}

SYNO_API_Info_Query = "query.cgi?api=SYNO.API.Info&method=Query&version=1&query=SYNO.API.Auth,SYNO.SurveillanceStation.Camera"
SYNO_API_Auth_Prefix = "auth.cgi"

requests.packages.urllib3.disable_warnings()
success = False

def print_error(info, errors):
    errorcode = info["error"]["code"]
    print("ERROR: ", end='')
    print(errors[errorcode])
    print("JSON : ", end='')
    print(info)

print("========================================")
print("Querying the SYNO.API.Info endpoint")
resp = requests.get(api_url + SYNO_API_Info_Query, verify=False)
if resp.status_code == 200:
    info = json.loads(resp.content)
    success = info['success']
    if success:
        print("Got info for commands:")
        for name in info["data"]:
            print(f'{name}: {info["data"][name]["path"]}')
        # Parse Auth
        SYNO_API_Auth_Prefix = info["data"]["SYNO.API.Auth"]['path']
        SYNO_API_Camera_Prefix = info["data"]["SYNO.SurveillanceStation.Camera"]['path']
        SYNO_API_Auth_Query = SYNO_API_Auth_Prefix + "?api=SYNO.API.Auth&method=login&version=7&account=" + username + "&passwd=" + password + "&session=SurveillanceStation&format=sid"
    else:
        print_error(info, SYNO_Errors)
if success:
    print("----------------------------------------")
    print("Login via the SYNO.API.Auth endpoint")
    # Now do login and get sid
    # GET /webapi/auth.cgi?api=SYNO.API.Auth&method=login&version=1&account=admin&passwd=123456&session=SurveillanceStation
    resp = requests.get(api_url + SYNO_API_Auth_Query, verify=False)
    info = json.loads(resp.content)
    success = info['success']
    if success:
        sid = info["data"]["sid"]
        print(f'SID   : {sid}')
        SYNO_API_Camera_Query = SYNO_API_Camera_Prefix + "?api=SYNO.SurveillanceStation.Camera&method=List&basic=true&version=1&_sid=" + sid
        pass
    else:
        print_error(info, SYNO_AUTH_Errors)
if success:
    print("----------------------------------------")
    print("List cameras via the SYNO.API.Camera endpoint")
    # GET /webapi/entry.cgi?api=SYNO.SurveillanceStation.Camera&method=List&version=1&start=10&limit=3&_sid=”Jn5dZ9aS95wh2”
    resp = requests.get(api_url + SYNO_API_Camera_Query, verify=False)
    info = json.loads(resp.content)
    success = info['success']
    if success:
        cameras = info["data"]["cameras"]
        for camera in cameras:
            print(f'Camera         : {camera["name"]} (id: {camera["id"]})')
            print(f'Cam IP         : {camera["detailInfo"]["camIP"]}')
            print(f'Snapshot path  : {camera["snapshot_path"]}')

            # Now get urls for the camera
            id = str(camera["id"])
            get_live_view_url = "entry.cgi?api=SYNO.SurveillanceStation.Camera&method=GetLiveViewPath&version=9&idList=" + id + "&_sid=" + sid
            resp = requests.get(api_url + get_live_view_url, verify=False)
            info = json.loads(resp.content)
            print(info)
            for item in info["data"]:
                print(f'MJPEG HTTP      : {item["mjpegHttpPath"]}')
                print(f'MXPEG HTTP      : {item["mxpegHttpPath"]}')
                print(f'RTSP            : {item["rtspPath"]}')
                print(f'RTSP Multicast  : {item["multicstPath"]}')
                print(f'RTSP over HTTP  : {item["rtspOverHttpPath"]}')
        pass
    else:
        print_error(info, SYNO_Errors)

