from django.db import models

class Policy(models.Model):
    client = models.ForeignKey("clients.Client", on_delete=models.CASCADE)
    company = models.CharField(max_length=100)
    policy_number = models.CharField(max_length=50)
    insurance_type = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.policy_number} - {self.client}"
