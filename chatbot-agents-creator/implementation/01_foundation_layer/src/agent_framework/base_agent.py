class BaseAgent:
    def __init__(self, config):
        self.config = config

    def initialize(self):
        pass

    def execute_task(self, task):
        pass

    def report_status(self):
        pass

    def terminate(self):
        pass