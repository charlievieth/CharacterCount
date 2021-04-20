from .plugin.logger import get_logger
from .plugin.settings import Settings

import sublime
import sublime_plugin

try:
    # isascii() was added in 3.7 and ST4 uses 3.8
    "".isascii()
    HAS_ISASCII = True
except AttributeError:
    HAS_ISASCII = False

STATUS_KEY = "~last"

# Global logger
log = get_logger()

# Global settings
settings = Settings(enabled=True, file_extensions=[".go"])


class CharacterCountDisable(sublime_plugin.WindowCommand):
    """ Disable character count for the current buffer """

    def run(self) -> None:
        view = self.window.active_view()
        if view:
            settings.disable_file_name(view.file_name())
            view.settings().set("character_count_enabled", False)
            view.erase_status(STATUS_KEY)

    def is_enabled(self) -> bool:
        return settings.is_enabled_for_view(self.window.active_view())


class CharacterCountEnable(sublime_plugin.WindowCommand):
    """ Enable character count for the current buffer """

    def run(self) -> None:
        view = self.window.active_view()
        if view:
            settings.enable_file_name(view.file_name())
            view.settings().set("character_count_enabled", True)

    def is_enabled(self) -> bool:
        return not settings.is_enabled_for_view(self.window.active_view())


class CharacterCountListener(sublime_plugin.EventListener):
    """ Reports the character offset of the cursor. """

    def on_selection_modified_async(self, view: sublime.View) -> None:
        if not settings.is_enabled_for_view(view):
            view.erase_status(STATUS_KEY)
            return

        text = ""
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
                text = "Pos: " + str(size)
        except IndexError as e:
            # This happens when the file is closed before this can run
            log.warning("index error: {}".format(e))
        except Exception as e:
            log.exception("calculating offset: {}".format(e))

        view.set_status(STATUS_KEY, text)


def plugin_loaded() -> None:
    global settings
    settings = Settings.from_sublime_settings()
    log.debug("loaded plugin")


def plugin_unloaded() -> None:
    log.debug("unloading plugin")
    settings.clear_disabled_file_names()
    for w in sublime.windows():
        for v in w.views():
            try:
                v.erase_status(STATUS_KEY)
            except Exception:
                log.exception("erasing status")
