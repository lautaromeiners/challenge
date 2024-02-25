from django.test import TestCase
from rest_framework.test import APIRequestFactory
from scheduler.models import Task, Scheduler
from scheduler.serializers import TaskSerializer
from scheduler.views import TaskViewSet
from rest_framework.response import Response
from rest_framework import status


class TaskViewSetTest(TestCase):

    def test_schedule_task_fail(self):
        """Test scheduling a Task with invalid data."""
        factory = APIRequestFactory()
        data = [{"name": "", "resources": ["disk"], "profit": -0.4}]
        request = factory.post("/api/tasks/", data=data, format="json")
        view = TaskViewSet.as_view({"post": "create"})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(set(response.data[0]), set(["name", "profit"]))
        self.assertEqual(Task.objects.count(), 0)

    def test_schedule_single_task_success(self):
        """Test scheduling a single Task with valid data."""
        factory = APIRequestFactory()
        data = [{"name": "clean satellite disk", "resources": ["disk"], "profit": 0.4}]
        request = factory.post("/api/tasks/", data=data, format="json")
        view = TaskViewSet.as_view({"post": "create"})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tasks"][0]["name"], "clean satellite disk")
        self.assertEqual(response.data["tasks"][0]["resources"], ["disk"])
        self.assertEqual(response.data["tasks"][0]["profit"], 0.4)
        self.assertEqual(len(response.data["tasks"]), 1)
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(Task.objects.first().status, Task.Status.SCHEDULED)

    def test_schedule_multiple_task_success(self):
        """Test scheduling a multiple Task with valid data."""
        factory = APIRequestFactory()
        data = [
            {"name": "clean satellite disk", "resources": ["disk"], "profit": 0.4},
            {
                "name": "capture for client 1098",
                "resources": ["camera", "disk", "proc"],
                "profit": 9.2,
            },
            {"name": "upgrade to v2.1", "resources": ["proc"], "profit": 2.9},
        ]
        request = factory.post("/api/tasks/", data=data, format="json")
        view = TaskViewSet.as_view({"post": "create"})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tasks"][0]["name"], "capture for client 1098")
        self.assertEqual(
            response.data["tasks"][0]["resources"], ["camera", "disk", "proc"]
        )
        self.assertEqual(response.data["tasks"][0]["profit"], 9.2)

        # Due to the fact that the tasks have conflicting resource requirements
        # just the highest price task gets scheduled
        self.assertEqual(len(response.data["tasks"]), 1)
        self.assertEqual(Task.objects.count(), 3)
        self.assertEqual(Task.objects.unscheduled_tasks().count(), 2)

        # We now schedule another task that just uses the camera
        # And because we have two previously buffered tasks that use disk and proc
        # We will have 3 scheduled tasks on this iteration
        data = [
            {"name": "clean camera lense", "resources": ["camera"], "profit": 0.2},
        ]
        request = factory.post("/api/tasks/", data=data, format="json")
        view = TaskViewSet.as_view({"post": "create"})
        response = view(request)
        self.assertEqual(len(response.data["tasks"]), 3)
        self.assertEqual(response.data["tasks"][0]["name"], "upgrade to v2.1")
        self.assertEqual(response.data["tasks"][0]["resources"], ["proc"])
        self.assertEqual(response.data["tasks"][0]["profit"], 2.9)
        self.assertEqual(response.data["tasks"][1]["name"], "clean satellite disk")
        self.assertEqual(response.data["tasks"][1]["resources"], ["disk"])
        self.assertEqual(response.data["tasks"][1]["profit"], 0.4)
        self.assertEqual(response.data["tasks"][2]["name"], "clean camera lense")
        self.assertEqual(response.data["tasks"][2]["resources"], ["camera"])
        self.assertEqual(response.data["tasks"][2]["profit"], 0.2)

        # We have 4 scheduled tasks because we already had a scheduled task from the previous iteration
        # saved on the db.
        self.assertEqual(Task.objects.count(), 4)
        self.assertEqual(Task.objects.unscheduled_tasks().count(), 0)
