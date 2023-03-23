from django.db import models


class Action(models.Model):
    unit = models.CharField(null=False, max_length=2000, blank=False)
    user = models.CharField(null=False, max_length=2000, blank=False)
    action = models.CharField(null=False, max_length=2000, blank=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created']
        db_table = 'common_action'

    def __str__(self):
        return f"common_action-{self.user}-{self.action}"
