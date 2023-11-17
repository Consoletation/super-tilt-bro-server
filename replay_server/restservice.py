"""REST API for replay service."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, Response

from . import replaydb

app = FastAPI()


@app.middleware("http")
async def check_addr(request: Request, call_next):
    """Check if the client is authorized to perform the request."""
    if request.client.host not in app.state.addr_white_list:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return await call_next(request)


@app.post("/api/replay/games")
async def post_games(games: list[dict]):
    """Push the given games info to the database."""
    try:
        replaydb.push_games(games)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"status": "ok"}


@app.get("/api/replay/games")
async def get_games() -> list[dict]:
    """Get the list of games."""
    try:
        return replaydb.get_games_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/replay/games/{game}")
async def get_game(game: str) -> str:
    """Get a specific game."""
    try:
        game_data = replaydb.get_fm2(game.rstrip(".fm2"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    if game_data is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return Response(content=game_data, media_type="application/x-fceux-movie")


def serve(port, whitelist=None):
    """Serve the replay service on the given port."""
    import uvicorn

    app.state.addr_white_list = whitelist
    uvicorn.run(app, host="0.0.0.0", port=port)
