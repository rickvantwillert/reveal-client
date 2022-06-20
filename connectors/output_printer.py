
import html2text
import textwrap
import re

class OutputPrinter():

    def wrap_lines(self, string, max_width=80):
        if not max_width or max_width <= 0:
            return string

        def wrap(lines):
            for l in lines:
                length = len(l)
                if length <= max_width:
                    yield l
                else:
                    k = 0
                    while k < length:
                        snippet = l[k:k+max_width]
                        if k > 0:
                            snippet = " " + snippet
                        yield snippet
                        k += max_width
                        
        wrapped_lines = wrap(string.splitlines())
        return '\n'.join(wrapped_lines)


    def output_html2text(self, html_string):
        html_string = self.replace_tasks(html_string)
        text_maker = html2text.HTML2Text()
        text_maker.single_line_break = True
        text_maker.ignore_emphasis = True
        text_maker.bypass_tables = True
        text_maker.use_automatic_links = True
        text_maker.images_to_alt = True
        text_maker.default_image_alt = "image"
        text_maker.emphasis_mark = ""
        text_maker.strong_mark = ""
        clean_string = text_maker.handle(html_string)
        clean_string = clean_string.replace("* * *\n", "")
        clean_string = clean_string.replace("###", "")
        clean_string = clean_string.replace("##", "")
        clean_string = self.format_tables(clean_string)
        clean_string = self.wrap_lines(clean_string)
        return clean_string

    def output_options(self, options, max_width=80):
                
        def optionize(options_list):
            for i,option in enumerate(options_list):
                option_item = f'{i+1}. {option}'
                length = len(option_item)
                if length > max_width:
                    yield textwrap.shorten(option_item, width=max_width-3, placeholder="...")
                else:
                    yield option_item

        options = optionize(options)
        return options

    def format_tables(self, html):
        tables = re.findall(r'<table.*?>(?s:.*?)<\/table>', html)
        for table in tables:
        #     new_part = part
            new_table = table.replace("\n", "")
            new_table = new_table.replace("|", "-")
            new_table = re.sub(r'<\/tr>(?s:.*?)<tr.*?>', "\n", new_table)
            new_table = re.sub(r'<\/tr>', "", new_table)
            new_table = re.sub(r'<tr.*?>', "", new_table)
            new_table = re.sub(r'<\/th>(?s:.*?)<th.*?>', " || ", new_table)
            new_table = re.sub(r'<\/td> *?<td.*?>', " | ", new_table)
            new_table = re.sub(r'<\/td>(?s:.*?)<td.*?>', "\n", new_table)
            new_table = re.sub(r'<.*?>', "", new_table)
            rows = new_table.split("\n")
            new_rows = []
            for row in rows:
                row = row.strip()
                if " || " in row:
                    row = f'|| {row} ||'
                    # row = row + "\n" + "-" * len(row) # add seperator rule
                else:
                    row = f'| {row} |'
                new_rows.append(row)
            new_table = "\n" + "\n".join(new_rows) + "\n"
            html = html.replace(table, new_table)
        return html

    def replace_tasks(self, html):
        lists = re.findall(r'<ac:task-list>(?s:.*?)</ac:task-list>', html)
        for list in lists:
            new_list = list.replace("\n", "")
            html = html.replace(list, new_list)
        html = html.replace("<ac:task-status>complete</ac:task-status>", "Completed-task: ")
        html = html.replace("<ac:task-status>incomplete</ac:task-status>", "Incompleted-task: ")
        html = html.replace('<ac:task-list>', "<ul>")
        html = html.replace('</ac:task-list>', "</ul>\n")
        html = re.sub(r'<ac:task-id>(?s:.*?)<\/ac:task-id>', "", html)
        html = html.replace('<ac:task>', "<li>")
        html = html.replace('</ac:task>', "</li>\n")
        return html