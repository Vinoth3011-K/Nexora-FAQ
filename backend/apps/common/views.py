from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class HealthCheckView(APIView):
    """
    Health check endpoint returning application status and database availability.
    Does not expose sensitive credentials or stack traces.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        db_healthy = False
        db_details = "unavailable"

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                row = cursor.fetchone()
                if row and row[0] == 1:
                    db_healthy = True
                    db_details = "connected"
        except Exception:
            db_healthy = False
            db_details = "disconnected"

        is_healthy = db_healthy
        response_data = {
            "status": "healthy" if is_healthy else "degraded",
            "service": "company-faq-rag-backend",
            "database": db_details,
            "version": "1.0.0"
        }

        return Response(
            response_data,
            status=status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        )
