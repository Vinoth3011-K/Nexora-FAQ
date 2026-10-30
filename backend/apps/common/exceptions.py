import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        custom_data = {
            'status': 'error',
            'status_code': response.status_code,
            'message': 'A validation or request error occurred.',
            'errors': response.data
        }
        response.data = custom_data
        return response

    # Unhandled exceptions
    logger.error(f"Unhandled exception in API context: {exc}", exc_info=True)
    return Response(
        {
            'status': 'error',
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'message': 'An internal server error occurred. Please try again later.'
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
