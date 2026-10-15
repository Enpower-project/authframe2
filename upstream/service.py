from fastapi import FastAPI, Request, HTTPException
from typing import Dict

app = FastAPI()

# Mock dataset
REPORTS = {
    "r_1": {"id": "r_1", "title": "Project A Report", "content": "Sensitive data..."},
    "r_2": {"id": "r_2", "title": "Project B Report", "content": "Internal data only."},
}

@app.get("/reports/{report_id}")
async def get_report(report_id: str, request: Request):
    user = request.headers.get("x-user", "anonymous")
    print(f"Access granted by Envoy for {user} to report {report_id}")
    report = REPORTS.get(report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    return {"user": user, "report": report}
