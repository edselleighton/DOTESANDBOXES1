import math
from tkinter import Canvas


def _rounded_polygon(canvas, canvas_width, canvas_height, radius, **kwargs):
    left, top = 1, 1
    right, bottom = canvas_width - 1, canvas_height - 1
    radius = min(radius, (right - left) / 2, (bottom - top) / 2)
    fill = kwargs.pop("fill", "")
    outline = kwargs.pop("outline", "")
    outline_width = kwargs.pop("width", 1)
    points = []
    corners = (
        (right - radius, top + radius, -90, 0),
        (right - radius, bottom - radius, 0, 90),
        (left + radius, bottom - radius, 90, 180),
        (left + radius, top + radius, 180, 270),
    )

    for center_x, center_y, start, end in corners:
        for step in range(13):
            angle = math.radians(start + (end - start) * step / 12)
            points.extend((
                center_x + radius * math.cos(angle),
                center_y + radius * math.sin(angle),
            ))

    fill_item = canvas.create_polygon(
        points,
        smooth=False,
        joinstyle="round",
        fill=fill,
        outline="",
        **kwargs,
    )
    border_items = (
        canvas.create_line(
            left + radius, top, right - radius, top,
            fill=outline, width=outline_width,
        ),
        canvas.create_arc(
            right - 2 * radius, top, right, top + 2 * radius,
            start=0, extent=90, style="arc",
            outline=outline, width=outline_width,
        ),
        canvas.create_line(
            right, top + radius, right, bottom - radius,
            fill=outline, width=outline_width,
        ),
        canvas.create_arc(
            right - 2 * radius, bottom - 2 * radius, right, bottom,
            start=270, extent=90, style="arc",
            outline=outline, width=outline_width,
        ),
        canvas.create_line(
            right - radius, bottom, left + radius, bottom,
            fill=outline, width=outline_width,
        ),
        canvas.create_arc(
            left, bottom - 2 * radius, left + 2 * radius, bottom,
            start=180, extent=90, style="arc",
            outline=outline, width=outline_width,
        ),
        canvas.create_line(
            left, bottom - radius, left, top + radius,
            fill=outline, width=outline_width,
        ),
        canvas.create_arc(
            left, top, left + 2 * radius, top + 2 * radius,
            start=90, extent=90, style="arc",
            outline=outline, width=outline_width,
        ),
    )
    return fill_item, border_items


def _set_border_color(canvas, border_items, color):
    for item in border_items:
        option = "fill" if canvas.type(item) == "line" else "outline"
        canvas.itemconfigure(item, **{option: color})


class RoundedPanel(Canvas):
    def __init__(self, parent, width, height, radius=24, **kwargs):
        parent_bg = kwargs.pop("bg", parent.cget("bg"))
        outline = kwargs.pop("outline", "#555555")
        fill = kwargs.pop("fill", "black")
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent_bg,
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self.shape, self.border_items = _rounded_polygon(
            self,
            width,
            height,
            radius,
            fill=fill,
            outline=outline,
            width=1,
        )


class RoundedButton(Canvas):
    def __init__(
        self,
        parent,
        text="",
        command=None,
        width=15,
        height=56,
        radius=12,
        **kwargs,
    ):
        self.command = command
        self.normal_fill = kwargs.pop("bg", "black")
        self.active_fill = kwargs.pop("activebackground", "#202020")
        self.outline = kwargs.pop("outline", "#777777")
        foreground = kwargs.pop("fg", "white")
        active_foreground = kwargs.pop("activeforeground", foreground)
        button_font = kwargs.pop("font", ("Comic Sans MS", 18))
        cursor = kwargs.pop("cursor", "hand2")
        pixel_width = width if width > 50 else max(150, width * 14)
        parent_bg = parent.cget("bg")

        super().__init__(
            parent,
            width=pixel_width,
            height=height,
            bg=parent_bg,
            highlightthickness=0,
            bd=0,
            cursor=cursor,
            takefocus=True,
            **kwargs,
        )

        self.shape, self.border_items = _rounded_polygon(
            self,
            pixel_width,
            height,
            radius,
            fill=self.normal_fill,
            outline=self.outline,
            width=1,
        )
        self.label = self.create_text(
            pixel_width / 2,
            height / 2,
            text=text,
            fill=foreground,
            activefill=active_foreground,
            font=button_font,
        )

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._invoke)
        self.bind("<Return>", self._invoke)
        self.bind("<space>", self._invoke)

    def _on_enter(self, _event):
        self.itemconfigure(self.shape, fill=self.active_fill)
        _set_border_color(self, self.border_items, "white")

    def _on_leave(self, _event):
        self.itemconfigure(self.shape, fill=self.normal_fill)
        _set_border_color(self, self.border_items, self.outline)

    def _invoke(self, _event):
        if self.command:
            self.command()
