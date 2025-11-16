"""
Orchestrator Agent Server (ADK + AG-UI Protocol)

Starts the Orchestrator Agent as an AG-UI Protocol server.
"""

import json
import os
import time

import uvicorn
from fastapi import FastAPI
from starlette.types import ASGIApp, Message, Receive, Scope, Send

try:
    from ag_ui_adk import add_adk_fastapi_endpoint  # noqa: E402
except ImportError:
    print(
        "⚠️  Warning: ag_ui_adk not installed. Install with: uv pip install ag-ui-adk or make backend-install"
    )
    add_adk_fastapi_endpoint = None
    ADKAgent = None

from .agent import build_adk_orchestrator_agent  # noqa: E402
from .core.constants import DEFAULT_PORT  # noqa: E402
from .core.logger import log_agent_message, log_error, log_request, log_response  # noqa: E402


class LoggingMiddleware:
    """Middleware to log all requests and responses using ASGI protocol."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI application callable."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        request_body = b""
        request_body_complete = False

        # Extract method and path from scope for logging
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")
        headers = dict(scope.get("headers", []))

        # Wrap receive to capture request body
        async def receive_wrapper() -> Message:
            nonlocal request_body, request_body_complete
            message = await receive()
            if message["type"] == "http.request":
                if "body" in message:
                    request_body += message.get("body", b"")
                if not message.get("more_body", False):
                    request_body_complete = True
                    # Log request once body is complete
                    try:
                        body_json = (
                            json.loads(request_body.decode("utf-8")) if request_body else None
                        )
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        body_json = (
                            request_body.decode("utf-8", errors="ignore") if request_body else None
                        )

                    log_request(
                        method=method,
                        path=path,
                        headers={k.decode(): v.decode() for k, v in headers.items()}
                        if headers
                        else None,
                        body=body_json,
                    )
            return message

        # Wrap send to capture response
        response_status = None
        response_headers = {}
        response_body = b""
        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal response_status, response_headers, response_body, response_started
            if message["type"] == "http.response.start":
                response_status = message["status"]
                response_headers = {k.decode(): v.decode() for k, v in message.get("headers", [])}
                response_started = True
            elif message["type"] == "http.response.body":
                if "body" in message:
                    response_body += message.get("body", b"")
                if not message.get("more_body", False):
                    # Response complete, log it
                    response_time_ms = (time.time() - start_time) * 1000
                    try:
                        response_body_json = (
                            json.loads(response_body.decode("utf-8")) if response_body else None
                        )
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        response_body_json = (
                            response_body.decode("utf-8", errors="ignore")
                            if response_body
                            else None
                        )

                    log_response(
                        status_code=response_status or 200,
                        headers=response_headers,
                        body=response_body_json,
                        response_time_ms=response_time_ms,
                    )
            await send(message)

        # Process request
        try:
            await self.app(scope, receive_wrapper, send_wrapper)
        except Exception as e:
            path = scope.get("path", "/")
            log_error(e, context=f"Request to {path}")
            raise


def create_app() -> FastAPI:
    """Create FastAPI application with orchestrator agent."""
    if add_adk_fastapi_endpoint is None:
        raise ImportError(
            "ag_ui_adk is required. Install with: uv pip install ag-ui-adk or make backend-install"
        )

    app = FastAPI(title="DeFi Orchestrator (ADK)")

    adk_orchestrator_agent = build_adk_orchestrator_agent()
    add_adk_fastapi_endpoint(app, adk_orchestrator_agent, path="/")

    # Wrap app with logging middleware (must be done after routes are added)
    app = LoggingMiddleware(app)

    return app


app = create_app()


def main():
    """Main entry point for orchestrator server."""
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: GOOGLE_API_KEY environment variable not set!")
        print("   Set it with: export GOOGLE_API_KEY='your-key-here'")
        print("   Get a key from: https://aistudio.google.com/app/apikey")
        print()

    # Railway uses PORT env var, fallback to ORCHESTRATOR_PORT or DEFAULT_PORT
    port = int(os.getenv("PORT", os.getenv("ORCHESTRATOR_PORT", DEFAULT_PORT)))
    print(f"🚀 Starting Orchestrator Agent (ADK + AG-UI) on http://0.0.0.0:{port}")
    log_agent_message("Orchestrator Agent started - Logging enabled for all requests and responses")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
