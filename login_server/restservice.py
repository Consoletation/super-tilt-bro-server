"""REST API for login service."""

from __future__ import annotations

import asyncio

from fastapi import FastAPI, HTTPException, Request

from . import logindb, udpservice

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """Start the UDP service."""
    return asyncio.create_task(udpservice.serve(listen_port=app.state.udp_port))


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


def serve(rest_port: int, udp_port: int, whitelist=None):
    """Serve the login service on the given port."""
    import uvicorn

    app.state.udp_port = udp_port
    app.state.addr_white_list = whitelist
    uvicorn.run(app, host="0.0.0.0", port=rest_port)
