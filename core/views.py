from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import connection
from django.core.cache import cache
from django.conf import settings

class HealthCheckView(APIView):
    """
    GET /api/health/
    Health check endpoint for monitoring and deployment checks.
    Checks database connectivity and cache connectivity.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        health_status = {
            'status': 'healthy',
            'checks': {}
        }
        overall_healthy = True
        
        # Check database connectivity
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            health_status['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            overall_healthy = False
            health_status['status'] = 'unhealthy'
            health_status['checks']['database'] = {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}'
            }
        
        # Check cache connectivity
        try:
            test_key = 'health_check_test'
            cache.set(test_key, 'test_value', 10)
            cached_value = cache.get(test_key)
            if cached_value == 'test_value':
                cache.delete(test_key)
                health_status['checks']['cache'] = {
                    'status': 'healthy',
                    'message': 'Cache connection successful'
                }
            else:
                overall_healthy = False
                health_status['status'] = 'unhealthy'
                health_status['checks']['cache'] = {
                    'status': 'unhealthy',
                    'message': 'Cache read/write test failed'
                }
        except Exception as e:
            overall_healthy = False
            health_status['status'] = 'unhealthy'
            health_status['checks']['cache'] = {
                'status': 'unhealthy',
                'message': f'Cache connection failed: {str(e)}'
            }
        
        # Add environment info (non-sensitive)
        health_status['environment'] = {
            'debug': settings.DEBUG,
            'timezone': str(settings.TIME_ZONE),
        }
        
        http_status = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(health_status, status=http_status)
