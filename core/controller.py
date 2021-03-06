import xml.etree.cElementTree as et
from os import sep

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, \
    EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED
from apscheduler.schedulers.background import BackgroundScheduler

from core import config
from core import workflow as wf
from core.case import callbacks
from core.events import EventListener


class SchedulerStatusListener(EventListener):
    def __init__(self, shared_log=None):
        EventListener.__init__(self, "schedulerStatus", shared_log=shared_log,
                               events={EVENT_SCHEDULER_START: callbacks.add_system_entry("Scheduler start"),
                                       EVENT_SCHEDULER_SHUTDOWN: callbacks.add_system_entry("Scheduler shutdown"),
                                       EVENT_SCHEDULER_PAUSED: callbacks.add_system_entry("Scheduler paused"),
                                       EVENT_SCHEDULER_RESUMED: callbacks.add_system_entry("Scheduler resumed")})


class JobStatusListener(EventListener):
    def __init__(self, shared_log=None):
        EventListener.__init__(self, "jobStatus", shared_log,
                               events={EVENT_JOB_ADDED: callbacks.add_system_entry("Job added"),
                                       EVENT_JOB_REMOVED: callbacks.add_system_entry("Job removed")})


class JobExecutionListener(EventListener):
    def __init__(self, shared_log=None):
        EventListener.__init__(self, "jobExecution", shared_log,
                               events={'JobExecuted': callbacks.add_system_entry("Job executed"),
                                       'JobError': callbacks.add_system_entry("Job executed with error")})

    def execute_event(self, sender, event):
        if event.exception:
            self.events['JobError'].send(sender)
            self.eventlog.append({"jobError": event.retval})
        else:
            self.events['JobExecuted'].send(sender)
            self.eventlog.append({"jobExecuted": event.retval})

    def execute_event_code(self, sender, event_code):
        if event_code == 'JobExecuted':
            self.events[event_code].send(sender)
            self.eventlog.append({"jobExecuted": 'Success'})
        elif event_code == 'JobError':
            self.events[event_code].send(sender)
            self.eventlog.append({"jobError": 'Error'})
        else:
            self.eventlog.append({event_code: 'Unsupported!'})

    def callback(self, sender):
        def execution(event):
            self.execute_event(sender, event)

        return execution


class Controller(object):
    def __init__(self, name="defaultController"):
        self.name = name
        self.workflows = {}
        self.instances = {}
        self.tree = None
        self.eventlog = []
        self.schedulerStatusListener = SchedulerStatusListener(self.eventlog)
        self.jobStatusListener = JobStatusListener(self.eventlog)
        self.jobExecutionListener = JobExecutionListener(self.eventlog)
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_listener(self.schedulerStatusListener.callback(self),
                                    EVENT_SCHEDULER_START | EVENT_SCHEDULER_SHUTDOWN
                                    | EVENT_SCHEDULER_PAUSED | EVENT_SCHEDULER_RESUMED)
        self.scheduler.add_listener(self.jobStatusListener.callback(self), EVENT_JOB_ADDED | EVENT_JOB_REMOVED)
        self.scheduler.add_listener(self.jobExecutionListener.callback(self), EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.ancestry = [self.name]

    def loadWorkflowsFromFile(self, path):
        self.tree = et.ElementTree(file=path)
        for workflow in self.tree.iter(tag="workflow"):
            name = workflow.get("name")
            self.workflows[name] = wf.Workflow(name=name, workflowConfig=workflow, parent_name=self.name)
        self.addChildWorkflows()
        self.addWorkflowScheduledJobs()

    def addChildWorkflows(self):
        for workflow in self.workflows:
            children = self.workflows[workflow].options.children
            for child in children:
                if child in self.workflows:
                    children[child] = self.workflows[child]

    def addWorkflowScheduledJobs(self):
        for workflow in self.workflows:
            if (self.workflows[workflow].options.enabled
                    and self.workflows[workflow].options.scheduler["autorun"] == "true"):
                schedule_type = self.workflows[workflow].options.scheduler["type"]
                schedule = self.workflows[workflow].options.scheduler["args"]
                self.scheduler.add_job(self.workflows[workflow].execute, trigger=schedule_type, replace_existing=True,
                                       **schedule)

    def createWorkflowFromTemplate(self, name="emptyWorkflow"):
        self.loadWorkflowsFromFile(path=config.templatesPath + sep + name + ".workflow")

    def removeWorkflow(self, name=""):
        if name in self.workflows:
            del self.workflows[name]
            return True
        return False

    def updateWorkflowName(self, oldName="", newName=""):
        self.workflows[newName] = self.workflows.pop(oldName)
        self.workflows[newName].name = newName

    def executeWorkflow(self, name, start="start", data=None):
        steps, instances = self.workflows[name].execute(start=start, data=data)
        self.jobExecutionListener.execute_event_code(self, 'JobExecuted')
        return steps, instances

    # Starts active execution
    def start(self):
        self.scheduler.start()

    # Stops active execution
    def stop(self, wait=True):
        self.scheduler.shutdown(wait=wait)

    # Pauses active execution
    def pause(self):
        self.scheduler.pause()

    # Resumes active execution
    def resume(self):
        self.scheduler.resume()

    # Pauses active execution of specific job
    def pauseJob(self, job_id):
        self.scheduler.pause_job(job_id=job_id)

    # Resumes active execution of specific job
    def resumeJob(self, job_id):
        self.scheduler.resume_job(job_id=job_id)

    # Returns jobs scheduled for active execution
    def getScheduledJobs(self):
        self.scheduler.get_jobs()
