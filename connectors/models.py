from abc import ABC, abstractmethod, abstractproperty


class Result():
     def __init__(self, subject=None, context="global", options_list=[], error=None, questions=None, answers=None):
         self.subject = subject
         self.context = context
         self.options_list = options_list
         self.error = error
         self.questions = questions
         self.answers = answers


class Instruction():

    def __init__(self, description, function, context="global", history=True, subject=None, endpoint=None, parameter=None, local=False, title=None):
        self.description = description
        self.function = function
        self.context = context
        self.history = history
        self.subject = subject
        self.endpoint = endpoint
        self.parameter = parameter
        self.local = local
        self.title = title

    def set_available(self, available, commands=True):
        if commands:
            self.available_commands = available
        else:
            self.available_shortcuts = {v: k for k, v in available.items()}


class ConnectorModel(ABC):
    
    MENU = abstractproperty()
    CONTEXTS = abstractproperty()
    SHORTCUTS = abstractproperty()

    @abstractmethod
    def test_connection(self):
        pass

    @abstractmethod
    def connect(self, url, username, password):
        pass

class Question():
   def __init__(self, summary=None, options_list=[], multi=False, mandatory=False, answer=None):
       self.summary = summary
       self.options_list = options_list
       self.multi = multi
       self.manadatory = mandatory
       self.answer = answer
