from django.db import models


class WebPagePart(models.Model):
    page = models.ForeignKey("webpages.WebPage", on_delete=models.CASCADE, related_name="parts")
    part_number = models.IntegerField()
    raw_html = models.TextField()
    is_done = models.BooleanField(default=False)

    class Meta:
        unique_together = ('page', 'part_number')
    
    def __str__(self):
        return f"Part {self.part_number} of {self.page.url}"
    

