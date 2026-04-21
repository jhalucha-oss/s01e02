API Documentation (from help action):

Actions:
- help: requires [] - Show available actions and parameters.
- reconfigure: requires [route] - Enable reconfigure mode for the given route.
- getstatus: requires [route] - Get current status for the given route.
- setstatus: requires [route, value] - Set route status while in reconfigure mode. Allowed values: RTOPEN, RTCLOSE.
- save: requires [route] - Exit reconfigure mode for the given route.

Route format: [a-z]-[0-9]{1,2} (case-insensitive)
Status values mapping:
- RTOPEN -> open
- RTCLOSE -> close

Notes:
- To change status of the road, you must first set it to "reconfigure" mode.

(Logged response savedTo path: C:\\ZRODLA\\s01e02\\01_05_UNKNOWN_API\\post_verify_last.json)


Error Log (from failed request):
- Request: {"task":"railway","answer":{"action":"reconfigure","route":"X-01"}}
- Response: {"code": -985, "message": "API rate limit exceeded. Please retry later.", "retry_after": 23}
- Action taken: Waiting for retry_after period plus small buffer before retrying.


Request Log (successful reconfigure):
- Request: {"task":"railway","answer":{"action":"reconfigure","route":"X-01"}}
- Response: {"ok": true, "route": "X-01", "mode": "reconfigure", "status": "open", "message": "Reconfigure mode enabled for this route."}


Error Log (from failed setstatus request):
- Request: {"task":"railway","answer":{"action":"setstatus","route":"X-01","value":"RTOPEN"}}
- Response: {"code": -985, "message": "API rate limit exceeded. Please retry later.", "retry_after": 14}
- Action taken: Waiting for retry_after period plus small buffer before retrying.


Request Log (successful setstatus):
- Request: {"task":"railway","answer":{"action":"setstatus","route":"X-01","value":"RTOPEN"}}
- Response: {"ok": true, "route": "X-01", "mode": "reconfigure", "status": "open", "message": "Status updated."}


Error Log (from failed save request):
- Request: {"task":"railway","answer":{"action":"save","route":"X-01"}}
- Response: {"code": -985, "message": "API rate limit exceeded. Please retry later.", "retry_after": 13}
- Action taken: Waiting for retry_after period plus small buffer before retrying.


Final Response (save):
- Request: {"task":"railway","answer":{"action":"save","route":"X-01"}}
- Response: {"code": 0, "message": "{FLG:COUNTRYROADS}"}
- Action taken: Flag received and saved to flag.txt; full response logged to verify_response.json
