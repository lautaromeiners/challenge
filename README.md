# Satellite Task Selector Challenge

On this challenge, I was tasked with creating a Task Scheduler. This Task Scheduler, given a list of tasks that may have conflicting resource usage, must proritize those with higher profit and buffer the unscheduled tasks for subsequent iterations.

## Installation Instructions

After cloning the repository the first step for installation is creating a virtual environment.

```
python3 -m venv venv
```

And activate it

```
source venv/bin/activate
```

Once we've got the virtual environment activated we have to install the required dependencies. For this project I'm using pip, so the command to run is

```
pip install -r requirements.txt
```

With the dependencies installed, what's left to do is run migrations.

```
python manage.py migrate
```

With this step done we are ready to run our server.

```
python manage.py runserver
```

## Usage Instructions

With the repo installed and ready to go, now we need to be able to use the application to schedule the tasks. We expose an API where a user can send the tasks and receive back the tasks that where scheduled on that iteration.
The easiest way to use this, is with cURL. Here is a sample command that you can ran.

```
curl -X POST http://localhost:8000/api/tasks/ -H "Content-Type: application/json" -d '[{"name": "capture for client 1098", "resources": ["camera", "disk", "proc"], "profit": 9.2}, {"name": "clean satellite disk", "resources": ["disk"], "profit": 0.4}, {"name": "upgrade to v2.1", "resources": ["proc"], "profit": 2.9}]'
```
This will return the following JSON

```
{
    "tasks": [
        {
            "name": "capture for client 1098",
            "resources": [
                "camera",
                "disk",
                "proc"
            ],
            "profit": 9.2
        }
    ]
}
```
There we can see that the Task that got scheduled was 'capture for client 1098', whilst the other tasks were buffered and will be re-evaluated when the scheduler runs again (when new tasks are received).

## Architecture Considerations

- The API has no authentication/authorization, of course, this would be absolutely needed on a production solution, possibly giving registered users an API key that they should provide on each requests header using authorizationToken
- Similar to the previous point, this application has no User model. Of course, we would want to have something like that for the User to retrieve its scheduled tasks and check their tasks status.
- Although there is just two status values (NOT_SCHEDULED_YET & SCHEDULED) I decided to use a ChoicesField instead of a BooleanField (for example scheduled) to make it easier to extend for more possible statuses (that of course a production application would have such as pending, completed, failed, etc)
- Due to the fact that the provided JSON to schedule a task on the resources key has a list instead of a dictionary I was not able to create a Resource model that had a ManyToMany relationship with Task. Of course this would have been better domain modelling but I did not want to change the provided JSON structure.
- To keep it simple I decided not to use Docker. Docker/Docker-Compose would be of key importance to scale the application (see below). In the same vein, I used the default sqlite db. Of course than on production we would have used PostgreSQL (or similar). Likewise I did not include any code observability tools such as Sentry, New Relic, Grafana, etc. 

## Scaling Proposal

Here's a quick diagram of how I envision that the Task Scheduler could be scaled.

![scaling-scheduler](https://github.com/lautaromeiners/challenge/assets/66447691/91f6f004-c551-42fe-9b7f-c706f55f9099)

So, a User requests a list of tasks to be scheduled. This tasks are streamed to a message bus, where the Scheduler listens to incoming tasks and picks them up as available. Buffered tasks are saved on a per-instance cache for quick retrieval each time a new task is being processed. As I said before Docker (and Kubernetes) would be of great help here to be able to dynamically scale as demand grows/shrinks.
