"""
Interactive Turtle Shape Designer - Version 5 (FINAL FINAL)

The idea is to let students draw a shape with clicks instead of having to
guess a long list of coordinates first. The finished drawing can then become
real Turtle code that they can open, edit, and learn from.
"""

# Math handles the small distance calculations needed by snap mode.
import math
# Tkinter keeps the project lightweight and easy to run with standard Python.
import tkinter as tk
from tkinter import colorchooser, filedialog, font, messagebox

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
WINDOW_TITLE = "Year 10 Python Turtle Shape Designer"
WINDOW_SIZE = "1100x900"
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 800

# A square canvas gives the coordinate system a predictable centre.
CANVAS_SIZE = 600
# Twelve pixels is close enough to help, without stealing distant clicks.
SNAP_DISTANCE = 12
# Three points is the smallest shape that has an inside (a triangle).
MIN_POINTS = 3
POINT_RADIUS = 3

FONT_NAME = "Segoe UI"
DEFAULT_FILL = "#3498db"
DEFAULT_OUTLINE = "#000000"
PANEL_COLOUR = "#f0f4f8"
GRID_COLOUR = "#bdc3c7"
ADD_GREEN = "#24a866"
UNDO_ORANGE = "#f0a43c"
CLEAR_RED = "#d9534f"
SAVE_BLUE = "#3188c9"
BUTTON_WHITE = "#ffffff"
BUTTON_TEXT = "#20252b"
BUTTON_PRESSED = "#dfe7ee"

# One step per line. (Version 4 had a blank line between every step, which
# made the text too tall for the panel and cut steps 1, 2 and 7 off.)
INSTRUCTIONS = (
    "1. Click on the grid to place the corners of one part of your shape.\n"
    "2. Click 'Add this shape part' when that part is complete. You need "
    "at least 3 different points that are not all in a straight line.\n"
    "3. Keep clicking to draw another part, such as an eye, wheel, or "
    "handle.\n"
    "4. Use 'Undo last point' to remove the latest click.\n"
    "5. Use 'Undo last shape' to remove the last finished part, or "
    "'Clear entire drawing' to start over.\n"
    "6. Snap mode joins clicks close to saved points or lines. Turn it off "
    "for completely free clicking.\n"
    "7. Choose colours whenever you like, then click 'Save Turtle program' "
    "to create a Python file.\n"
    "The grey cross is the centre (0, 0)."
)


class ShapeComponent:
    """Keep the points and colours for one part of the drawing."""

    def __init__(self, points, fill_color=DEFAULT_FILL,
                 outline_color=DEFAULT_OUTLINE):
        # One component is one finished part, such as a body, wheel, or eye.
        # Points are (x, y) tuples measured from the centre (0, 0).
        self.points = points
        # The colours travel with the points so undo and redraw keep them.
        self.fill_color = fill_color
        self.outline_color = outline_color


class ShapeDesignerApp:
    """The window where the drawing is made and saved as Turtle code."""

    def __init__(self, root):
        # The app receives the window and builds the project inside it.
        self.root = root
        self.root.title(WINDOW_TITLE)
        # The extra height leaves space for the in-window instructions.
        self.root.geometry(WINDOW_SIZE)
        # A minimum size stops the layout becoming cramped when resized.
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        # Unfinished clicks are kept separate from accepted shape parts.
        self.components = []
        self.current_points = []
        # New parts use these colours until the user picks new ones.
        self.current_fill = DEFAULT_FILL
        self.current_outline = DEFAULT_OUTLINE
        # Using half the canvas size puts (0, 0) in the visual centre.
        self.canvas_size = CANVAS_SIZE
        self.origin_x = CANVAS_SIZE // 2
        self.origin_y = CANVAS_SIZE // 2
        # Help and snapping are both optional modes remembered by the window.
        self.instructions_visible = False
        self.snap_enabled = True
        self.snap_distance = SNAP_DISTANCE
        # Named fonts keep headings, buttons, and text looking the same.
        self.heading_font = font.Font(family=FONT_NAME, size=15,
                                      weight="bold")
        self.button_font = font.Font(family=FONT_NAME, size=10)
        self.body_font = font.Font(family=FONT_NAME, size=10)

        # Build the controls first, then add the coordinate reference lines.
        self._build_ui()
        self._draw_grid()

    # -----------------------------------------------------------------------
    # Building the window
    # -----------------------------------------------------------------------
    def _build_ui(self):
        """Build the drawing area and the controls beside it."""
        # Left side is for making the shape; right side is for decisions.
        left_frame = tk.Frame(self.root)
        self.left_frame = left_frame
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                        padx=(20, 10), pady=10)

        right_frame = tk.Frame(self.root, width=340, bg=PANEL_COLOUR)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 30), pady=10)

        # The canvas is the main workspace where all points are placed.
        self.canvas = tk.Canvas(left_frame, width=CANVAS_SIZE,
                                height=CANVAS_SIZE, bg="white",
                                cursor="cross")
        self.canvas.pack(pady=10)
        # Only the left mouse button draws, so drawing stays predictable.
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # The status line is a quiet prompt right under the drawing.
        self.status_label = tk.Label(
            left_frame,
            text="Click the grid to draw a shape. Add it when you are "
                 "finished.",
            font=self.body_font,
        )
        self.status_label.pack()

        # The controls are listed in the same order you use them.
        self._make_heading(right_frame, "Build your shape", (5, 12))

        # The colour previews show the current settings before adding.
        self._make_button(right_frame, "Choose inside colour",
                          self._pick_fill).pack(pady=4)
        self.fill_preview = tk.Label(right_frame, text="  Inside colour  ",
                                     bg=self.current_fill, fg="white",
                                     font=self.body_font)
        self.fill_preview.pack(pady=2)

        self._make_button(right_frame, "Choose outside line",
                          self._pick_outline).pack(pady=4)
        self.outline_preview = tk.Label(right_frame, text="  Outside line  ",
                                        bg=self.current_outline, fg="white",
                                        font=self.body_font)
        self.outline_preview.pack(pady=2)

        # The main editing loop: add, undo a point, undo a part, or reset.
        self._make_button(right_frame, "Add this shape part",
                          self._finish_component, ADD_GREEN,
                          "white").pack(pady=(16, 5))
        self._make_button(right_frame, "Undo last point",
                          self._undo_last_point, UNDO_ORANGE,
                          "white").pack(pady=4)
        self._make_button(right_frame, "Undo last shape",
                          self._undo_last_component, UNDO_ORANGE,
                          "white").pack(pady=4)
        self._make_button(right_frame, "Clear entire drawing",
                          self._reset_all, CLEAR_RED, "white").pack(pady=4)
        # Snap mode sits with the drawing controls because it changes clicks.
        self.snap_button = self._make_button(right_frame, "Snap mode: ON",
                                             self._toggle_snap)
        self.snap_button.pack(pady=(8, 4))

        # Saving is split into a runnable program and a simple point list.
        self._make_heading(right_frame, "Save your work", (22, 12))
        self._make_button(right_frame, "Save Turtle program",
                          self._export_python_file, SAVE_BLUE,
                          "white").pack(pady=4)
        self._make_button(right_frame, "Save point list",
                          self._export_tuples_file).pack(pady=4)
        self.instructions_button = self._make_button(
            right_frame, "Show instructions", self._show_instructions)
        self.instructions_button.pack(pady=(15, 5))

        # The help panel is made now, so opening it later is instant.
        self.instructions_panel = tk.Frame(self.root, bg="white",
                                           relief=tk.GROOVE, borderwidth=1)
        tk.Label(self.instructions_panel, text="How to make a shape",
                 font=self.heading_font, bg="white").pack(
            anchor="w", pady=(12, 8), padx=30)
        tk.Label(self.instructions_panel, text=INSTRUCTIONS,
                 justify=tk.LEFT, anchor="w", font=self.body_font,
                 bg="white", wraplength=1000).pack(anchor="w", padx=30,
                                                   pady=(0, 12))

    def _make_heading(self, parent, text, padding):
        """Add a section heading to the control panel."""
        tk.Label(parent, text=text, font=self.heading_font,
                 bg=PANEL_COLOUR).pack(anchor="w", pady=padding)

    def _make_button(self, parent, text, command, background=BUTTON_WHITE,
                     foreground=BUTTON_TEXT):
        """Use one clean button style throughout the control panel."""
        # One helper stops small styling differences between buttons.
        return tk.Button(
            parent,
            text=text,
            command=command,
            # A fixed width stops the layout jumping when labels change.
            width=22,
            font=self.button_font,
            bg=background,
            fg=foreground,
            activebackground=BUTTON_PRESSED,
            activeforeground=BUTTON_TEXT,
            relief=tk.FLAT,
            borderwidth=0,
            padx=8,
            pady=5,
            cursor="hand2",
        )

    def _set_status(self, text):
        """Show a short message under the canvas."""
        self.status_label.config(text=text)

    def _show_instructions(self):
        """Show or hide the instructions without taking away the drawing."""
        # place() overlays the bottom area instead of moving everything.
        if self.instructions_visible:
            self.instructions_panel.place_forget()
            self.instructions_button.config(text="Show instructions")
        else:
            # No fixed height, so the panel grows to fit all of the text.
            self.instructions_panel.place(relx=0, rely=1, anchor="sw",
                                          relwidth=1, y=-10)
            self.instructions_button.config(text="Back to drawing")
        self.instructions_visible = not self.instructions_visible

    # -----------------------------------------------------------------------
    # Drawing on the grid
    # -----------------------------------------------------------------------
    def _draw_grid(self):
        """Draw the centre cross so Turtle coordinates are easier to read."""
        self.canvas.delete("grid")
        self.canvas.create_line(0, self.origin_y, CANVAS_SIZE, self.origin_y,
                                fill=GRID_COLOUR, width=2, tags="grid")
        self.canvas.create_line(self.origin_x, 0, self.origin_x, CANVAS_SIZE,
                                fill=GRID_COLOUR, width=2, tags="grid")

    def _to_screen(self, points):
        """Change Turtle coordinates (centre is 0, 0) into canvas pixels."""
        return [(x + self.origin_x, self.origin_y - y) for x, y in points]

    def _toggle_snap(self):
        """Turn point snapping on or off for the next clicks."""
        # Only future clicks change; saved coordinates are never rewritten.
        self.snap_enabled = not self.snap_enabled
        state = "ON" if self.snap_enabled else "OFF"
        self.snap_button.config(text=f"Snap mode: {state}")

    def _nearby_saved_point(self, screen_x, screen_y):
        """Return the closest saved corner or line point within snap range."""
        closest_point = None
        closest_distance = self.snap_distance

        # Every saved part is searched because a new part may join any of them.
        for component in self.components:
            screen_points = self._to_screen(component.points)

            # Corners are candidates; each edge adds its nearest point too.
            snap_candidates = list(screen_points)
            for index, start in enumerate(screen_points):
                end = screen_points[(index + 1) % len(screen_points)]
                edge_x = end[0] - start[0]
                edge_y = end[1] - start[1]
                edge_length_squared = edge_x ** 2 + edge_y ** 2
                if edge_length_squared == 0:
                    continue

                # How far along the edge (0 = start, 1 = end) is the click?
                position = ((screen_x - start[0]) * edge_x
                            + (screen_y - start[1]) * edge_y)
                position /= edge_length_squared
                # Clamp so the point stays on the edge, not past its ends.
                position = max(0, min(1, position))
                snap_candidates.append((start[0] + position * edge_x,
                                        start[1] + position * edge_y))

            # <= means a click exactly on the snap distance still snaps.
            for point_x, point_y in snap_candidates:
                distance = math.hypot(screen_x - point_x, screen_y - point_y)
                if distance <= closest_distance:
                    closest_point = (point_x, point_y)
                    closest_distance = distance

        return closest_point

    def _on_canvas_click(self, event):
        """Turn a screen click into a point relative to the grid centre."""
        click_x = event.x
        click_y = event.y
        if self.snap_enabled:
            snapped_point = self._nearby_saved_point(click_x, click_y)
            if snapped_point:
                # Rounding keeps the saved code tidy (50 instead of
                # 49.99999). Half a pixel is too small to see.
                click_x = round(snapped_point[0])
                click_y = round(snapped_point[1])

        # Tkinter measures down from the top-left; Turtle measures up from
        # the centre, so the y value is flipped.
        new_point = (click_x - self.origin_x, self.origin_y - click_y)

        # Two clicks on the same spot would make an invisible edge.
        if self.current_points and self.current_points[-1] == new_point:
            self._set_status("That point is already there. Click somewhere "
                             "else for the next corner.")
            return

        self.current_points.append(new_point)
        self._set_status(f"Point {len(self.current_points)} added. Add the "
                         "shape part when you are finished.")
        # Show the unfinished outline straight away.
        self._draw_current_points()

    def _draw_current_points(self):
        """Redraw the unfinished points and lines after a click or undo."""
        # Only temporary marks are cleared; saved parts have the shape tag.
        self.canvas.delete("temp")
        screen_points = self._to_screen(self.current_points)

        # Small dots show every unfinished point, even a single first click.
        for point_x, point_y in screen_points:
            self.canvas.create_oval(
                point_x - POINT_RADIUS, point_y - POINT_RADIUS,
                point_x + POINT_RADIUS, point_y + POINT_RADIUS,
                fill="black", tags="temp",
            )

        # Dashed lines show the path without pretending it is finished.
        for start, end in zip(screen_points, screen_points[1:]):
            self.canvas.create_line(start[0], start[1], end[0], end[1],
                                    fill="gray", dash=(2, 2), tags="temp")

    # -----------------------------------------------------------------------
    # Shape parts and colours
    # -----------------------------------------------------------------------
    def _pick_fill(self):
        """Choose the inside colour for the next part."""
        color = colorchooser.askcolor(title="Choose Fill Color")[1]
        # Pressing Cancel returns None, so the old colour is kept.
        if color:
            self.current_fill = color
            self.fill_preview.config(bg=color)

    def _pick_outline(self):
        """Choose the outline colour for the next part."""
        color = colorchooser.askcolor(title="Choose Outline Color")[1]
        if color:
            self.current_outline = color
            self.outline_preview.config(bg=color)

    @staticmethod
    def _all_in_one_line(points):
        """Return True if every point sits on one straight line."""
        # Make a line from the first point to the first different point.
        start_x, start_y = points[0]
        end_x, end_y = next(p for p in points if p != points[0])
        for point_x, point_y in points:
            # This "cross product" is 0 only when the point is on that line.
            cross = ((end_x - start_x) * (point_y - start_y)
                     - (end_y - start_y) * (point_x - start_x))
            if cross != 0:
                return False
        return True

    def _finish_component(self):
        """Turn the current clicks into one permanent part of the shape."""
        # A set removes repeats, so this counts different points only.
        if len(set(self.current_points)) < MIN_POINTS:
            messagebox.showwarning(
                "Not enough points",
                f"A shape part needs at least {MIN_POINTS} different points.")
            return

        # Points in one straight line would make an invisible, flat shape.
        if self._all_in_one_line(self.current_points):
            messagebox.showwarning(
                "Shape is flat",
                "All of these points are in one straight line, so the shape "
                "would have nothing inside it.\n\nMove one point off the "
                "line, or use 'Undo last point'.")
            return

        # Copy the list because the user is about to start a new part.
        component = ShapeComponent(list(self.current_points),
                                   self.current_fill, self.current_outline)
        self.components.append(component)
        self._draw_component(component)
        self._clear_current()
        self._set_status(f"Added shape part {len(self.components)}. Click "
                         "the grid to draw another part.")

    def _draw_component(self, component):
        """Put one saved shape part on the canvas."""
        canvas_points = []
        for point in self._to_screen(component.points):
            canvas_points.extend(point)
        self.canvas.create_polygon(canvas_points, fill=component.fill_color,
                                   outline=component.outline_color, width=2,
                                   tags="shape")

    # -----------------------------------------------------------------------
    # Editing
    # -----------------------------------------------------------------------
    def _undo_last_point(self):
        """Remove only the latest unfinished click."""
        if not self.current_points:
            messagebox.showinfo("Nothing to undo",
                                "There is no unfinished point to remove.")
            return

        self.current_points.pop()
        # Redrawing also removes the line joined to the deleted point.
        self._draw_current_points()
        self._set_status(f"Point removed. This part now has "
                         f"{len(self.current_points)} points.")

    def _undo_last_component(self):
        """Remove only the most recently saved part, then redraw the rest."""
        # Any unfinished attempt is thrown away for a clean restart.
        self._clear_current()

        if not self.components:
            messagebox.showinfo("Nothing to undo",
                                "There is no finished shape to remove yet.")
            return

        self.components.pop()
        # Redrawing the saved parts makes sure the removed one disappears.
        self.canvas.delete("shape")
        for component in self.components:
            self._draw_component(component)
        self._set_status("Last shape part removed. Click the grid to keep "
                         "drawing.")

    def _clear_current(self):
        """Forget the unfinished points and remove their marks."""
        self.current_points.clear()
        self.canvas.delete("temp")

    def _reset_all(self):
        """Delete everything and start again."""
        self.components.clear()
        self.current_points.clear()
        self.canvas.delete("all")
        # The grid is drawn again so the next attempt has its reference.
        self._draw_grid()
        self._set_status("Drawing cleared. Click the grid to start again.")

    # -----------------------------------------------------------------------
    # Saving
    # -----------------------------------------------------------------------
    def _ready_to_save(self):
        """Check there is something to save, and warn about loose points."""
        if not self.components:
            messagebox.showerror(
                "Nothing to save",
                "You haven't added any shape parts yet.\n\nClick the grid, "
                "then press 'Add this shape part' first.")
            return False

        # Unfinished points are not part of the shape, so ask first.
        if self.current_points:
            return messagebox.askyesno(
                "Unfinished part",
                f"You have {len(self.current_points)} point(s) that haven't "
                "been added as a shape part, so they won't be saved.\n\n"
                "Save anyway?")
        return True

    def _write_file(self, file_path, text):
        """Write text to a file. Returns True if it worked."""
        # Both save buttons use this, so the error handling is in one place.
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(text)
        except OSError as error:
            # e.g. the folder was deleted, the USB was removed, or the file
            # is open in another program.
            messagebox.showerror(
                "Could not save",
                f"Your file could not be saved.\n\n{error}\n\nTry saving "
                "somewhere else, like your Documents folder.")
            self._set_status("Save failed. Your drawing is still here.")
            return False
        return True

    def _export_python_file(self):
        """Turn the drawing into a runnable Turtle program."""
        if not self._ready_to_save():
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".py", filetypes=[("Python Files", "*.py")])
        # An empty path means the user pressed Cancel.
        if not file_path:
            return

        # The generated file stays plain so students can read and edit it.
        code_lines = [
            '"""Turtle program for my custom shape."""',
            "import turtle",
            "",
            "# Set up screen",
            "screen = turtle.Screen()",
            f'screen.bgcolor("{PANEL_COLOUR}")',
            "",
            "# Keep all of the shape parts together",
            'custom_shape = turtle.Shape("compound")',
            "",
        ]

        # Parts are saved in the same order they were drawn.
        for number, component in enumerate(self.components, 1):
            code_lines.append(f"# Shape part {number}")
            code_lines.append(
                f"part_{number}_points = {tuple(component.points)}")
            code_lines.append(
                f"custom_shape.addcomponent(part_{number}_points, "
                f'"{component.fill_color}", "{component.outline_color}")')
            code_lines.append("")

        code_lines.extend([
            "# Register the shape so turtles can use it",
            'screen.register_shape("custom_user_shape", custom_shape)',
            "t = turtle.Turtle()",
            't.shape("custom_user_shape")',
            "t.penup()",
            "# Turtle turns custom shapes to face the way the turtle is",
            "# heading. Facing up (90) shows the shape the way you drew it.",
            "t.setheading(90)",
            "# 1 = the same size you drew it. Try 0.5 for a smaller sprite.",
            "t.shapesize(1)",
            "",
            "turtle.done()",
            "",
        ])

        if self._write_file(file_path, "\n".join(code_lines)):
            messagebox.showinfo("Saved!",
                                f"Your Turtle program was saved to:\n"
                                f"{file_path}")
            self._set_status("Turtle program saved.")

    def _export_tuples_file(self):
        """Save the points separately so they can be checked or reused."""
        if not self._ready_to_save():
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not file_path:
            return

        # Colours are included so the design is not split from its data.
        lines = []
        for number, component in enumerate(self.components, 1):
            lines.append(f"Shape part {number} ({component.fill_color}, "
                         f"{component.outline_color}):")
            lines.append(str(tuple(component.points)) + "\n")

        if self._write_file(file_path, "\n".join(lines)):
            messagebox.showinfo("Saved!",
                                f"Your point list was saved to:\n{file_path}")
            self._set_status("Point list saved.")


if __name__ == "__main__":
    # This guard stops the window opening when the file is imported for
    # testing.
    root = tk.Tk()
    app = ShapeDesignerApp(root)
    root.mainloop()

