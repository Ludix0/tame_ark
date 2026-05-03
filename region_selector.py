# -*- coding: utf-8 -*-
import tkinter as tk


class RegionSelector:
    """Overlay plein écran pour sélectionner une zone par cliquer-glisser."""

    def __init__(self, callback):
        self.callback = callback
        self._x0 = self._y0 = self._x1 = self._y1 = 0
        self._dragging = False
        self._rect_id = None

        self.win = tk.Tk()
        self.win.attributes("-fullscreen", True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.35)
        self.win.configure(bg="black", cursor="crosshair")
        self.win.overrideredirect(True)

        self.canvas = tk.Canvas(self.win, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_text(
            self.win.winfo_screenwidth() // 2,
            self.win.winfo_screenheight() // 2,
            text="Cliquez et glissez sur la valeur de torpeur dans ARK\n(Échap pour annuler)",
            fill="white", font=("Segoe UI", 18, "bold"), justify="center"
        )

        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",        self._on_drag)
        self.canvas.bind("<ButtonRelease-1>",  self._on_release)
        self.win.bind("<Escape>", lambda e: self._cancel())
        self.win.mainloop()

    def _on_press(self, event):
        self._x0, self._y0 = event.x_root, event.y_root
        self._dragging = True
        if self._rect_id:
            self.canvas.delete(self._rect_id)

    def _on_drag(self, event):
        if self._dragging:
            if self._rect_id:
                self.canvas.delete(self._rect_id)
            x0 = self._x0 - self.win.winfo_rootx()
            y0 = self._y0 - self.win.winfo_rooty()
            self._rect_id = self.canvas.create_rectangle(
                x0, y0, event.x, event.y,
                outline="#00d4ff", width=2, fill="#00d4ff", stipple="gray25"
            )
            self._x1, self._y1 = event.x_root, event.y_root

    def _on_release(self, event):
        self._dragging = False
        self.win.destroy()
        x = min(self._x0, self._x1)
        y = min(self._y0, self._y1)
        w = abs(self._x1 - self._x0)
        h = abs(self._y1 - self._y0)
        self.callback({"left": x, "top": y, "width": w, "height": h} if w > 5 and h > 5 else None)

    def _cancel(self):
        self.win.destroy()
        self.callback(None)
