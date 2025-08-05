from django.db import models

class WebPage(models.Model):
    url = models.URLField()
    raw_html = models.TextField(default="", blank=True)
    crawled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"content of {self.url}"