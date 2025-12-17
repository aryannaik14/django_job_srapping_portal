from django.db import models

class JobListing(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=100)
    source = models.CharField(max_length=50)
    link = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # This explicitly tells Django this model belongs to the 'core' app
        app_label = 'core'

    def __str__(self):
        return f"{self.title} at {self.company}"