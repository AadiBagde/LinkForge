"""
Global error handling middleware for LinkForge.
Catches all exceptions and returns standardized error responses.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from datetime import datetime
import traceback
from typing import Callable, Any

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global exception handler middleware.
    Catches all exceptions and returns standardized error responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        try:
            # Store start time for logging
            request.state.start_time = datetime.utcnow()
            
            response = await call_next(request)
            return response
            
        except StarletteHTTPException as exc:
            # FastAPI HTTP exceptions
            logger.warning(
                f"HTTP exception: {exc.status_code} - {exc.detail}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": exc.status_code,
                }
            )
            return JSONResponse(
                status_code=exc.status_code,
                content=self._error_response(
                    status_code=exc.status_code,
                    message=exc.detail,
                    request_path=request.url.path,
                ),
            )
        
        except ValueError as exc:
            # Validation errors
            logger.warning(
                f"Validation error: {str(exc)}",
                extra={"path": request.url.path, "method": request.method}
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=self._error_response(
                    status_code=422,
                    message=f"Validation error: {str(exc)}",
                    request_path=request.url.path,
                ),
            )
        
        except Exception as exc:
            # Unhandled exceptions - log full traceback
            logger.error(
                f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "exception_type": type(exc).__name__,
                    "traceback": traceback.format_exc(),
                }
            )
            
            # Return generic error response (don't expose internals in production)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=self._error_response(
                    status_code=500,
                    message="Internal server error. Please try again later.",
                    request_path=request.url.path,
                ),
            )
    
    @staticmethod
    def _error_response(
        status_code: int,
        message: str,
        request_path: str,
    ) -> dict:
        """
        Generate standardized error response format.
        
        Args:
            status_code: HTTP status code
            message: Error message
            request_path: Request path for debugging
            
        Returns:
            Standardized error response dict
        """
        return {
            "error": True,
            "status_code": status_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "path": request_path,
        }


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs all HTTP requests and responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        request.state.start_time = datetime.utcnow()
        
        # Extract request info
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params) if request.query_params else {}
        
        logger.info(
            f"Request started: {method} {path}",
            extra={
                "method": method,
                "path": path,
                "query_params": query_params,
                "client": request.client.host if request.client else "unknown",
            }
        )
        
        response = await call_next(request)
        
        # Log response
        duration_ms = (datetime.utcnow() - request.state.start_time).total_seconds() * 1000
        
        logger.info(
            f"Request completed: {method} {path} - {response.status_code}",
            extra={
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client": request.client.host if request.client else "unknown",
            }
        )
        
        return response


def setup_error_handlers(app) -> None:
    """
    Register error handling middleware with FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
    
    logger.info("Error handling middleware registered")
