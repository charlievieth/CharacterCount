from os.path import splitext

from .plugin.logger import load_logger
from .plugin.typing import Any
from .plugin.typing import Dict
from .plugin.typing import Optional
from .plugin.typing import Set  # noqa

import sublime
import sublime_plugin

try:
    # isascii() was added in 3.7 and ST4 uses 3.8
    ''.isascii()
    HAS_ISASCII = True
except AttributeError:
    HAS_ISASCII = False

STATUS_KEY = '~last'

DISABLED_FILE_NAMES = set()  # type: Set[str]

# Global logger
log = load_logger("CC")

# Global settings
_settings = {}  # type: Dict[str, Any]


def on_settings_changed() -> None:
    global _settings

    try:
        current = sublime.load_settings("CharacterCount.sublime-settings")
    except AttributeError:
        # This sometimes happen if we were unloaded
        log.exception('loading Sublime settings')
        return

    if current:
        current.clear_on_change("CharacterCount")
        current.add_on_change("CharacterCount", on_settings_changed)

        enabled = current.get("character_count_enabled", False)
        if isinstance(enabled, bool):
            _settings["character_count_enabled"] = enabled

        exts = current.get("character_count_file_exts", [])
        if exts and isinstance(exts, list):
            _settings["character_count_file_exts"] = set(
                [x if x.startswith('.') else '.' + x for x in exts]
            )


def load_settings() -> Dict[str, Any]:
    if not _settings:
        on_settings_changed()
    return _settings


def enabled_for_view(view: Optional[sublime.View]) -> bool:
    if view and not view.is_scratch():
        enabled = view.settings().get("character_count_enabled")
        if isinstance(enabled, bool):
            return enabled is True

        settings = load_settings()
        if settings.get("character_count_enabled") is False:
            return False

        file_name = view.file_name()
        if file_name:
            if file_name in DISABLED_FILE_NAMES:
                return False
            return splitext(file_name)[1] in settings.get(
                "character_count_file_exts", set(),
            )
    return False


class CharacterCountDisable(sublime_plugin.WindowCommand):
    """ Disable character count for the current buffer """

    def run(self) -> None:
        view = self.window.active_view()
        if view:
            file_name = view.file_name()
            if file_name:
                DISABLED_FILE_NAMES.add(file_name)
            view.settings().set("character_count_enabled", False)
            view.erase_status(STATUS_KEY)

    def is_enabled(self) -> bool:
        return enabled_for_view(self.window.active_view())


class CharacterCountEnable(sublime_plugin.WindowCommand):
    """ Enable character count for the current buffer """

    def run(self) -> None:
        view = self.window.active_view()
        if view:
            file_name = view.file_name()
            if file_name:
                DISABLED_FILE_NAMES.discard(file_name)
            view.settings().set("character_count_enabled", True)

    def is_enabled(self) -> bool:
        return not enabled_for_view(self.window.active_view())


class CharacterCountListener(sublime_plugin.EventListener):
    """ Reports the character offset of the cursor. """

    def on_selection_modified_async(self, view: sublime.View) -> None:
        if not enabled_for_view(view):
            view.erase_status(STATUS_KEY)
            return

        text = ''
        try:
            sel = view.sel()
            if sel and len(sel) == 1:
                pt = sel[0].begin()
                src = view.substr(sublime.Region(0, view.size()))
                # Try to skip encoding is the string is ASCII
                if HAS_ISASCII and src.isascii():
                    size = int(pt)
                else:
                    size = len(src[:pt].encode("utf-8"))
                text = 'Pos: ' + str(size)
        except IndexError as e:
            # This happens when the file is closed before this can run
            log.warning("index error: {}".format(e))
        except Exception as e:
            log.exception("calculating offset: {}".format(e))

        view.set_status(STATUS_KEY, text)


def plugin_unloaded() -> None:
    log.info('unloading plugin')
    DISABLED_FILE_NAMES.clear()
    for w in sublime.windows():
        for v in w.views():
            try:
                v.erase_status(STATUS_KEY)
            except Exception:
                log.exception('erasing status')
