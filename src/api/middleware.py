import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.infrastructure.log import log

class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """
    Middleware that intercepts incoming requests, measures the time it takes 
    for the API to process them, and adds an 'X-Process-Time' header to the response.
    It also logs the request method, path, and duration.
    """
    async def dispatch(self, request: Request, call_next):
        # Record start time
        start_time = time.time()
        
        # Pass request to the next middleware or the endpoint itself
        try:
            response = await call_next(request)
        except Exception as e:
            # If an unhandled exception occurs in the endpoint, log the time up to failure
            process_time = time.time() - start_time
            log.error(f"Request failed: {request.method} {request.url.path} | Time: {process_time:.4f}s | Error: {e}")
            raise e
            
        # Record end time and calculate duration
        process_time = time.time() - start_time
        
        # Log the successful request
        log.info(f"Request: {request.method} {request.url.path} | Time: {process_time:.4f}s | Status: {response.status_code}")
        
        # Add the custom header to the response
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
