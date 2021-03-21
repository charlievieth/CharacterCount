from os.path import splitext

from .plugin.typing import Any
from .plugin.typing import Dict
from .plugin.typing import Set
from .plugin.typing import TypedDict

import sublime
import sublime_plugin

try:
    ''.isascii()
    HAS_ISASCII = True
except AttributeError:
    HAS_ISASCII = False

STATUS_KEY = '~last'

ENABLED_FILE_EXTS = frozenset([
    '.go',
])

DISABLED_FILE_NAMES = set()  # type: Set[str]


settings = {}  # type: Dict[str, Any]


def on_settings_changed():
    global settings
    current = sublime.load_settings("CharacterCount.sublime-settings")
    if current:
        current.clear_on_change("CharacterCount")
        current.add_on_change("CharacterCount", on_settings_changed)

        settings["character_count_enabled"] = current.get("character_count_enabled", False)

        exts = current.get("character_count_file_exts", [])
        settings["character_count_file_exts"] = set(
            [x if x.startswith('.') else '.' + x for x in exts]
        )


def load_settings() -> Dict[str, Any]:
    if not settings:
        on_settings_changed()
    return settings


class CharacterCountToggle(sublime_plugin.WindowCommand):
    _enabled = False

    @property
    def enabled(self):
        return self._enabled

    def run(self) -> None:
        """ Toggles linting for the current view """
        view = self.window.active_view()
        if view:
            file_name = view.file_name()
            if file_name:
                if self._enabled:
                    DISABLED_FILE_NAMES.discard(file_name)
                else:
                    DISABLED_FILE_NAMES.add(file_name)
            view.settings().add("character_count_enabled", self._enabled)

    def _is_enabled(self, view: sublime.View) -> bool:
        if view:
            if view.settings().get("character_count_enabled", False):
                return True
            file_name = view.file_name()
            if file_name in DISABLED_FILE_NAMES:
                return False

        return False

    def _is_disabled(self, view: sublime.View) -> bool:
        """ returns if the view is explicitly disabled """
        if view:
            file_name = view.file_name()
            if (
                (file_name and file_name in DISABLED_FILE_NAMES) or
                view.settings().get("character_count_enabled", False),
            ):
                return True
        return False


class CharacterCountDisable(CharacterCountToggle):
    """ Disable character count for the current buffer """

    def __init__(self):
        self._enabled = False
        super(CharacterCountDisable, self).__init__()

    def is_enabled(self) -> bool:
        return True
        # return self._is_disabled(self.window.active_view()) is False


class CharacterCountEnable(CharacterCountToggle):
    """ Enable character count for the current buffer """

    def __init__(self):
        self._enabled = True
        super(CharacterCountEnable, self).__init__()

    def is_enabled(self) -> bool:
        return self._is_disabled(self.window.active_view()) is False


class CharacterCountListener(sublime_plugin.EventListener):
    """ Reports the character offset of the cursor. """

    def on_load_async(self, view: sublime.View) -> None:

        pass

    def is_enabled(self, view: sublime.View) -> bool:
        if view is None or view.is_scratch():
            return False

        file_name = view.file_name()
        if not file_name:
            return False

        settings = load_settings()
        if settings["character_count_enabled"] is False:
            return False

        return splitext(file_name)[1] in settings["character_count_file_exts"]

    def reset_status(self, view: sublime.View) -> None:
        if view.get_status(STATUS_KEY):
            view.set_status(STATUS_KEY, '')

    def on_selection_modified_async(self, view: sublime.View) -> None:
        if view:
            enabled = view.settings().get("character_count_enabled")
            print("character_count_enabled: {}".format(enabled))
        if not self.is_enabled(view):
            self.reset_status(view)
            return

        text = ''
        try:
            sel = view.sel()
            if sel and len(sel) > 0:
                pt = sel[0].begin()
                src = view.substr(sublime.Region(0, view.size()))
                size = len(src[:pt].encode("utf-8"))
                text = 'Pos: ' + str(size)
        except Exception:
            pass
        view.set_status(STATUS_KEY, text)
