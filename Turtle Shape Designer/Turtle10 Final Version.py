"""
Interactive Turtle Shape Designer

The idea is to let students draw a shape with clicks instead of having to
guess a long list of coordinates first. The finished drawing can then become
real Turtle code that they can open, edit, and learn from.
"""

# Math handles the small distance calculations needed by snap mode.
import math
# Tkinter keeps the final project lightweight and easy to run with standard Python.
import tkinter as tk
from tkinter import colorchooser, filedialog, font, messagebox


class ShapeComponent:
    """Keep the points and colours for one part of the drawing."""

    def __init__(self, points, fill_color="#3498db", outline_color="#000000"):
        # One component represents one finished part, such as a body, wheel, or eye.
        self.points = points  # List of (x, y) tuples relative to center (0,0)
        # The colours travel with the points so undo and redraw do not lose the design.
        self.fill_color = fill_color
        self.outline_color = outline_color


class ShapeDesignerApp:
    """The window where the drawing is made and saved as Turtle code."""

    def __init__(self, root):
        # The app receives the already-created window and builds the project inside it.
        self.root = root
        self.root.title("Year 10 Python Turtle Shape Designer")
        # The title tells the user exactly what this small program is for.
        self.root.geometry("1100x900")
        # The extra height leaves a real space for the in-window instructions.
        self.root.minsize(1000, 800)
        # A minimum size stops the layout becoming cramped if the window is resized.
        # The window is intentionally generous because the canvas is the main working area.

        # These two lists keep unfinished work separate from accepted shape parts.
        self.components = []
        self.current_points = []
        # New parts start with these colours, but the user can change them at any time.
        self.current_fill = "#3498db"
        self.current_outline = "#000000"
        # A fixed square gives the coordinate system a predictable centre.
        self.canvas_size = 600
        self.origin_x = self.canvas_size // 2
        self.origin_y = self.canvas_size // 2
        # Using half the canvas size puts (0, 0) in the visual centre.
        # Help and snapping are both optional modes remembered by the window.
        self.instructions_visible = False
        self.snap_enabled = True
        # Snapping starts ready to help, but the user can turn it off at any point.
        # Twelve pixels feels close enough to help, without stealing distant clicks.
        self.snap_distance = 12
        # The radius is small on purpose: snapping should assist accuracy, not control the drawing.
        # These named fonts keep headings, buttons, and explanations visually consistent.
        self.heading_font = font.Font(family="Segoe UI", size=15, weight="bold")
        self.button_font = font.Font(family="Segoe UI", size=10)
        self.body_font = font.Font(family="Segoe UI", size=10)
        # Keeping fonts as objects means every widget can share the same visual settings.

        # Build the controls first, then add the coordinate reference lines.
        self._build_ui()
        self._draw_grid()

    def _build_ui(self):
        """Build the drawing area and the controls beside it."""
        # The left side is for making the shape; the right side is for decisions and saving.
        # Padding is kept here so the controls stay comfortable at the larger window size.
        left_frame = tk.Frame(self.root)
        # Frames keep the canvas area independent from the control column.
        self.left_frame = left_frame
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 10), pady=10)
        # The left frame expands into available space while the canvas keeps its fixed square size.

        right_frame = tk.Frame(self.root, width=340, bg="#f0f4f8")
        # This width gives the longer beginner-friendly labels enough room.
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 30), pady=10)
        # The right frame stays vertical so the actions read in the same order as the workflow.

        # The canvas is the main workspace where all shape points are placed.
        self.canvas = tk.Canvas(
            left_frame, width=self.canvas_size, height=self.canvas_size, bg="white", cursor="cross"
        )
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        # Binding only the left mouse button keeps the drawing action predictable.

        # The status line is a quiet prompt rather than a second pop-up interrupting the work.
        self.status_label = tk.Label(
            left_frame, text="Click the grid to draw a shape. Add it when you are finished.", font=self.body_font
        )
        self.status_label.pack()
        # Feedback belongs directly below the place where the user is working.

        # Section headings make the control panel readable from top to bottom.
        tk.Label(right_frame, text="Build your shape", font=self.heading_font, bg="#f0f4f8").pack(anchor="w", pady=(5, 12))

        # The colour previews show the current settings before another part is added.
        self._make_button(right_frame, "Choose inside colour", self._pick_fill).pack(pady=4)
        self.fill_preview = tk.Label(right_frame, text="  Inside colour  ", bg=self.current_fill, fg="white", font=self.body_font)
        self.fill_preview.pack(pady=2)
        # This swatch makes the selected fill visible without reopening the picker.

        self._make_button(right_frame, "Choose outside line", self._pick_outline).pack(pady=4)
        self.outline_preview = tk.Label(right_frame, text="  Outside line  ", bg=self.current_outline, fg="white", font=self.body_font)
        self.outline_preview.pack(pady=2)
        # The outline swatch works the same way for the border colour.

        # These actions cover the main editing loop: add, undo a point, undo a part, or reset.
        self._make_button(right_frame, "Add this shape part", self._finish_component, "#24a866", "white").pack(pady=(16, 5))
        self._make_button(right_frame, "Undo last point", self._undo_last_point, "#f0a43c", "white").pack(pady=4)
        self._make_button(right_frame, "Undo last shape", self._undo_last_component, "#f0a43c", "white").pack(pady=4)
        self._make_button(right_frame, "Clear entire drawing", self._reset_all, "#d9534f", "white").pack(pady=4)
        self.snap_button = self._make_button(right_frame, "Snap mode: ON", self._toggle_snap)
        self.snap_button.pack(pady=(8, 4))
        # Snap mode sits beside drawing controls because it changes click behavior.

        # Saving is split into a runnable result and a simple data result for inspection.
        tk.Label(right_frame, text="Save your work", font=self.heading_font, bg="#f0f4f8").pack(anchor="w", pady=(22, 12))
        self._make_button(right_frame, "Save Turtle program", self._export_python_file, "#3188c9", "white").pack(pady=4)
        self._make_button(right_frame, "Save point list", self._export_tuples_file).pack(pady=4)
        self.instructions_button = self._make_button(right_frame, "Show instructions", self._show_instructions)
        self.instructions_button.pack(pady=(15, 5))
        # Help stays at the bottom of the controls so it is easy to find but not distracting.

        # This panel uses the reserved lower space, so showing help never moves the canvas.
        self.instructions_panel = tk.Frame(self.root, bg="white", relief=tk.GROOVE, borderwidth=1)
        # Creating the panel at startup makes opening help instant and avoids a second window.
        tk.Label(
            self.instructions_panel,
            text="How to make a shape",
            font=self.heading_font,
            bg="white",
        ).pack(anchor="w", pady=(12, 8), padx=30)
        tk.Label(
            self.instructions_panel,
            text=(
                "1. Click on the grid to place the corners of one part of your shape.\n\n"
                "2. Click 'Add this shape part' when that part is complete. You need at least 3 points.\n\n"
                "3. Keep clicking to draw another part, such as an eye, wheel, or handle.\n\n"
                "4. Use 'Undo last point' to remove the latest click.\n\n"
                "5. Use 'Undo last shape' to remove the last finished part, or 'Clear entire drawing' to start over.\n\n"
                "6. Snap mode joins clicks close to saved points or lines. Turn it off for completely free clicking.\n\n"
                "7. Choose colours whenever you like, then click 'Save Turtle program' to create a Python file.\n\n"
                "The grey cross is the centre (0, 0)."
            ),
            justify=tk.LEFT,
            anchor="w",
            font=self.body_font,
            bg="white",
        ).pack(anchor="w", padx=30, pady=(0, 12))

    def _make_button(self, parent, text, command, background="#ffffff", foreground="#20252b"):
        # One helper prevents small styling differences appearing between buttons.
        """Use one clean button style throughout the control panel."""
        return tk.Button(
            parent,
            text=text,
            command=command,
            # A stable width keeps labels from changing the layout as actions change.
            width=22,
            font=self.button_font,
            bg=background,
            fg=foreground,
            activebackground="#dfe7ee",
            activeforeground="#20252b",
            relief=tk.FLAT,
            borderwidth=0,
            padx=8,
            pady=5,
            cursor="hand2",
        )

    def _show_instructions(self):
        # place() overlays the bottom area instead of asking pack() to rearrange everything.
        """Show or hide the instructions without taking away the drawing."""
        # The same button acts as both open and close, keeping the interface compact.
        if self.instructions_visible:
            self.instructions_panel.place_forget()
            self.instructions_button.config(text="Show instructions")
        else:
            self.instructions_panel.place(relx=0, rely=1, anchor="sw", relwidth=1, height=210, x=0, y=-15)
            self.instructions_button.config(text="Back to drawing")
        self.instructions_visible = not self.instructions_visible

    def _draw_grid(self):
        """Draw the centre lines that make the Turtle coordinates easier to read."""
        # Redrawing the grid after reset removes old marks without rebuilding the widget.
        self.canvas.delete("grid")
        # The cross makes it easier to see where the Turtle origin is.
        self.canvas.create_line(0, self.origin_y, self.canvas_size, self.origin_y, fill="#bdc3c7", width=2, tags="grid")
        self.canvas.create_line(self.origin_x, 0, self.origin_x, self.canvas_size, fill="#bdc3c7", width=2, tags="grid")

    def _toggle_snap(self):
        """Turn point snapping on or off for the next clicks."""
        # Snap mode changes only future clicks; existing coordinates are never rewritten.
        self.snap_enabled = not self.snap_enabled
        state = "ON" if self.snap_enabled else "OFF"
        self.snap_button.config(text=f"Snap mode: {state}")

    def _nearby_saved_point(self, screen_x, screen_y):
        """Return the closest saved corner or line point within snap distance."""
        # Returning screen coordinates lets the click handler use one conversion path.
        closest_point = None
        closest_distance = self.snap_distance

        # Every saved part is searched because a new part may join any older part.
        for component in self.components:
            screen_points = [
                (turtle_x + self.origin_x, self.origin_y - turtle_y)
                for turtle_x, turtle_y in component.points
            ]

            # Corners are candidates themselves; edges add a projected point between corners.
            snap_candidates = list(screen_points)
            for index, start in enumerate(screen_points):
                end = screen_points[(index + 1) % len(screen_points)]
                segment_x = end[0] - start[0]
                segment_y = end[1] - start[1]
                segment_length_squared = segment_x ** 2 + segment_y ** 2
                if segment_length_squared == 0:
                    continue

                # Projection finds the nearest location along this particular edge.
                position = (
                    ((screen_x - start[0]) * segment_x + (screen_y - start[1]) * segment_y)
                    / segment_length_squared
                )
                position = max(0, min(1, position))
                snap_candidates.append(
                    (start[0] + position * segment_x, start[1] + position * segment_y)
                )

            # Keep whichever candidate is genuinely closest to the mouse click.
            for point_x, point_y in snap_candidates:
                distance = math.hypot(screen_x - point_x, screen_y - point_y)
                if distance <= closest_distance:
                    closest_point = (point_x, point_y)
                    closest_distance = distance

        return closest_point

    def _on_canvas_click(self, event):
        """Turn a screen click into a point relative to the centre of the grid."""
        # Tkinter measures down from the top-left; Turtle measures up from the centre.
        # Snapping first means the saved coordinate lands exactly on the target.
        click_x = event.x
        click_y = event.y
        snapped_point = self._nearby_saved_point(click_x, click_y) if self.snap_enabled else None
        if snapped_point:
            click_x, click_y = snapped_point

        turtle_x = click_x - self.origin_x
        turtle_y = self.origin_y - click_y

        self.current_points.append((turtle_x, turtle_y))
        self.status_label.config(text=f"Point {len(self.current_points)} added. Add the shape part when you are finished.")

        # Show the unfinished outline straight away, so clicks do not feel invisible.
        self._draw_current_points()

    def _draw_current_points(self):
        """Redraw the unfinished points and lines after a click or undo."""
        # Clear only temporary marks; completed coloured polygons have the shape tag.
        self.canvas.delete("temp")
        screen_points = [
            (turtle_x + self.origin_x, self.origin_y - turtle_y)
            for turtle_x, turtle_y in self.current_points
        ]

        # Small dots show every unfinished point, including a single first click.
        for point_x, point_y in screen_points:
            radius = 3
            self.canvas.create_oval(
                point_x - radius,
                point_y - radius,
                point_x + radius,
                point_y + radius,
                fill="black",
                tags="temp",
            )

        # Dashed lines show the current path without pretending it is finished yet.
        for start, end in zip(screen_points, screen_points[1:]):
            self.canvas.create_line(
                start[0], start[1], end[0], end[1], fill="gray", dash=(2, 2), tags="temp"
            )

    def _undo_last_point(self):
        """Remove only the latest unfinished click."""
        # This is intentionally different from undoing a whole saved shape part.
        if not self.current_points:
            messagebox.showinfo("Nothing to undo", "There is no unfinished point to remove.")
            return

        self.current_points.pop()
        # Redrawing also removes the line that used to connect to the deleted point.
        self._draw_current_points()

    def _pick_fill(self):
        # Colour selection affects the next part, not polygons that are already finished.
        color = colorchooser.askcolor(title="Choose Fill Color")[1]
        if color:
            self.current_fill = color
            self.fill_preview.config(bg=color)

    def _pick_outline(self):
        # Keeping the outline separate makes borders readable against bright fills.
        color = colorchooser.askcolor(title="Choose Outline Color")[1]
        if color:
            self.current_outline = color
            self.outline_preview.config(bg=color)

    def _finish_component(self):
        """Turn the current clicks into one permanent part of the shape."""
        # Three points is the smallest valid polygon, so this protects against bad exports.
        if len(self.current_points) < 3:
            messagebox.showwarning("Warning", "A polygon requires at least 3 points.")
            return

        # Copy the list because the user is about to start a new temporary part.
        component = ShapeComponent(list(self.current_points), self.current_fill, self.current_outline)
        self.components.append(component)

        # Draw the saved part so the person can see the complete shape grow.
        self._draw_component(component)

        # Clearing here prepares the canvas for the next part without deleting the new one.
        self._clear_current()
        self.status_label.config(text=f"Added shape part {len(self.components)}. Click the grid to draw another part.")

    def _draw_component(self, component):
        """Put one saved shape part back on the canvas."""
        # Convert from Turtle's centre-based coordinates to Tkinter pixel coordinates.
        canvas_points = []
        for x, y in component.points:
            canvas_points.extend([x + self.origin_x, self.origin_y - y])

        self.canvas.create_polygon(
            canvas_points, fill=component.fill_color, outline=component.outline_color, width=2, tags="shape"
        )

    def _undo_last_component(self):
        """Remove only the most recently saved part, then redraw what remains."""
        # Any unfinished attempt is discarded because undoing a part starts a clean attempt.
        self.current_points.clear()
        self.canvas.delete("temp")

        if not self.components:
            messagebox.showinfo("Nothing to undo", "There is no finished shape to remove yet.")
            return

        self.components.pop()
        # Rebuilding the saved polygons avoids leaving the removed part visible.
        self.canvas.delete("shape")
        for component in self.components:
            self._draw_component(component)

        self.status_label.config(text="Last shape part removed. Click the grid to keep drawing.")

    def _clear_current(self):
        self.current_points.clear()
        self.canvas.delete("temp")

    def _reset_all(self):
        # Reset is the deliberate full-stop action: data and canvas marks both disappear.
        self.components.clear()
        self.current_points.clear()
        # Rebuilding the grid after clearing gives the next attempt the same starting reference.
        self.canvas.delete("all")
        self._draw_grid()
        self.status_label.config(text="Drawing cleared. Click the grid to start again.")

    def _export_python_file(self):
        """Turn the drawing into a runnable Turtle program."""
        # Refuse an empty export because an empty Turtle shape would not teach much.
        if not self.components:
            messagebox.showerror("Error", "No shape components created to export.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py")])
        if not file_path:
            return

        # The generated file stays plain so it can be opened and understood in class.
        code_lines = [
            '"""Turtle program for my custom shape."""',
            'import turtle\n',
            '# Set up screen',
            'screen = turtle.Screen()',
            'screen.bgcolor("#f0f4f8")\n',
            '# Keep all of the shape parts together',
            'custom_shape = turtle.Shape("compound")\n'
        ]

        # Keep the same order as the drawing, making the export easier to compare.
        for idx, comp in enumerate(self.components, 1):
            pts_tuple = tuple(comp.points)
            code_lines.append(f'# Shape part {idx}')
            code_lines.append(f'comp_{idx}_points = {pts_tuple}')
            code_lines.append(f'custom_shape.addcomponent(comp_{idx}_points, "{comp.fill_color}", "{comp.outline_color}")\n')

        code_lines.extend([
            '# Register shape and instantiate turtle',
            'screen.register_shape("custom_user_shape", custom_shape)',
            't = turtle.Turtle()',
            't.shape("custom_user_shape")',
            't.shapesize(2, 2)',
            '\nturtle.done()'
        ])

        # UTF-8 keeps the saved file predictable on different computers.
        with open(file_path, "w", encoding="utf-8") as file:
            file.write("\n".join(code_lines))

        messagebox.showinfo("Success", f"File successfully saved to:\n{file_path}")

    def _export_tuples_file(self):
        """Save the points separately so they can be inspected or reused."""
        # The point-list export is useful when checking the coordinate maths separately.
        if not self.components:
            messagebox.showerror("Error", "No components created to export.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not file_path:
            return

        lines = []
        # Include colours as well as points so the design is not separated from its data.
        for idx, comp in enumerate(self.components, 1):
            lines.append(f"Shape part {idx} ({comp.fill_color}, {comp.outline_color}):")
            lines.append(str(tuple(comp.points)) + "\n")

        with open(file_path, "w", encoding="utf-8") as file:
            file.write("\n".join(lines))

        messagebox.showinfo("Success", f"Tuples saved to:\n{file_path}")


if __name__ == "__main__":
    # This guard prevents the window opening when the classes are imported for testing.
    root = tk.Tk()
    app = ShapeDesignerApp(root)
    root.mainloop()