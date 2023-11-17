"""REST API for ranking service."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request

from . import rankingdb

app = FastAPI()


@app.middleware("http")
async def check_addr(request: Request, call_next):
    """Check if the request is from a whitelisted address."""
    if request.client.host not in app.state.addr_white_list:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return await call_next(request)


@app.post("/api/rankings")
async def post_rankings(msg: list[dict]) -> dict:
    """Push a list of games to the ranking service."""
    try:
        rankingdb.push_games(msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"status": "ok"}


@app.get("/api/rankings")
async def get_rankings():
    """Get the current rankings."""
    try:
        return rankingdb.get_ladder()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def serve(port, whitelist=None):
    """Serve the ranking service on the given port."""
    import uvicorn

    app.state.addr_white_list = whitelist
    uvicorn.run(app, host="0.0.0.0", port=port)
