from django.db import models

class Author(models.Model):
    page = models.ForeignKey("webpages.WebPage", on_delete=models.CASCADE, related_name="authors")
    name = models.CharField(max_length=100)
    interests = models.CharField(max_length=255, null=True, blank=True)
    homepage = models.URLField(null=True, blank=True)
    homepage_content = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    sent_email = models.BooleanField(default=False)
    orcid_url = models.URLField(null=True, blank=True)
    openalex_url = models.URLField(null=True, blank=True)
    works = models.JSONField(null=True, blank=True)
    openalex_called = models.BooleanField(default=False)
    openalex_retries = models.IntegerField(default=0)

    def __str__(self):
        return self.name