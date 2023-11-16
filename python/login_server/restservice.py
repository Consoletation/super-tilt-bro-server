"""REST API for login service."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request

from . import logindb

app = FastAPI()


@app.middleware("http")
async def check_addr(request: Request, call_next):
    """Check if the request is from a whitelisted address."""
    if request.client.host not in app.state.addr_white_list:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return await call_next(request)


@app.get("/api/login/user_name/{user_id}")
async def get_user_name(user_id: int) -> str:
    """Return the user name for the given user ID."""
    try:
        user_name = logindb.get_user_name(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if user_name is None:
        raise HTTPException(status_code=404, detail="User ID not found")
    return user_name


def serve(port, whitelist=None):
    """Serve the login service on the given port."""
    import uvicorn

    app.state.addr_white_list = whitelist
    uvicorn.run(app, host="0.0.0.0", port=port)
