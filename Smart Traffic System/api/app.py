# api/app.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
from database.db import get_violations, init_db
import uvicorn
import logging
import traceback

app = FastAPI(title="Smart Traffic Violation API")

# Serve evidence images as static files and templates for the dashboard
app.mount("/static", StaticFiles(directory="evidence"), name="static")
jinja_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html", "xml"])
)

init_db()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        violations = get_violations()
        template = jinja_env.get_template("dashboard.html")
        html = template.render(
            request=request,
            violations=violations,
            title="Traffic Violation Dashboard"
        )
        return HTMLResponse(html)
    except Exception as e:
        logging.exception("Failed to render dashboard")
        tb = traceback.format_exc()
        return HTMLResponse(f"<h1>Internal Server Error</h1><pre>{tb}</pre>", status_code=500)

@app.get("/api/violations")
async def api_violations():
    """JSON API endpoint for future mobile apps"""
    violations = get_violations()
    return {"violations": violations, "count": len(violations)}

if __name__ == "__main__":
    uvicorn.run("api.app:app", host="127.0.0.1", port=8000, reload=True)