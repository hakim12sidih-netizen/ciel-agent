# `ciel.interfaces.backends.cli` — CLI Terminal & Theme

## Constantes

- **`TERMINAL_DB`** (`dict`) — `{'kitty': {'family': 'kitty', 'color_depth': '24-bit', 'unicode': True, 'capabilities': ['true_color', 'unicode', 'hyper`

## Classes

### `Console`

A high level console interface.

Args:
color_system (str, optional): The color system supported by your terminal,
either ``"standard"``, ``"256"`` or ``"truecolor"``. Leave as ``"auto"`` to autodetect.
force_terminal (Optional[bool], optional): Enable/disable terminal control codes, or None to auto-detect terminal. Defaults to None.
force_jupyter (Optional[bool], optional): Enable/disable Jupyter rendering, or None to auto-detect Jupyter. Defaults to None.
force_interactive (Optional[bool], optional): Enable/disable interactive mode, or None to auto detect. Defaults to None.
soft_wrap (Optional[bool], optional): Set soft wrap default on print method. Defaults to False.
theme (Theme, optional): An optional style theme object, or ``None`` for default theme.
stderr (bool, optional): Use stderr rather than stdout if ``file`` is not specified. Defaults to False.
file (IO, optional): A file object where the console should write to. Defaults to stdout.
quiet (bool, Optional): Boolean to suppress all output. Defaults to False.
width (int, optional): The width of the terminal. Leave as default to auto-detect width.
height (int, optional): The height of the terminal. Leave as default to auto-detect height.
style (StyleType, optional): Style to apply to all output, or None for no style. Defaults to None.
no_color (Optional[bool], optional): Enabled no color mode, or None to auto detect. Defaults to None.
tab_size (int, optional): Number of spaces used to replace a tab character. Defaults to 8.
record (bool, optional): Boolean to enable recording of terminal output,
required to call :meth:`export_html`, :meth:`export_svg`, and :meth:`export_text`. Defaults to False.
markup (bool, optional): Boolean to enable :ref:`console_markup`. Defaults to True.
emoji (bool, optional): Enable emoji code. Defaults to True.
emoji_variant (str, optional): Optional emoji variant, either "text" or "emoji". Defaults to None.
highlight (bool, optional): Enable automatic highlighting. Defaults to True.
log_time (bool, optional): Boolean to enable logging of time by :meth:`log` methods. Defaults to True.
log_path (bool, optional): Boolean to enable the logging of the caller by :meth:`log`. Defaults to True.
log_time_format (Union[str, TimeFormatterCallable], optional): If ``log_time`` is enabled, either string for strftime or callable that formats the time. Defaults to "[%X] ".
highlighter (HighlighterType, optional): Default highlighter.
legacy_windows (bool, optional): Enable legacy Windows mode, or ``None`` to auto detect. Defaults to ``None``.
safe_box (bool, optional): Restrict box options that don't render on legacy Windows.
get_datetime (Callable[[], datetime], optional): Callable that gets the current time as a datetime.datetime object (used by Console.log),
or None for datetime.now.
get_time (Callable[[], time], optional): Callable that gets the current time in seconds, default uses time.monotonic.

**Méthodes :**

- **`__init__(color_system: Union = 'auto', force_terminal: Union = None, force_jupyter: Union = None, force_interactive: Union = None, soft_wrap: bool = False, theme: Union = None, stderr: bool = False, file: Union = None, quiet: bool = False, width: Union = None, height: Union = None, style: Union = None, no_color: Union = None, tab_size: int = 8, record: bool = False, markup: bool = True, emoji: bool = True, emoji_variant: Union = None, highlight: bool = True, log_time: bool = True, log_path: bool = True, log_time_format: Union = '[%X]', highlighter: Union = <rich.highlighter.ReprHighlighter object at 0x7f41f441a660>, legacy_windows: Union = None, safe_box: bool = True, get_datetime: Union = None, get_time: Union = None, _environ: Union = None)`**
- **`begin_capture()`**
  - Begin capturing console output. Call :meth:`end_capture` to exit capture mode and return output.
- **`bell()`**
  - Play a 'bell' sound (if supported by the terminal).
- **`capture()`**
  - A context manager to *capture* the result of print() or log() in a string,
- **`clear(home: bool = True)`**
  - Clear the screen.
- **`clear_live()`**
  - Clear the Live instance. Used by the Live context manager (no need to call directly).
- **`control(control: Control)`**
  - Insert non-printing control codes.
- **`end_capture()`**
  - End capture mode and return captured string.
- **`export_html(theme: Union = None, clear: bool = True, code_format: Union = None, inline_styles: bool = False)`**
  - Generate HTML from console contents (requires record=True argument in constructor).
- **`export_svg(title: str = 'Rich', theme: Union = None, clear: bool = True, code_format: str = '<svg class="rich-terminal" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">\n    <!-- Generated with Rich https://www.textualize.io -->\n    <style>\n\n    @font-face {{\n        font-family: "Fira Code";\n        src: local("FiraCode-Regular"),\n                url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff2/FiraCode-Regular.woff2") format("woff2"),\n                url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff/FiraCode-Regular.woff") format("woff");\n        font-style: normal;\n        font-weight: 400;\n    }}\n    @font-face {{\n        font-family: "Fira Code";\n        src: local("FiraCode-Bold"),\n                url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff2/FiraCode-Bold.woff2") format("woff2"),\n                url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff/FiraCode-Bold.woff") format("woff");\n        font-style: bold;\n        font-weight: 700;\n    }}\n\n    .{unique_id}-matrix {{\n        font-family: Fira Code, monospace;\n        font-size: {char_height}px;\n        line-height: {line_height}px;\n        font-variant-east-asian: full-width;\n    }}\n\n    .{unique_id}-title {{\n        font-size: 18px;\n        font-weight: bold;\n        font-family: arial;\n    }}\n\n    {styles}\n    </style>\n\n    <defs>\n    <clipPath id="{unique_id}-clip-terminal">\n      <rect x="0" y="0" width="{terminal_width}" height="{terminal_height}" />\n    </clipPath>\n    {lines}\n    </defs>\n\n    {chrome}\n    <g transform="translate({terminal_x}, {terminal_y})" clip-path="url(#{unique_id}-clip-terminal)">\n    {backgrounds}\n    <g class="{unique_id}-matrix">\n    {matrix}\n    </g>\n    </g>\n</svg>\n', font_aspect_ratio: float = 0.61, unique_id: Union = None)`**
  - Generate an SVG from the console contents (requires record=True in Console constructor).
- **`export_text(clear: bool = True, styles: bool = False)`**
  - Generate text from console contents (requires record=True argument in constructor).
- **`get_style(name: Union, default: Union = None)`**
  - Get a Style instance by its theme name or parse a definition.
- **`input(prompt: Union = '', markup: bool = True, emoji: bool = True, password: bool = False, stream: Union = None)`**
  - Displays a prompt and waits for input from the user. The prompt may contain color / style.
- **`line(count: int = 1)`**
  - Write new line(s).
- **`log(objects: Any, sep: str = ' ', end: str = '\n', style: Union = None, justify: Union = None, emoji: Union = None, markup: Union = None, highlight: Union = None, log_locals: bool = False, _stack_offset: int = 1)`**
  - Log rich content to the terminal.
- **`measure(renderable: Union, options: Union = None)`**
  - Measure a renderable. Returns a :class:`~rich.measure.Measurement` object which contains
- **`on_broken_pipe()`**
  - This function is called when a `BrokenPipeError` is raised.
- **`out(objects: Any, sep: str = ' ', end: str = '\n', style: Union = None, highlight: Union = None)`**
  - Output to the terminal. This is a low-level way of writing to the terminal which unlike
- **`pager(pager: Union = None, styles: bool = False, links: bool = False)`**
  - A context manager to display anything printed within a "pager". The pager application
- **`pop_render_hook()`**
  - Pop the last renderhook from the stack.
- **`pop_theme()`**
  - Remove theme from top of stack, restoring previous theme.
- **`print(objects: Any, sep: str = ' ', end: str = '\n', style: Union = None, justify: Union = None, overflow: Union = None, no_wrap: Union = None, emoji: Union = None, markup: Union = None, highlight: Union = None, width: Union = None, height: Union = None, crop: bool = True, soft_wrap: Union = None, new_line_start: bool = False)`**
  - Print to the console.
- **`print_exception(width: Union = 100, extra_lines: int = 3, theme: Union = None, word_wrap: bool = False, show_locals: bool = False, suppress: Iterable = (), max_frames: int = 100)`**
  - Prints a rich render of the last exception and traceback.
- **`print_json(json: Union = None, data: Any = None, indent: Union = 2, highlight: bool = True, skip_keys: bool = False, ensure_ascii: bool = False, check_circular: bool = True, allow_nan: bool = True, default: Union = None, sort_keys: bool = False)`**
  - Pretty prints JSON. Output will be valid JSON.
- **`push_render_hook(hook: RenderHook)`**
  - Add a new render hook to the stack.
- **`push_theme(theme: Theme, inherit: bool = True)`**
  - Push a new theme on to the top of the stack, replacing the styles from the previous theme.
- **`render(renderable: Union, options: Union = None)`**
  - Render an object in to an iterable of `Segment` instances.
- **`render_lines(renderable: Union, options: Union = None, style: Union = None, pad: bool = True, new_lines: bool = False)`**
  - Render objects in to a list of lines.
- **`render_str(text: str, style: Union = '', justify: Union = None, overflow: Union = None, emoji: Union = None, markup: Union = None, highlight: Union = None, highlighter: Union = None)`**
  - Convert a string to a Text instance. This is called automatically if
- **`rule(title: Union = '', characters: str = '─', style: Union = 'rule.line', align: Literal = 'center')`**
  - Draw a line with optional centered title.
- **`save_html(path: Union, theme: Union = None, clear: bool = True, code_format: str = '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="UTF-8">\n<style>\n{stylesheet}\nbody {{\n    color: {foreground};\n    background-color: {background};\n}}\n</style>\n</head>\n<body>\n    <pre style="font-family:Menlo,\'DejaVu Sans Mono\',consolas,\'Courier New\',monospace"><code style="font-family:inherit">{code}</code></pre>\n</body>\n</html>\n', inline_styles: bool = False)`**
  - Generate HTML from console contents and write to a file (requires record=True argument in constructor).
- **`save_svg(path: Union, title: str = 'Rich', theme: Union = None, clear: bool = True, code_format: str = '<svg class="rich-terminal" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">\n    <!-- Generated with Rich https://www.textualize.io -->\n    <style>\n\n    @font-face {{\n        font-family: "Fira Code";\n        src: local("FiraCode-Regular"),\n                url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff2/FiraCode-Regular.woff2") format("woff2"),\n                url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff/FiraCode-Regular.woff") format("woff");\n        font-style: normal;\n        font-weight: 400;\n    }}\n    @font-face {{\n        font-family: "Fira Code";\n        src: local("FiraCode-Bold"),\n                url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff2/FiraCode-Bold.woff2") format("woff2"),\n                url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff/FiraCode-Bold.woff") format("woff");\n        font-style: bold;\n        font-weight: 700;\n    }}\n\n    .{unique_id}-matrix {{\n        font-family: Fira Code, monospace;\n        font-size: {char_height}px;\n        line-height: {line_height}px;\n        font-variant-east-asian: full-width;\n    }}\n\n    .{unique_id}-title {{\n        font-size: 18px;\n        font-weight: bold;\n        font-family: arial;\n    }}\n\n    {styles}\n    </style>\n\n    <defs>\n    <clipPath id="{unique_id}-clip-terminal">\n      <rect x="0" y="0" width="{terminal_width}" height="{terminal_height}" />\n    </clipPath>\n    {lines}\n    </defs>\n\n    {chrome}\n    <g transform="translate({terminal_x}, {terminal_y})" clip-path="url(#{unique_id}-clip-terminal)">\n    {backgrounds}\n    <g class="{unique_id}-matrix">\n    {matrix}\n    </g>\n    </g>\n</svg>\n', font_aspect_ratio: float = 0.61, unique_id: Union = None)`**
  - Generate an SVG file from the console contents (requires record=True in Console constructor).
- **`save_text(path: Union, clear: bool = True, styles: bool = False)`**
  - Generate text from console and save to a given location (requires record=True argument in constructor).
- **`screen(hide_cursor: bool = True, style: Union = None)`**
  - Context manager to enable and disable 'alternative screen' mode.
- **`set_alt_screen(enable: bool = True)`**
  - Enables alternative screen mode.
- **`set_live(live: Live)`**
  - Set Live instance. Used by Live context manager (no need to call directly).
- **`set_window_title(title: str)`**
  - Set the title of the console terminal window.
- **`show_cursor(show: bool = True)`**
  - Show or hide the cursor.
- **`status(status: Union, spinner: str = 'dots', spinner_style: Union = 'status.spinner', speed: float = 1.0, refresh_per_second: float = 12.5)`**
  - Display a status and spinner.
- **`update_screen(renderable: Union, region: Union = None, options: Union = None)`**
  - Update the screen at a given offset.
- **`update_screen_lines(lines: List, x: int = 0, y: int = 0)`**
  - Update lines of the screen at a given offset.
- **`use_theme(theme: Theme, inherit: bool = True)`**
  - Use a different theme for the duration of the context manager.

### `Panel`

A console renderable that draws a border around its contents.

Example:
>>> console.print(Panel("Hello, World!"))

Args:
renderable (RenderableType): A console renderable object.
box (Box): A Box instance that defines the look of the border (see :ref:`appendix_box`. Defaults to box.ROUNDED.
title (Optional[TextType], optional): Optional title displayed in panel header. Defaults to None.
title_align (AlignMethod, optional): Alignment of title. Defaults to "center".
subtitle (Optional[TextType], optional): Optional subtitle displayed in panel footer. Defaults to None.
subtitle_align (AlignMethod, optional): Alignment of subtitle. Defaults to "center".
safe_box (bool, optional): Disable box characters that don't display on windows legacy terminal with *raster* fonts. Defaults to True.
expand (bool, optional): If True the panel will stretch to fill the console width, otherwise it will be sized to fit the contents. Defaults to True.
style (str, optional): The style of the panel (border and contents). Defaults to "none".
border_style (str, optional): The style of the border. Defaults to "none".
width (Optional[int], optional): Optional width of panel. Defaults to None to auto-detect.
height (Optional[int], optional): Optional height of panel. Defaults to None to auto-detect.
padding (Optional[PaddingDimensions]): Optional padding around renderable. Defaults to 0.
highlight (bool, optional): Enable automatic highlighting of panel title (if str). Defaults to False.

**Méthodes :**

- **`__init__(renderable: RenderableType, box: Box = Box(...), title: Union = None, title_align: Literal = 'center', subtitle: Union = None, subtitle_align: Literal = 'center', safe_box: Union = None, expand: bool = True, style: Union = 'none', border_style: Union = 'none', width: Union = None, height: Union = None, padding: Union = (0, 1), highlight: bool = False)`**

### `Table`

A console renderable to draw a table.

Args:
*headers (Union[Column, str]): Column headers, either as a string, or :class:`~rich.table.Column` instance.
title (Union[str, Text], optional): The title of the table rendered at the top. Defaults to None.
caption (Union[str, Text], optional): The table caption rendered below. Defaults to None.
width (int, optional): The width in characters of the table, or ``None`` to automatically fit. Defaults to None.
min_width (Optional[int], optional): The minimum width of the table, or ``None`` for no minimum. Defaults to None.
box (box.Box, optional): One of the constants in box.py used to draw the edges (see :ref:`appendix_box`), or ``None`` for no box lines. Defaults to box.HEAVY_HEAD.
safe_box (Optional[bool], optional): Disable box characters that don't display on windows legacy terminal with *raster* fonts. Defaults to True.
padding (PaddingDimensions, optional): Padding for cells (top, right, bottom, left). Defaults to (0, 1).
collapse_padding (bool, optional): Enable collapsing of padding around cells. Defaults to False.
pad_edge (bool, optional): Enable padding of edge cells. Defaults to True.
expand (bool, optional): Expand the table to fit the available space if ``True``, otherwise the table width will be auto-calculated. Defaults to False.
show_header (bool, optional): Show a header row. Defaults to True.
show_footer (bool, optional): Show a footer row. Defaults to False.
show_edge (bool, optional): Draw a box around the outside of the table. Defaults to True.
show_lines (bool, optional): Draw lines between every row. Defaults to False.
leading (int, optional): Number of blank lines between rows (precludes ``show_lines``). Defaults to 0.
style (Union[str, Style], optional): Default style for the table. Defaults to "none".
row_styles (List[Union, str], optional): Optional list of row styles, if more than one style is given then the styles will alternate. Defaults to None.
header_style (Union[str, Style], optional): Style of the header. Defaults to "table.header".
footer_style (Union[str, Style], optional): Style of the footer. Defaults to "table.footer".
border_style (Union[str, Style], optional): Style of the border. Defaults to None.
title_style (Union[str, Style], optional): Style of the title. Defaults to None.
caption_style (Union[str, Style], optional): Style of the caption. Defaults to None.
title_justify (str, optional): Justify method for title. Defaults to "center".
caption_justify (str, optional): Justify method for caption. Defaults to "center".
highlight (bool, optional): Highlight cell contents (if str). Defaults to False.

**Méthodes :**

- **`__init__(headers: Union, title: Union = None, caption: Union = None, width: Union = None, min_width: Union = None, box: Union = Box(...), safe_box: Union = None, padding: Union = (0, 1), collapse_padding: bool = False, pad_edge: bool = True, expand: bool = False, show_header: bool = True, show_footer: bool = False, show_edge: bool = True, show_lines: bool = False, leading: int = 0, style: Union = 'none', row_styles: Union = None, header_style: Union = 'table.header', footer_style: Union = 'table.footer', border_style: Union = None, title_style: Union = None, caption_style: Union = None, title_justify: JustifyMethod = 'center', caption_justify: JustifyMethod = 'center', highlight: bool = False)`**
- **`add_column(header: RenderableType = '', footer: RenderableType = '', header_style: Union = None, highlight: Union = None, footer_style: Union = None, style: Union = None, justify: JustifyMethod = 'left', vertical: VerticalAlignMethod = 'top', overflow: OverflowMethod = 'ellipsis', width: Union = None, min_width: Union = None, max_width: Union = None, ratio: Union = None, no_wrap: bool = False)`**
  - Add a column to the table.
- **`add_row(renderables: Union, style: Union = None, end_section: bool = False)`**
  - Add a row of renderables.
- **`add_section()`**
  - Add a new section (draw a line after current row).
- **`get_row_style(console: Console, index: int)`**
  - Get the current row style.

## Fonctions

### `get_all()`

### `get_available()`

### `get_detector()`

### `get_terminal_adapters()`

### `get_theme(name: str | None = None)`

### `list_themes()`

### `set_theme(name: str)`
