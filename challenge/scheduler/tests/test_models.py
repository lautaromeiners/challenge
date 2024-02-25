from django.test import TestCase
from scheduler.models import Task, Scheduler
from django.db.utils import IntegrityError


class TaskModelTest(TestCase):

    def test_create_task(self):
        """Test creating a Task object with valid data."""
        task = Task.objects.create(
            name="Test Task",
            resources=["camera", "disk", "proc"],
            profit=10.0,
            status=Task.Status.NOT_SCHEDULED_YET,
        )
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.resources, ["camera", "disk", "proc"])
        self.assertEqual(task.profit, 10.0)
        self.assertEqual(task.status, Task.Status.NOT_SCHEDULED_YET)

    def test_create_task_with_invalid_profit(self):
        """Test creating a Task object with negative profit."""
        with self.assertRaises(IntegrityError):
            Task.objects.create(
                name="Test Task",
                resources=[],
                profit=-10.0,
                status=Task.Status.NOT_SCHEDULED_YET,
            )

    def test_task_ordering(self):
        """Test that tasks are ordered by profit in descending order."""
        task1 = Task.objects.create(
            name="Task1",
            profit=20.0,
            status=Task.Status.NOT_SCHEDULED_YET,
            resources=[],
        )
        task2 = Task.objects.create(
            name="Task2",
            profit=10.0,
            status=Task.Status.NOT_SCHEDULED_YET,
            resources=[],
        )
        tasks = Task.objects.all()
        self.assertEqual(list(tasks), [task1, task2])

    def test_task_string_representation(self):
        """Test the string representation of a Task object."""
        task = Task.objects.create(
            name="capture for client 1098",
            profit=10.0,
            status=Task.Status.NOT_SCHEDULED_YET,
            resources=[],
        )
        self.assertEqual(str(task), "capture for client 1098")


class SchedulerTest(TestCase):

    def test_single_task_scheduling(self):
        """Test scheduling a single task"""
        task = Task.objects.create(
            name="Test Task",
            resources=["camera", "disk", "proc"],
            profit=10.0,
        )

        scheduled_task = Scheduler.schedule()

        self.assertEqual(len(scheduled_task), 1)
        self.assertEqual(scheduled_task[0], task)
        self.assertEqual(Task.objects.unscheduled_tasks().count(), 0)

    def test_multiple_task_scheduling_no_resource_conflict(self):
        """Test scheduling multiple tasks with no resouce conflict"""
        camera_task = Task.objects.create(
            name="Camera",
            resources=["camera"],
            profit=10.0,
        )

        proc_task = Task.objects.create(
            name="Proc",
            resources=["proc"],
            profit=5.0,
        )

        disk_task = Task.objects.create(
            name="Disk",
            resources=["disk"],
            profit=2.5,
        )

        scheduled_tasks = Scheduler.schedule()

        self.assertEqual(len(scheduled_tasks), 3)
        self.assertEqual(scheduled_tasks[0], camera_task)
        self.assertEqual(scheduled_tasks[1], proc_task)
        self.assertEqual(scheduled_tasks[2], disk_task)
        self.assertEqual(Task.objects.unscheduled_tasks().count(), 0)

    def test_multiple_task_scheduling_with_resource_conflict(self):
        """Test scheduling multiple tasks with resource conflict and re-scheduling buffered tasks"""
        camera_task = Task.objects.create(
            name="Camera",
            resources=["camera"],
            profit=10.0,
        )

        proc_task = Task.objects.create(
            name="Proc",
            resources=["proc"],
            profit=5.0,
        )

        disk_task = Task.objects.create(
            name="Disk",
            resources=["disk"],
            profit=2.5,
        )

        client_task = Task.objects.create(
            name="capture for client 1098",
            profit=13.0,
            resources=["camera", "disk", "proc"],
        )

        scheduled_tasks = Scheduler.schedule()

        self.assertEqual(len(scheduled_tasks), 1)
        self.assertEqual(scheduled_tasks[0], client_task)
        self.assertEqual(Task.objects.unscheduled_tasks().count(), 3)

        # If I call the Scheduler again, let's say because a new
        # Task is called that requires no resources it will schedule
        # The buffered tasks
        scheduled_tasks = Scheduler.schedule()

        self.assertEqual(len(scheduled_tasks), 3)
        self.assertEqual(scheduled_tasks[0], camera_task)
        self.assertEqual(scheduled_tasks[1], proc_task)
        self.assertEqual(scheduled_tasks[2], disk_task)
        self.assertEqual(Task.objects.unscheduled_tasks().count(), 0)
