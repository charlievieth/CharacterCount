from os.path import splitext

from .logger import get_logger
from .typing import List
from .typing import Optional
from .typing import Set  # noqa

import sublime

log = get_logger()


class Settings:
    __slots__ = "enabled", "file_extensions", "_disabled_file_names"

    def __init__(
        self,
        enabled: bool = True,
        file_extensions: Optional[List[str]] = None,
    ):
        self.enabled = enabled
        if file_extensions:
            self.file_extensions = set(
                [x if x.startswith(".") else "." + x for x in file_extensions]
            )
        else:
            self.file_extensions = set()
        self._disabled_file_names: Set[str] = set()

    def is_enabled_for_file(self, file_name: Optional[str]) -> bool:
        return bool(
            file_name and
            file_name not in self._disabled_file_names and
            splitext(file_name)[1] in self.file_extensions
        )

    def is_enabled_for_view(self, view: Optional[sublime.View]) -> bool:
        if view and not view.is_scratch():
            enabled = view.settings().get("character_count_enabled")
            if isinstance(enabled, bool):
                return enabled is True

            if self.enabled:
                return self.is_enabled_for_file(view.file_name())
            else:
                return False
        return False

    def disable_file_name(self, file_name: Optional[str]) -> None:
        if file_name:
            self._disabled_file_names.add(file_name)

    def enable_file_name(self, file_name: Optional[str]) -> None:
        if file_name:
            self._disabled_file_names.discard(file_name)

    def clear_disabled_file_names(self) -> None:
        self._disabled_file_names.clear()

    def on_update(self) -> None:
        try:
            settings = sublime.load_settings("CharacterCount.sublime-settings")
        except AttributeError:
            # This sometimes happen if we were unloaded
            log.exception("loading Sublime settings")
            return

        if settings:
            settings.clear_on_change("CharacterCount")
            settings.add_on_change("CharacterCount", self.on_update)

            self.enabled = settings.get("character_count_enabled") is True

            exts = settings.get("character_count_file_exts")
            if isinstance(exts, list):
                self.file_extensions = set(
                    [x if x.startswith(".") else "." + x for x in exts]
                )

    @classmethod
    def from_sublime_settings(cls) -> "Settings":
        settings = Settings(enabled=True, file_extensions=[".go"])
        settings.on_update()
        return settings
