"""
Interactive Turtle Shape Designer

The idea is to let students draw a shape with clicks instead of having to
guess a long list of coordinates first. The finished drawing can then become
real Turtle code that they can open, edit, and learn from.
"""

# Math is used to measure how close a click is to a corner or line.
import math
import tkinter as tk
from tkinter import colorchooser, filedialog, font, messagebox


class ShapeComponent:
    """Keep the points and colours for one part of the drawing."""

    def __init__(self, points, fill_color="#3498db", outline_color="#000000"):
        # Keeping one part together makes redraw, undo, and export easier to manage.
        self.points = points  # List of (x, y) tuples relative to center (0,0)
        self.fill_color = fill_color
        self.outline_color = outline_color


class ShapeDesignerApp:
    """The window where the drawing is made and saved as Turtle code."""

    def __init__(self, root):
        # This stage concentrates on making the controls and drawing feel more complete.
        self.root = root
        self.root.title("Turtle Shape Designer - Version 3")
        self.root.geometry("1050x850")
        self.root.minsize(950, 750)

        # This is the small bit of memory the app needs while someone draws.
        # Points are temporary until the user adds them as a finished shape part.
        # The current part is temporary; components are the parts the user has accepted.
        self.components = []
        self.current_points = []
        self.current_fill = "#3498db"
        self.current_outline = "#000000"
        self.canvas_size = 600
        self.origin_x = self.canvas_size // 2
        self.origin_y = self.canvas_size // 2
        self.instructions_visible = False
        # Snap mode is intended to make joins cleaner without changing far-away clicks.
        self.snap_enabled = True
        self.snap_distance = 12
        # Stage 3 has the main features, but the visual polish is still being worked on.
        self.heading_font = font.Font(family="Arial", size=14, weight="bold")
        self.button_font = font.Font(family="Arial", size=10)
        self.body_font = font.Font(family="Arial", size=10)

        self._build_ui()
        self._draw_grid()

    def _build_ui(self):
        """Build the drawing area and the controls beside it."""
        # I kept the drawing area on the left and the useful actions on the right.
        # The extra space around the controls stops the buttons feeling squeezed in.
        left_frame = tk.Frame(self.root)
        self.left_frame = left_frame
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 10), pady=10)

        right_frame = tk.Frame(self.root, width=340, bg="#f0f4f8")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 30), pady=10)

        # Every click becomes a coordinate, or is adjusted to the nearest saved point or line.
        self.canvas = tk.Canvas(
            left_frame, width=self.canvas_size, height=self.canvas_size, bg="white", cursor="cross"
        )
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # This sentence changes as the user works, so they always know what to do next.
        self.status_label = tk.Label(
            left_frame, text="Click the grid to draw a shape. Add it when you are finished.", font=self.body_font
        )
        self.status_label.pack()

        # These labels describe what will happen, so a first-time user can just follow along.
        tk.Label(right_frame, text="Build your shape", font=self.heading_font, bg="#f0f4f8").pack(anchor="w", pady=(5, 12))

        # Colours are optional, but seeing the preview makes the choice less mysterious.
        self._make_button(right_frame, "Choose inside colour", self._pick_fill).pack(pady=4)
        self.fill_preview = tk.Label(right_frame, text="  Inside colour  ", bg=self.current_fill, fg="white", font=self.body_font)
        self.fill_preview.pack(pady=2)

        self._make_button(right_frame, "Choose outside line", self._pick_outline).pack(pady=4)
        self.outline_preview = tk.Label(right_frame, text="  Outside line  ", bg=self.current_outline, fg="white", font=self.body_font)
        self.outline_preview.pack(pady=2)

        # Separate undo actions let the user repair a point or a whole finished part.
        self._make_button(right_frame, "Add this shape part", self._finish_component, "#24a866", "white").pack(pady=(16, 5))
        self._make_button(right_frame, "Undo last point", self._undo_last_point, "#f0a43c", "white").pack(pady=4)
        self._make_button(right_frame, "Undo last shape", self._undo_last_component, "#f0a43c", "white").pack(pady=4)
        self._make_button(right_frame, "Clear entire drawing", self._reset_all, "#d9534f", "white").pack(pady=4)
        self.snap_button = self._make_button(right_frame, "Snap mode: ON", self._toggle_snap)
        self.snap_button.pack(pady=(8, 4))

        # Saving is deliberately split into the useful Turtle program and the coordinate list.
        tk.Label(right_frame, text="Save your work", font=self.heading_font, bg="#f0f4f8").pack(anchor="w", pady=(22, 12))
        self._make_button(right_frame, "Save Turtle program", self._export_python_file, "#3188c9", "white").pack(pady=4)
        self._make_button(right_frame, "Save point list", self._export_tuples_file).pack(pady=4)
        self.instructions_button = self._make_button(right_frame, "Show instructions", self._show_instructions)
        self.instructions_button.pack(pady=(15, 5))

        # This panel is placed over the extra space at the bottom. Showing help
        # does not resize or move the drawing area at all.
        self.instructions_panel = tk.Frame(self.root, bg="white", relief=tk.GROOVE, borderwidth=1)
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
        """Use one clean button style throughout the control panel."""
        return tk.Button(
            parent,
            text=text,
            command=command,
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
        # Instructions share the window with the canvas so users can refer back while drawing.
        """Show or hide the instructions without taking away the drawing."""
        if self.instructions_visible:
            self.instructions_panel.place_forget()
            self.instructions_button.config(text="Show instructions")
        else:
            self.instructions_panel.place(relx=0, rely=1, anchor="sw", relwidth=1, height=210, x=0, y=-15)
            self.instructions_button.config(text="Back to drawing")
        self.instructions_visible = not self.instructions_visible

    def _draw_grid(self):
        """Draw the centre lines that make the Turtle coordinates easier to read."""
        self.canvas.delete("grid")
        # The cross is a visual reference for the (0, 0) Turtle origin.
        self.canvas.create_line(0, self.origin_y, self.canvas_size, self.origin_y, fill="#bdc3c7", width=2, tags="grid")
        self.canvas.create_line(self.origin_x, 0, self.origin_x, self.canvas_size, fill="#bdc3c7", width=2, tags="grid")

    def _toggle_snap(self):
        # The label makes the current mode visible without opening a settings window.
        """Turn point snapping on or off for the next clicks."""
        self.snap_enabled = not self.snap_enabled
        state = "ON" if self.snap_enabled else "OFF"
        self.snap_button.config(text=f"Snap mode: {state}")

    def _nearby_saved_point(self, screen_x, screen_y):
        """Return the closest saved corner or line point within snap distance."""
        # A small radius keeps snapping helpful instead of making every click jump unexpectedly.
        closest_point = None
        closest_distance = self.snap_distance

        for component in self.components:
            screen_points = [
                (turtle_x + self.origin_x, self.origin_y - turtle_y)
                for turtle_x, turtle_y in component.points
            ]

            # Check corners first, then check the nearest spot on each saved edge.
            snap_candidates = list(screen_points)
            for index, start in enumerate(screen_points):
                end = screen_points[(index + 1) % len(screen_points)]
                segment_x = end[0] - start[0]
                segment_y = end[1] - start[1]
                segment_length_squared = segment_x ** 2 + segment_y ** 2
                if segment_length_squared == 0:
                    continue

                position = (
                    ((screen_x - start[0]) * segment_x + (screen_y - start[1]) * segment_y)
                    / segment_length_squared
                )
                position = max(0, min(1, position))
                snap_candidates.append(
                    (start[0] + position * segment_x, start[1] + position * segment_y)
                )

            for point_x, point_y in snap_candidates:
                distance = math.hypot(screen_x - point_x, screen_y - point_y)
                # Known Version 3 boundary issue: a click exactly on the edge
                # of the snap radius does not snap.
                if distance <= closest_distance:
                    closest_point = (point_x, point_y)
                    closest_distance = distance

        return closest_point

    def _on_canvas_click(self, event):
        """Turn a screen click into a point relative to the centre of the grid."""
        # Tkinter measures down from the top-left; Turtle measures up from the centre.
        click_x = event.x
        click_y = event.y
        # Snapping happens before conversion so the stored point is exactly on the target.
        snapped_point = self._nearby_saved_point(click_x, click_y) if self.snap_enabled else None
        if snapped_point:
            click_x, click_y = snapped_point

        turtle_x = click_x - self.origin_x
        turtle_y = self.origin_y - click_y

        self.current_points.append((turtle_x, turtle_y))
        
        # Show the unfinished outline straight away, so clicks do not feel invisible.
        self._draw_current_points()

    def _draw_current_points(self):
        # Temporary points are redrawn as a group after every click and undo.
        """Redraw the unfinished points and lines after a click or undo."""
        self.canvas.delete("temp")
        screen_points = [
            (turtle_x + self.origin_x, self.origin_y - turtle_y)
            for turtle_x, turtle_y in self.current_points
        ]

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

        for start, end in zip(screen_points, screen_points[1:]):
            self.canvas.create_line(
                start[0], start[1], end[0], end[1], fill="gray", dash=(2, 2), tags="temp"
            )

    def _undo_last_point(self):
        """Remove only the latest unfinished click."""
        if not self.current_points:
            messagebox.showinfo("Nothing to undo", "There is no unfinished point to remove.")
            return

        self.current_points.pop()
        self._draw_current_points()

    def _pick_fill(self):
        color = colorchooser.askcolor(title="Choose Fill Color")[1]
        if color:
            self.current_fill = color
            self.fill_preview.config(bg=color)

    def _pick_outline(self):
        color = colorchooser.askcolor(title="Choose Outline Color")[1]
        if color:
            self.current_outline = color
            self.outline_preview.config(bg=color)

    def _finish_component(self):
        """Turn the current clicks into one permanent part of the shape."""
        if len(self.current_points) < 3:
            messagebox.showwarning("Warning", "A polygon requires at least 3 points.")
            return

        # Copy the list because the next shape part must start with fresh points.
        component = ShapeComponent(list(self.current_points), self.current_fill, self.current_outline)
        self.components.append(component)

        # Draw the saved part so the person can see the complete shape grow.
        self._draw_component(component)

        self._clear_current()
        self.status_label.config(text=f"Added shape part {len(self.components)}. Click the grid to draw another part.")

    def _draw_component(self, component):
        """Put one saved shape part back on the canvas."""
        # Convert the saved Turtle coordinates back to pixels for the Tkinter canvas.
        canvas_points = []
        for x, y in component.points:
            canvas_points.extend([x + self.origin_x, self.origin_y - y])

        self.canvas.create_polygon(
            canvas_points, fill=component.fill_color, outline=component.outline_color, width=2, tags="shape"
        )

    def _undo_last_component(self):
        """Remove only the most recently saved part, then redraw what remains."""
        self.current_points.clear()
        self.canvas.delete("temp")

        if not self.components:
            messagebox.showinfo("Nothing to undo", "There is no finished shape to remove yet.")
            return

        # Remove only the last accepted part and redraw the parts that remain.
        self.components.pop()
        self.canvas.delete("shape")
        for component in self.components:
            self._draw_component(component)

        self.status_label.config(text="Last shape part removed. Click the grid to keep drawing.")

    def _clear_current(self):
        self.current_points.clear()
        self.canvas.delete("temp")

    def _reset_all(self):
        # Reset is intentionally stronger than undo: it removes all accepted parts.
        self.components.clear()
        self.current_points.clear()
        self.canvas.delete("all")
        self._draw_grid()
        self.status_label.config(text="Drawing cleared. Click the grid to start again.")

    def _export_python_file(self):
        """Turn the drawing into a runnable Turtle program."""
        # Export only has something useful to write after a part has been accepted.
        if not self.components:
            messagebox.showerror("Error", "No shape components created to export.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py")])
        if not file_path:
            return

        code_lines = [
            '"""Turtle program for my custom shape."""',
            'import turtle\n',
            '# Set up screen',
            'screen = turtle.Screen()',
            'screen.bgcolor("#f0f4f8")\n',
            '# Keep all of the shape parts together',
            'custom_shape = turtle.Shape("compound")\n'
        ]

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

        with open(file_path, "w", encoding="utf-8") as file:
            file.write("\n".join(code_lines))

        messagebox.showinfo("Success", f"File successfully saved to:\n{file_path}")

    def _export_tuples_file(self):
        """Save the points separately so they can be inspected or reused."""
        if not self.components:
            messagebox.showerror("Error", "No components created to export.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not file_path:
            return

        lines = []
        for idx, comp in enumerate(self.components, 1):
            lines.append(f"Shape part {idx} ({comp.fill_color}, {comp.outline_color}):")
            lines.append(str(tuple(comp.points)) + "\n")

        with open(file_path, "w", encoding="utf-8") as file:
            file.write("\n".join(lines))

        messagebox.showinfo("Success", f"Tuples saved to:\n{file_path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ShapeDesignerApp(root)
    root.mainloop()