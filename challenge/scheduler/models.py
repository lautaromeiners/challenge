from django.db import models
from django.core.validators import MinValueValidator


class TaskQuerySet(models.QuerySet):
    def unscheduled_tasks(self):
        return self.filter(status=Task.Status.NOT_SCHEDULED_YET)


class Task(models.Model):
    class Status(models.IntegerChoices):
        NOT_SCHEDULED_YET = 0, "Not Scheduled Yet"
        SCHEDULED = 1, "Scheduled"

    name = models.CharField(max_length=255)
    resources = models.JSONField(blank=True)
    profit = models.FloatField(validators=[MinValueValidator(0)])
    status = models.IntegerField(
        choices=Status.choices, default=Status.NOT_SCHEDULED_YET
    )
    objects = TaskQuerySet.as_manager()

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(profit__gte=0), name="profit_gte_0"),
        ]
        ordering = ["-profit"]

    def __str__(self):
        return self.name


class Scheduler:

    @staticmethod
    def schedule():
        """
        Schedules unscheduled tasks, ensuring tasks with conflicting resource requirements
        are not scheduled together.

        Returns:
            list: A list of all scheduled tasks.
        """
        unscheduled_tasks = Task.objects.unscheduled_tasks()
        used_resources = set()
        scheduled_tasks = []

        for task in unscheduled_tasks:
            resources = task.resources
            if not any(resource in used_resources for resource in resources):
                used_resources.update({resource for resource in resources})
                task.status = Task.Status.SCHEDULED
                task.save()
                scheduled_tasks.append(task)

        return scheduled_tasks
