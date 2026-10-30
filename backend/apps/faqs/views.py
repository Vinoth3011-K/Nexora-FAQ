from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import FAQ
from .serializers import FAQSerializer


class FAQViewSet(viewsets.ModelViewSet):
    serializer_class = FAQSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = FAQ.objects.all()

        if not (self.request.user and self.request.user.is_staff):
            queryset = queryset.filter(is_active=True)

        category = self.request.query_params.get('category')
        if category and category.strip().lower() != 'all':
            queryset = queryset.filter(category__iexact=category.strip())

        return queryset.order_by('-created_at')

    @action(detail=False, methods=['get'], url_path='categories')
    def categories(self, request):
        cats = FAQ.objects.filter(is_active=True).values_list('category', flat=True).distinct()
        cleaned_cats = sorted(list({c for c in cats if c}))
        response_categories = ['All'] + [c for c in cleaned_cats if c.lower() != 'all']
        return Response({
            'status': 'success',
            'categories': response_categories,
        })

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        query = request.query_params.get('q', '').strip()
        category = request.query_params.get('category', '').strip()

        if not query:
            return Response({
                'status': 'success',
                'count': 0,
                'results': [],
                'message': 'No search query provided.',
            })

        queryset = FAQ.objects.filter(is_active=True)
        if category and category.lower() != 'all':
            queryset = queryset.filter(category__iexact=category)

        query_filter = (
            Q(question__icontains=query) |
            Q(answer__icontains=query) |
            Q(keywords__icontains=query)
        )

        results = queryset.filter(query_filter).distinct()
        page = self.paginate_queryset(results)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(results, many=True)
        return Response({
            'status': 'success',
            'count': results.count(),
            'results': serializer.data,
        })
