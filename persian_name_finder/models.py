from django.db import models

class WebPage(models.Model):
    url = models.URLField(unique=True)
    raw_html = models.TextField()
    crawled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"content of {self.url}"

class WebPagePart(models.Model):
    page = models.ForeignKey(WebPage, on_delete=models.CASCADE, related_name="parts")
    part_number = models.IntegerField()
    raw_html = models.TextField()
    is_done = models.BooleanField(default=False)

    class Meta:
        unique_together = ('page', 'part_number')
    
    def __str__(self):
        return f"Part {self.part_number} of {self.page.url}"
    

class Author(models.Model):
    page = models.ForeignKey(WebPage, on_delete=models.CASCADE, related_name="authors")
    name = models.CharField(max_length=100)
    interests = models.CharField(max_length=255)
    homepage = models.URLField(null=True, blank=True)
    homepage_content = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    sent_email = models.BooleanField(default=False)

    def __str__(self):
        return self.name_text