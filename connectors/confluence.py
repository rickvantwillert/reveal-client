import requests
import re
from atlassian import Confluence
from .models import ConnectorModel, Instruction, Result, Question
from .output_printer import OutputPrinter
from .editor import editor


def get_connector():
    return ConfluenceConnector()


class ConfluenceConnector(ConnectorModel):

    def __init__(self):
        self.printer = OutputPrinter()
        self.confluence = None
        self.name = f'Confluence (NOT CONNECTED)'
        self.url = None
        self.username = None
        self.password = None
        self.current_user = None

    def connect(self, url, username, password):
        try:
            self.url = re.findall(r'.*.atlassian.net', url)[0]
            self.username = username
            self.password = password
            self.confluence = Confluence(
                url=self.url,
                username=username,
                password=password
            )
            self.name = f'Confluence ({url})'
            self.current_user = self.confluence_get(f'{self.url}/wiki/rest/api/user/current')
            print(f'Connected to {self.name}')
            print(f'Logged in as user: {self.current_user["displayName"]} ({self.current_user["accountId"]})')
            return True
        except:
            print(f'Could not connect to {self.name}')
            return False

    EDITABLE = "editable-by-reveal"

    MENU = {
        "main": {
            "Pages visited recently": Instruction(
                "List your recently visited pages",
                "list_cql_results",
                parameter="id in recentlyViewedContent(10) and type = page",
                title="YOUR 10 MOST RECENTLY VISITED PAGES:"
            ),  
            "Pages updated recently": Instruction(
                "List the most recently updated pages",
                "list_cql_results",
                parameter='lastModified > startOfDay("-1y") and type = page order by lastModified desc',
                title="THE 25 MOST RECENTLY EDITED PAGES:"
            ),  
            "Favourite pages": Instruction(
                "List your favourited pages",
                "list_cql_results",
                parameter="favourite = currentUser() and type = page",
                title="YOUR FAVOURITED PAGES:"
            ),  
            "Spaces visited recently": Instruction(
                "List your recently visited spaces",
                "list_cql_results",
                parameter="space in recentlyViewedSpaces(10) and type = space",
                title="YOUR 10 MOST RECENTLY VISITED SPACES:"
            ),  
            "Favourite spaces": Instruction(
                "List your favourited pages",
                "list_cql_results",
                parameter="space IN favouriteSpaces() and type = space",
                title="YOUR FAVOURITED SPACES:"
            ),
            "All Spaces": Instruction(
                "List all spaces you have access to",
                "list_all_spaces"
            ),
        }
    }

    CONTEXTS = {
        "global": {
            "search": Instruction(
                "Search for pages by title and content",
                "list_search_results",
                parameterized="keywords"
            ),
            "cql": Instruction(
                "Search for pages using Confluence Query Language (CQL)",
                "list_cql_results",
                parameterized="CQL query"
            )
        },
        "space": {
            "home": Instruction(
                "Open the space's homepage",
                "show_space_home",
                "space"
            ),
            "pages": Instruction(
                "List the top level pages in the space's page tree",
                "list_space_pages",
                "space"
            ),
            "blogs": Instruction(
                "List the the space's blog pages in descending chronilogical order",
                "list_space_blogs",
                "space"
            ),
            "favourite":  Instruction(
                "Toggles favuoriting the current space",
                "toggle_relation",
                "space",
                parameter="favourite",
                history=False
            )
        },
        "page": {
            "space": Instruction(
                "Open the space menu",
                "show_space_menu",
                "space"
            ),
            "view": Instruction(
                "View the current page",
                "view_page",
                "page"
            ),
            "edit": Instruction(
                "Edit the current page",
                "edit_page",
                "page"
            ),
            "create": Instruction(
                "Create a new page as a child page of the current page",
                "create_page",
                "page"
            ),
            "comment": Instruction(
                "DISABLED! Add a comment to the current page",
                "add_page_comment",
                "page"
            ),
            "comments": Instruction(
                "List all comments for the current page",
                "list_page_comments",
                "page"
            ),
            "info":  Instruction(
                "DISABLED! List page details",
                "show_page_info",
                "page"
            ),
            "parent":  Instruction(
                "Open the parent page of the current page",
                "open_parent_page",
                "page"
            ),
            "children":  Instruction(
                "List the children pages of the current page",
                "list_children_pages",
                "page"
            ),
            "siblings":  Instruction(
                "List the sibling pages (same parent) of the current page",
                "list_sibling_pages",
                "page"
            ),
            "favourite":  Instruction(
                "Toggles favuoriting the current page",
                "toggle_relation",
                "page",
                parameter="favourite",
                history=False
            ),
            "like":  Instruction(
                "Toggles liking the current page",
                "toggle_relation",
                "page",
                parameter="like",
                history=False
            ),
            "watch":  Instruction(
                "Toggles watching the current page",
                "toggle_watch",
                "page",
                history=False
            )
        }
    }

    SHORTCUTS = {
        "/": "search",
        "e": "edit",
        "c": "create",
        "m": "comment",
        "i": "info",
        "p": "parent",
        "f": "favourite",
        "v": "view",
        "w": "watch"
    }

    ### MENU FUNCTIONS ###

    def test_connection(self):
        pass
    
    def list_search_results(self, instruction_object):
        query = instruction_object.parameter
        instruction_object.parameter = f'title~"{query}" OR text~"{query}" and type=page'
        print(f'SEARCH RESULTS FOR: {query}')
        result_object = self.list_cql_results(instruction_object, False)
        if len(result_object.options_list) == 0:
            print("No results found")
        return result_object
    
    def list_cql_results(self, instruction_object, title=True):
        result_object = Result(instruction_object.subject)
        cql = instruction_object.parameter
        try:
            results = self.confluence.cql(cql, expand="metdata")["results"]
            instruction_objects = []
            if "space" in results[0]:
                spaces = [result["space"] for result in results]
                instruction_objects = self.generate_space_options_list(spaces)
            else:
                pages = [result["content"] for result in results]
                instruction_objects = self.generate_page_list(pages)
            if title:
                if instruction_object.title:
                    print(instruction_object.title)
                else:
                    print(f'{len(pages)} RESULTS FOR CQL QUERY: {cql}')
            self.print_instruction_objects(instruction_objects)
            result_object.options_list = instruction_objects
        except:
            if title:
                print(f'NO RESULTS FOUND! ({cql})')
            else:
                print(f'!INVALID CQL QUERY: {cql}')
        return result_object
    
    def list_all_spaces(self, instruction_object):
        all_spaces = self.confluence.get_all_spaces(start=0, limit=500, expand=None)["results"]
        all_spaces_by_type = self.generate_space_list(all_spaces)
        global_spaces = all_spaces_by_type["global"]
        print("LIST OF ALL GLOBAL SPACES (you have access to)")
        self.print_instruction_objects(global_spaces)
        return Result(instruction_object.subject, options_list=global_spaces)
    
    def show_space_home(self, instruction_object):
        space_home = self.get_space_home(instruction_object.subject)
        body = space_home["body"]["view"]["value"]
        print(f'HOMEPAGE OF SPACE: {self.get_space_name(space_home["space"])}')
        print(self.printer.output_html2text(body))
        return Result(space_home["id"], "page")
    
    def list_space_pages(self, instruction_object):
        space_home = self.get_space_home(instruction_object.subject)
        space_pages = self.generate_page_list(space_home["children"]["page"]["results"])
        print(f'LEVEL 1 PAGES OF SPACE: {self.get_space_name(space_home["space"])}')
        self.print_instruction_objects(space_pages)
        return Result(instruction_object.subject, "space", space_pages)
    
    def list_space_blogs(self, instruction_object):
        instruction_object.parameter = f'space = {instruction_object.subject} and type = blogpost order by created desc'
        print(f'BLOG POSTS FOR SPACE: {instruction_object.subject}')
        result_object = self.list_cql_results(instruction_object, False)
        if len(result_object.options_list) == 0:
            print("No blog posts found")
            return self.show_space_menu(instruction_object)
        return Result(instruction_object.subject, "space", result_object)

    def show_page(self, instruction_object):
        page = self.get_page_by_id(instruction_object.subject)
        print(f'PAGE: {page["title"]}')
        body = page["body"]["editor2"]["value"]
        body = self.printer.output_html2text(body)
        body_lines = body.split("\n")
        limit = 20
        if len(body_lines) > limit:
            print(f'NOTE: Showing first {limit} lines outof {len(body_lines)}. ')
            if self.is_editable(page):
                print(f'HINT: Type E or Edit to view and/or edit the entire page')
            else:
                print(f'HINT: Type V or View to view the entire page')
            view_body = "\n".join(body_lines[0:19])
            print(view_body)
        else:
            print(body)
        return Result(page["id"], "page")
    
    def edit_page(self, instruction_object):
        page = self.get_page_by_id(instruction_object.subject)
        if not self.is_editable(page):
            print("WARNING: This page is marked as being not editable through this client")
        else:
            title = page["title"]
            body = page["body"]["editor2"]["value"]
            page_before = f'TITLE={title}\n{self.printer.output_html2text(body)}'
            page_after = editor(text=page_before)
            if page_before != page_after:
                self.process_page_update(instruction_object, page_after)
        return self.show_page(instruction_object)

    def view_page(self, instruction_object):
        page = self.get_page_by_id(instruction_object.subject)
        title = page["title"]
        body = page["body"]["editor2"]["value"]
        page_before = f'TITLE={title}\n{self.printer.output_html2text(body)}'
        page_after = editor(text=page_before)
        if page_before != page_after and self.is_editable(page):
            print("WARNING: Changes have been made to this page. Type \"save\" to keep changes made.")
            answer = input().lower()
            if answer == "save":
                self.process_page_update(instruction_object, page_after)
        return self.show_page(instruction_object)

    def process_page_update(self, instruction_object, page_after):
        new_title = page_after.splitlines()[0].replace("TITLE=", "")
        new_body = "<br />".join(page_after.splitlines()[1:])
        try:
            self.confluence.update_page(
                instruction_object.subject,
                new_title,
                new_body
            )
            print("INFO: Page updated successfully")
        except:
            print("ERROR: Failed to update page. Check permissions or page restrictions")
        

    def create_page(self, instruction_object):
        page = self.get_page_by_id(instruction_object.subject)
        page_before = "TITLE=PAGE TITLE HERE\nINSERT PAGE CONTENT BELOW THIS LINE! (DO NOT REMOVE!)\n\n"
        page_after = editor(text=page_before)
        title = page_after.splitlines()[0].replace("TITLE=", "")
        body = "<br />".join(page_after.splitlines()[2:])
        page_id = None
        if page_after != page_before:
            try:
                new_page = self.confluence.create_page(
                    page["space"]["key"],
                    title,
                    body,
                    parent_id=instruction_object.subject,
                    type='page',
                    representation='storage',
                    editor='v2'
                )
                if "id" in new_page:
                    page_id = new_page["id"]
                    instruction_object.description = title
                    instruction_object.subject = page_id
                    try:
                        self.confluence.set_page_label(page_id, self.EDITABLE)
                    except:
                        pass
            except:
                print("ERROR: Failed to create page. Check permissions or title conflicts")
                print("HINT: First create page with title only, then edit page to add content")
        return self.show_page(instruction_object)
    
    def add_page_comment(self, instruction_object):
        print("!ERROR: Page commenting is disabled!")
        # if instruction_object.parameter:
        #     for question in instruction_object.parameter:
        #         self.confluence.add_comment(instruction_object.subject, question.answer)
        # else:
        #     return Result(
        #         instruction_object.subject,
        #         "page",
        #         questions=[Question("Enter your comment:", mandatory=True)]
        #     )
        return self.show_page(instruction_object)

    
    def list_page_comments(self, instruction_object):
        query = f'{self.url}/wiki/rest/api/content/{instruction_object.subject}/child/comment?expand=body.editor2,history.contributers,history'
        response = self.confluence_get(query)
        if response["results"]:
            comments = response["results"][::-1]
            print(f'COMMENTS FOR PAGE:')
            for comment in comments:
                print(f'COMMENT BY {comment["history"]["createdBy"]["displayName"]} ON {self.get_date(comment["history"]["createdDate"])}:')
                print(self.printer.output_html2text(comment["body"]["editor2"]["value"]) + "\n")
                return Result(instruction_object.subject, "page")
        else:
            print("NOTICE: Page doesn't have comments")
            instruction_object.parameter = instruction_object.subject
            return self.show_page(instruction_object)
    
    def show_page_info(self, instruction_object):
        # TODO: implement
        print("!ERROR: Not implemented yet")
        return self.show_page(instruction_object)
    
    def open_parent_page(self, instruction_object):
        page = self.get_page_by_id(instruction_object.subject)
        if page["ancestors"]:
            parent_page = page["ancestors"][-1]
            instruction_object.subject = parent_page["id"]
        else:
            print("NOTICE: This page doesn't have a parent")
        return self.show_page(instruction_object)
    
    def list_children_pages(self, instruction_object, title=True):
        page = self.get_page_by_id(instruction_object.subject)
        if page["children"]["page"]["results"]:
            page_children = self.generate_page_list(page["children"]["page"]["results"])
            if title:
                print(f'CHILDREN PAGES OF PAGE: {page["title"]}')
            self.print_instruction_objects(page_children)
            return Result(instruction_object.subject, "page", page_children)
        else:
            return Result(instruction_object.subject, "page", error="This page doesn't have children pages.")
    
    def list_sibling_pages(self, instruction_object):
        page = self.get_page_by_id(instruction_object.subject)
        error = False
        if page["ancestors"]:
            parent_page = page["ancestors"][-1]
            print(f'SIBLING PAGES OF PAGE: {page["title"]}')
            instruction_object.subject = parent_page["id"]
            return self.list_children_pages(instruction_object, False)
        else:
            print("NOTICE: This page doesn't have sibling pages.")
        return self.show_page(instruction_object)
        
    def toggle_relation(self, instruction_object):
        target_type = "content"
        if instruction_object.context == "space":
            target_type = instruction_object.context
        query = f'{self.url}/wiki/rest/api/relation/{instruction_object.parameter}/from/user/current/to/{target_type}/{instruction_object.subject}'
        result = self.confluence_get(query)
        if "message" in result:
            result = self.confluence_put(query)
            if "target" in result:
                if target_type == "space":
                    print(f'{str(instruction_object.parameter).upper()} ADDED FOR SPACE: {self.get_space_name(result["target"])}')
                else:
                    print(f'{str(instruction_object.parameter).upper()} ADDED FOR PAGE: {result["target"]["title"]}')
        else:
            result = self.confluence_delete(query)
            if result.status_code == 204:
                print(f'{str(instruction_object.parameter).upper()} REMOVED')
        if target_type == "space":
            return self.show_space_menu(instruction_object)
        else:
            return self.show_page(instruction_object)
    
    def toggle_watch(self, instruction_object):
        query = f'{self.url}/wiki/rest/api/user/watch/content/{instruction_object.subject}'
        if self.is_watcher(instruction_object):
            result = self.confluence_delete(query)
            if result.status_code == 204:
                print(f'WATCH REMOVED')
        else:
            result = self.confluence_post(query)
            if result.status_code == 204:
                print(f'WATCH ADDED')
        return self.show_page(instruction_object)

    ### SUPPORTING FUNCTIONS ###
    
    def get_page_by_id(self, page_id):
        query = f'{self.url}/wiki/rest/api/content/{page_id}?expand=history,space,version,childTypes.page,children.page,ancestors,body.editor2,body.view,metadata.currentuser,metadata.labels&trigger=viewed'
        response = self.confluence_get(query)
        return response
        # return self.confluence.get_page_by_id(page_id, \
        #     expand="history,space,version,childTypes.page,children.page,ancestors,body.editor2,body.view,metadata.currentuser&trigger=viewed")

    def get_space(self, space_key):
        return self.confluence.get_space(space_key, expand='homepage')

    def get_space_home(self, space_key):
        space = self.get_space(space_key)
        space_home_id = space["homepage"]["id"]
        return self.get_page_by_id(space_home_id)

    def get_space_name(self, space):
        return f'{space["name"]} ({space["key"]})'

    def show_space_menu(self, instruction_object):
        if instruction_object.subject.isdigit():
            page = self.get_page_by_id(instruction_object.subject)
            if page:
                instruction_object.subject = page["space"]["key"]
        space_name = self.get_space_name(self.get_space(instruction_object.subject))
        menu = self.CONTEXTS["space"]
        options_list = [*menu]
        for k,v in menu.items():
            v.subject = instruction_object.subject
        result_object = Result(instruction_object.subject, options_list=list(menu.values()))
        print(f'SPACE MENU FOR SPACE: {space_name}')
        print("\n".join(self.printer.output_options(options_list)))
        result_object.subject = instruction_object.subject
        return result_object

    def generate_page_list(self, pages):
        instruction_objects = []
        for page in pages:
            instruction_object = Instruction(
                page["title"],
                "show_page",
                "page",
                subject=page["id"]
            )
            instruction_objects.append(instruction_object)
        return instruction_objects

    def generate_space_options_list(self, spaces):
        instruction_objects = []
        for space in spaces:
            instruction_object = Instruction(
                f'{space["name"]} ({space["key"]})',
                "show_space_menu",
                "space",
                subject=space["key"]
            )
            instruction_objects.append(instruction_object)
        return instruction_objects
    
    def is_watcher(self, instruction_object):
        query = f'{self.url}/wiki/rest/api/content/{instruction_object.subject}/notification/child-created'
        response = self.confluence_get(query)
        is_watcher = False
        if "results" in response:
            for result in response["results"]:
                if result["watcher"]["accountId"] == self.current_user["accountId"]:
                    is_watcher = True
                    break
        return is_watcher

    def generate_space_list(self, spaces, archived=False, personal=False):
        global_spaces = []
        archived_spaces = []
        personal_spaces = []
        for space in spaces:
            instruction_object = Instruction(
                self.get_space_name(space),
                "show_space_menu",
                "space",
                subject=space["key"]
            )
            if space["status"] == "current":
                if space["type"] == "global":
                    global_spaces.append(instruction_object)
                elif personal and space["type"] == "personal":
                    personal_spaces.append(instruction_object)
            elif archived:
                archived_spaces.append(instruction_object)
        result = {
            "global": global_spaces,
            "archived": archived_spaces,
            "personal": personal_spaces
        }
        return result

    def get_page_labels(self, page):
        labels = []
        if "metadata" in page:
            if "labels" in page["metadata"]:
                if "results" in page["metadata"]["labels"]:
                    for label in page["metadata"]["labels"]["results"]:
                        labels.append(label["label"])
        return labels

    def is_editable(self, page):
        return self.EDITABLE in self.get_page_labels(page)

    def get_date(self, date):
        date_time = date.split("T")
        hour_min = date_time[1].split(":")
        return f'{date_time[0]} @ {hour_min[0]}:{hour_min[1]}'

    def print_instruction_objects(self, instruction_objects):
        options = [instruction_object.description for instruction_object in instruction_objects]
        print("\n".join(self.printer.output_options(options)))

    def confluence_get(self, query):
        try:
            return requests.get(query, auth=(self.username, self.password)).json()
        except Exception as e:
            print(e)
            return None

    def confluence_delete(self, query):
        try:
            result = requests.delete(query, auth=(self.username, self.password))
            return result
        except Exception as e:
            print(e)
            return None

    def confluence_put(self, query, body=None):
        try:
            if body:
                return requests.put(query, json=body, auth=(self.username, self.password)).json()
            else:
                return requests.put(query, auth=(self.username, self.password)).json()
        except Exception as e:
            print(e)
            return None

    def confluence_post(self, query, body=None):
        try:
            headers = { "X-Atlassian-Token": "no-check" }
            if body:
                return requests.post(query, json=body, auth=(self.username, self.password))
            else:
                return requests.post(query, headers=headers, auth=(self.username, self.password))
        except Exception as e:
            print(e)
            return None

# test = ConfluenceConnector()
# test.connect("https://tmcalm.atlassian.net", "rick.van.twillert@tmc.nl", "")

# instruction_object = Instruction("","","page",subject="1869971485",parameter="1869971485")

# # test.list_space_pages(instruction_object)
# test.open_parent_page(instruction_object)
# # test.list_page_comments(instruction_object)