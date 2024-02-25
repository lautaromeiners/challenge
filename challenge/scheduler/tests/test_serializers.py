from django.test import TestCase
from scheduler.models import Task
from scheduler.serializers import TaskSerializer


class TaskSerializerTest(TestCase):

    def test_valid_serialization(self):
        """Test serializing a Task object with valid data."""
        task = Task.objects.create(
            name="Test Task", resources=["camera", "disk", "proc"], profit=10.0
        )
        serializer = TaskSerializer(task)
        self.assertEqual(
            serializer.data,
            {
                "name": "Test Task",
                "resources": ["camera", "disk", "proc"],
                "profit": 10.0,
            },
        )

    def test_valid_deserialization(self):
        """Test deserializing a Task object with valid data."""
        data = {"name": "Test Task", "resources": ["proc"], "profit": 10.0}
        serializer = TaskSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        task = serializer.save()
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.resources, ["proc"])
        self.assertEqual(task.profit, 10.0)

    def test_invalid_deserialization(self):
        """Test deserializing a Task object with invalid data."""
        data = {"name": "", "profit": -10.0}  # Missing name & invalid profit
        serializer = TaskSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(set(serializer.errors), set(["name", "profit"]))
