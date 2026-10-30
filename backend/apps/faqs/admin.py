from django.contrib import admin
from .models import FAQ

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('id', 'question_preview', 'category', 'is_active', 'created_at', 'updated_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('question', 'answer', 'keywords')
    list_editable = ('is_active',)
    ordering = ('-created_at',)

    def question_preview(self, obj):
        return obj.question[:75] + "..." if len(obj.question) > 75 else obj.question
    question_preview.short_description = "Question"
