import os
from copy import deepcopy
import importlib
from connectors.models import Instruction, Result, Question
import connectors.output_printer
from credentials import Credentials

class Reveal:

    EXCLUDES = ["models", "__init__", "output_printer"]

    CONTEXTS = {
        "secundary": {
            "help": Instruction(
                "Open help for current context",
                "show_help",
                local=True
            ),
            "menu": Instruction(
                "Go to main menu",
                "show_menu",
                parameter="main",
                local=True
            ),
            "back": Instruction(
                "Go to previous",
                "go_back",
                history=False,
                local=True
            )
        },
        "primary": {
            "connect": Instruction(
                "Initiate a new connection. Close current if connected.",
                "connect",
                local=True
            ),
            "exit": Instruction(
                "Exits the program",
                "close",
                local=True
            )
        }
    }

    SHORTCUTS = {
        "?": "help",
        ".": "back",
        "quit": "exit"
    }

    def __init__(self):
        self.shortcuts = {}
        self.history = []
        self.connectors = list(self.get_connectors())
        self.connector = None
        self.context = "global"
        self.subject = None
        self.printer = connectors.output_printer.OutputPrinter()
        self.clear_screen()
        self.cred = Credentials()

    def get_connectors(self):
        connectors = os.listdir("connectors/")
        for connector in connectors:
            if connector.endswith(".py"):
                connector = connector.lower().removesuffix('.py')
                if connector not in self.EXCLUDES:
                    yield connector
        
    def load_connector(self, selected):
        for connector in self.connectors:
            if connector == selected:
                try:
                    connector_module = importlib.import_module(f'connectors.{connector}')
                    self.connector = connector_module.get_connector()
                    print(self.connector)
                except Exception as e:
                    print(f'ERROR: Connector file "{connector}" is not valid!')
                    print(f'Error details: {e}')

    def connect(self, ignore=None):
        def connect_handler(options):
            selected = None
            max_options = len(list(options))
            while not selected or not selected.isdigit() or int(selected) < 1 or int(selected) > max_options:
                if selected:
                    print(f'ERROR! Please select one of the available options')
                selected = input()
            return selected

        connected = False
        while not connected:
            print("To which service would you like to connect?")
            services = self.connectors
            print("\n".join(self.printer.output_options(services)))
            selected = connect_handler(services)
            self.load_connector(self.connectors[int(selected)-1])
            self.clear_screen()
            sites = ["New connection"]
            sites += self.cred.get_credentials_list()
            print("Which connection would you like to use?")
            print("\n".join(self.printer.output_options(sites)))
            selected = connect_handler(sites)
            connected = self.initiate_connection(int(selected)-1)
            if connected:
                print("Type menu to show the main menu options")
                print("Type ? or help for the help menu")

    def new_connection(self):
        print("URL:")
        url = input()
        print("Username:")
        username = input()
        print("Password/token:")
        secret = input()
        self.clear_screen()
        self.cred.save_credentials(url, username, secret)
        return { self.cred.strip_site(url): username }

    def initiate_connection(self, option):
        self.clear_screen()
        credentials = None
        if option == 0:
            credentials = self.new_connection()
        else:
            credentials = self.cred.get_credentials()
            option = option - 1
        site = list(dict(credentials).keys())[option]
        username = dict(credentials)[site]
        secret = self.cred.get_secret(site, username)
        return self.connector.connect(f'https://{site}', username, secret)

    def close(self, ignore=None):
        os._exit(0)
        
    def clear_screen(self, ignore=None):
        os.system('cls' if os.name=='nt' else 'clear')

    def log_to_history(self, instruction_object):
        if instruction_object.history:
            self.history.append(deepcopy(instruction_object))

    def go_back(self, instruction_object, parameter=None):
        result_object = Result(self.subject)
        if len(self.history) > 1:
            self.history.pop(-1)
            instruction_object = deepcopy(self.history[-1])
            self.history.pop(-1)
            result_object = self.execute_instruction_object(instruction_object, parameter)
        else:
            print("History for this session is empty. Main menu:")
            instruction_object = self.get_instruction_object("menu")
            result_object = self.execute_instruction_object(instruction_object, parameter)
        return result_object

    def get_option_instruction(self, command, options_list):
        instruction_object = None
        if options_list and isinstance(options_list, list):
            option = int(command) - 1
            if 0 <= option < len(options_list):
                instruction_object = options_list[option]
        return instruction_object
    
    def get_available_commands(self):
        available_commands = {}
        if self.connector:
            available_commands.update(deepcopy(self.connector.CONTEXTS[self.context]))
            available_commands.update(deepcopy(self.connector.CONTEXTS["global"]))
            available_commands.update(deepcopy(self.CONTEXTS["secundary"]))
        available_commands.update(deepcopy(self.CONTEXTS["primary"]))
        return available_commands

    def dictarize(self, available_commands):
        if isinstance(available_commands, dict):
            return deepcopy(available_commands)
        elif isinstance(available_commands, list):
            dict_commands = {}
            for command,function in enumerate(available_commands):
                dict_commands[command] = function
            return dict_commands
        return None

    def get_available_shortcuts(self):
        available_shortcuts = deepcopy(self.SHORTCUTS)
        if self.connector:
            available_shortcuts.update(deepcopy(self.connector.SHORTCUTS))
        return available_shortcuts

    def get_command_instruction(self, command, available_commands, available_shortcuts, subject=None):
        instruction_object = None
        if command in available_shortcuts:
            command = available_shortcuts[command]
        if command in available_commands:
            instruction_object = available_commands[command]
        if command == "help":
            instruction_object.set_available(available_commands)
            instruction_object.set_available(available_shortcuts, False)
        if instruction_object:
            instruction_object.subject = subject
        return instruction_object

    def get_instruction_object(self, command, result_object=None):
        instruction_object = None
        if command.isdigit() and result_object: # option
            instruction_object = self.get_option_instruction(command, result_object.options_list)
        else: # command
            available_commands = self.get_available_commands()
            available_shortcuts = self.get_available_shortcuts()
            if result_object:
                instruction_object = self.get_command_instruction(command, available_commands, available_shortcuts, result_object.subject)
            else:
                instruction_object = self.get_command_instruction(command, available_commands, available_shortcuts)
        return instruction_object
    
    def execute_instruction_object(self, instruction_object, parameter):
        result_object = None
        if not instruction_object.parameter and parameter:
            instruction_object.parameter = parameter
        self.log_to_history(instruction_object)
        if instruction_object.local:
            result_object = getattr(self, instruction_object.function)(instruction_object)
        else:
            result_object = getattr(self.connector, instruction_object.function)(instruction_object)
        if result_object:
            if result_object.questions and not result_object.answers:
                instruction_object.parameter = self.form_handler(result_object.questions)
                result_object = getattr(self.connector, instruction_object.function)(instruction_object)
            self.subject = result_object.subject
            self.context = result_object.context
        return result_object

    def input_handler(self, result_object=None, function=None):
        input_value = input().split(" ")
        #### 2022-06-15
        if input_value[0].startswith("/") and len(input_value[0]) > 1:
            input_value[0] = input_value[0][1:]
            input_value.insert(0, "/")
        ####
        command = input_value[0]
        parameter = None if len(input_value) == 1 else " ".join(input_value[1:])
        self.clear_screen()
        instruction_object = self.get_instruction_object(command, result_object)
        #### 2022-06-15
        if result_object and instruction_object.context == "global" and result_object.subject:
            instruction_object.context = result_object.context
            instruction_object.subject = result_object.subject
            # instruction_object.local = False
        ####
        result_object = None # reset return object
        if not instruction_object:
            instruction_object = self.get_instruction_object("help")
            print(f"ERROR: Invalid command '{command}'. "
                + "These are the available commands:")
        # instruction_object.subject = self.subject # set subject for history
        result_object = self.execute_instruction_object(instruction_object, parameter)
        if result_object:
            if result_object.error:
                print(f'ERROR! {result_object.error}')
                result_object = self.go_back(instruction_object)
            self.input_handler(result_object)
        else:
            self.input_handler()

    def get_title(self, title):
        title = title.upper()
        if self.context:
            title += f' - {self.context.capitalize()}'
            if self.subject:
                title += f' ({self.subject})'
        return title

    def show_help(self, instruction_object, parameter=None):

        def generate_help(instruction_object):
            yield self.get_title("HELP")
            for k,v in dict(instruction_object.available_commands).items():
                shortcut = ""
                parameterized = ""
                if k in instruction_object.available_shortcuts:
                    shortcut = f'{instruction_object.available_shortcuts[k]} or '
                if v.parameterized:
                    parameterized = f' <{v.parameterized}>'
                help_option = f'- {shortcut}{k}{parameterized}: {v.description}'
                yield help_option

        help = list(generate_help(instruction_object))
        print(self.printer.wrap_lines(str("\n".join(help))))
        return Result(instruction_object.subject, instruction_object.context)


    def show_menu(self, instruction_object, parameter=None):
        menu = self.connector.MENU[instruction_object.parameter]
        options_list = [*menu]
        result_object = Result(instruction_object.subject, options_list=list(menu.values()))
        print("\n".join(self.printer.output_options(options_list)))
        return result_object

    def question_handler(self, question):

        def print_question(question, error=None):
            self.clear_screen
            if error:
                print(f'ERROR: {error}')
            print(question.summary)
            if question.options_list:
                print("\n".join(self.printer.output_options(question.options_list)))
            return input()

        def validate_answer(answer, options_list):
            selected = answer.replace(" ", "").split(",")
            if not question.multi:
                selected = [answer[0]]
            for s in selected:
                if not s.isnumeric and int(s) > len(selected) or int(s) < 0:
                    return False
            return True

        answer = print_question(question)
        if question.manadatory:
            while not answer:
                answer = print_question(question, f'A value is required for "{question.summary}"')        
        if question.options_list:
            while not validate_answer(answer):
                answer = print_question(question, f'A valid option is required for "{question.summary}"')
        return answer
    
    def form_handler(self, questions):
        for question in questions:
            question.answer = self.question_handler(question)
        return questions


### TEST CODE ###

reveal = Reveal()

reveal.connect()
reveal.input_handler()
