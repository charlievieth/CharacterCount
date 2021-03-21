# CharacterCount

CharacterCount is a simple Sublime Text 3 plugin that shows the byte
offset of the cursor in the view status (`Pos: 123`).

### Settings
```js
{
  // Set to false to disable CharacterCount globally.
  "character_count_enabled": true,

  // List of file extensions that CharacterCount is enabled
  // for by default.
  "character_count_file_exts": [".go"]
}
```

### Command Palette:

* Character Count: Enable on this file
   * Enable CharacterCount regardless of file type
* Character Count: Disable on this file
   * Disable CharacterCount for the given file/view
