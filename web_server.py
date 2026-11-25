# ─────────────────────────────────────────────
#  web_server.py
#  FastAPI server for the 2D Pixel Browser Edition
#  Run:  python web_server.py
#   or:  python main.py --web
# ─────────────────────────────────────────────

import os
import uuid
import webbrowser
from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from engine.web_bridge import WebSession

app = FastAPI(title="The Viscount's Vigil — 2D Pixel Edition")

_SESSIONS: Dict[str, WebSession] = {}

WEB_DIR = os.path.join(os.path.dirname(__file__), "web")
os.makedirs(WEB_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


def _get_session(session_id: str) -> WebSession:
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = WebSession()
    return _SESSIONS[session_id]


class TalkReq(BaseModel):
    session_id: str
    npc_id: str
    message: str


class ActionReq(BaseModel):
    session_id: str
    target: str = ""


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


@app.post("/api/new_game")
def new_game():
    sid = str(uuid.uuid4())
    sess = WebSession()
    _SESSIONS[sid] = sess
    return {"session_id": sid, "state": sess.snapshot()}


@app.post("/api/advance_prologue")
def advance_prologue(req: ActionReq):
    sess = _get_session(req.session_id)
    return sess.advance_prologue()


@app.post("/api/finish_act0")
def finish_act0(req: ActionReq):
    sess = _get_session(req.session_id)
    return sess.finish_act0()


@app.post("/api/enter_hall")
def enter_hall(req: ActionReq):
    sess = _get_session(req.session_id)
    return sess.enter_hall_act2()


@app.post("/api/visit_station")
def visit_station(req: ActionReq):
    sess = _get_session(req.session_id)
    return sess.visit_station(req.target)


@app.post("/api/inspect_cellar")
def inspect_cellar(req: ActionReq):
    sess = _get_session(req.session_id)
    return sess.inspect_cellar(req.target)


@app.post("/api/talk")
def talk(req: TalkReq):
    sess = _get_session(req.session_id)
    return sess.talk(req.npc_id, req.message)


@app.post("/api/start_act3")
def start_act3(req: ActionReq):
    sess = _get_session(req.session_id)
    return sess.start_act3()


@app.post("/api/act3_action")
def act3_action(req: TalkReq):
    sess = _get_session(req.session_id)
    return sess.act3_action(req.message)


def launch(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True):
    url = f"http://{host}:{port}"
    print(f"\n  Launching The Viscount's Vigil (2D Pixel Edition) at {url}")
    print("  Terminal edition remains unchanged via: python main.py\n")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    launch()
