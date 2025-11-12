from datetime import datetime, timedelta, timezone
from flask import Flask, request, Response, stream_with_context
from flask_cors import CORS
import main as bw_main
import os
import pandas as pd

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def add_cors_headers(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp

def parse_iso_datetime(s: str) -> datetime:
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

@app.route("/download", methods=["GET", "POST", "OPTIONS"])
def download():
    if request.method == "OPTIONS":
        return ("", 204)
    start_param = request.values.get("start") or request.values.get("datetime")
    end_param = request.values.get("end")

    if not start_param:
        return {"error": "Missing required parameter 'start' (ISO datetime)"}, 400

    try:
        start_dt = parse_iso_datetime(start_param)
    except Exception as e:
        return {"error": f"Invalid start datetime: {e}"}, 400

    if end_param:
        try:
            end_dt = parse_iso_datetime(end_param)
        except Exception as e:
            return {"error": f"Invalid end datetime: {e}"}, 400
    else:
        end_dt = start_dt + timedelta(days=1)

    start_iso = start_dt.isoformat().replace("+00:00", "Z")
    end_iso = end_dt.isoformat().replace("+00:00", "Z")

    query_name = os.getenv("BW_QUERY_NAME")
    filename = f"mentions_{start_dt.strftime('%Y%m%dT%H%M%S')}.csv"

    def generator():
        first = True
        for page in bw_main.iter_mentions_pages(name=query_name, startDate=start_iso, endDate=end_iso, pagesize=5000):
            if not page:
                continue
            df = pd.json_normalize(page)
            csv_chunk = df.to_csv(index=False, header=first)
            first = False
            yield csv_chunk

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return Response(stream_with_context(generator()), mimetype="text/csv", headers=headers)

@app.route("/", methods=["GET"])
def index():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)), debug=False)
