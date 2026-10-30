from django.db import models
from django.core.exceptions import ValidationError

class FAQ(models.Model):
    """
    Company FAQ Model storing verified questions, answers, categories, and keywords.
    """
    question = models.TextField(help_text="The frequently asked question.")
    answer = models.TextField(help_text="Verified answer for the question.")
    category = models.CharField(
        max_length=120, 
        db_index=True, 
        help_text="Category group, e.g. 'General Information', 'Pricing & Payments'."
    )
    keywords = models.JSONField(
        default=list, 
        blank=True, 
        help_text="List of keyword tokens or phrases for matching."
    )
    is_active = models.BooleanField(
        default=True, 
        db_index=True, 
        help_text="Whether this FAQ is actively visible and searchable."
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_active', 'created_at']),
        ]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def clean(self):
        super().clean()
        if not self.question or not self.question.strip():
            raise ValidationError({'question': 'Question field cannot be empty.'})
        if not self.answer or not self.answer.strip():
            raise ValidationError({'answer': 'Answer field cannot be empty.'})
        if not self.category or not self.category.strip():
            raise ValidationError({'category': 'Category field cannot be empty.'})

    def save(self, *args, **kwargs):
        self.question = self.question.strip() if self.question else ""
        self.answer = self.answer.strip() if self.answer else ""
        self.category = self.category.strip() if self.category else "General"
        if not isinstance(self.keywords, list):
            self.keywords = [str(self.keywords)]
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.category}] {self.question[:60]}"
