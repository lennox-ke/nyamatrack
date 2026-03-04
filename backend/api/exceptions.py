from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns detailed error messages
    """
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data['status_code'] = response.status_code
        response.data['error_type'] = str(type(exc).__name__)
        
        # Log the full error details
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"API Error: {exc}", exc_info=True)
        
        # Add more detail for parsing errors
        if hasattr(exc, 'detail'):
            response.data['detail'] = str(exc.detail)
    
    return response