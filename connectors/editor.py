from pathlib import Path
import os, platform, subprocess, tempfile

DEFAULT_EDITOR = 'vim'
EDITORS = {'Windows': 'notepad'}

def editor(text=None, filename=None, editor=None, **kwargs):
    editor = editor or default_editor()
    is_temp = not filename
    if is_temp:
        fd, filename = tempfile.mkstemp()
        os.close(fd)

    try:
        path = Path(filename)
        if text is not None:
            path.write_text(text, encoding="utf-8")

        subprocess.run([editor, filename])
        return path.read_text(encoding="utf-8")

    finally:
        if is_temp:
            try:
                os.unlink(filename)
            except Exception as e:
                print(f'ERROR while editing file "{filename}"!')
                print(f'Error details: {e}')


def default_editor():
    return os.environ.get('VISUAL') or (
        os.environ.get('EDITOR')
        or EDITORS.get(platform.system(), DEFAULT_EDITOR)
    )