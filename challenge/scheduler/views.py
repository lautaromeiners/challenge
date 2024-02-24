from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Task, Scheduler
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def create(self, request):
        """
        Override the create method to handle the scheduler logic.

        Expects POST request with JSON data containing an array of tasks in 'tasks' key.
        """
        serializer = TaskSerializer(data=request.data, many=True)

        if serializer.is_valid():
            serializer.save()
            scheduled_tasks = Scheduler.schedule()
            scheduled_tasks = TaskSerializer(scheduled_tasks, many=True).data
            return Response({"tasks": scheduled_tasks}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
