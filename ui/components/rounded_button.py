from tkinter import Canvas


def _rounded_polygon(canvas, canvas_width, canvas_height, radius, **kwargs):
    points = (
        radius, 1,
        canvas_width - radius, 1,
        canvas_width - 1, radius,
        canvas_width - 1, canvas_height - radius,
        canvas_width - radius, canvas_height - 1,
        radius, canvas_height - 1,
        1, canvas_height - radius,
        1, radius,
    )
    return canvas.create_polygon(
        points,
        smooth=True,
        splinesteps=36,
        **kwargs,
    )


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
        _rounded_polygon(
            self,
            width,
            height,
            radius,
            fill=fill,
            outline=outline,
            width=2,
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

        self.shape = _rounded_polygon(
            self,
            pixel_width,
            height,
            radius,
            fill=self.normal_fill,
            outline=self.outline,
            width=2,
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
        self.itemconfigure(self.shape, fill=self.active_fill, outline="white")

    def _on_leave(self, _event):
        self.itemconfigure(self.shape, fill=self.normal_fill, outline=self.outline)

    def _invoke(self, _event):
        if self.command:
            self.command()
