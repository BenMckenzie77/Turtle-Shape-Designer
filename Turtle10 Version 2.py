"""
Interactive Turtle Shape Designer

The idea is to let students draw a shape with clicks instead of having to
guess a long list of coordinates first. The finished drawing can then become
real Turtle code that they can open, edit, and learn from.
"""

import math
# Tkinter handles the small desktop interface rather than needing a separate framework.
import tkinter as tk
from tkinter import colorchooser, filedialog, font, messagebox


class ShapeComponent:
    """Keep the points and colours for one part of the drawing."""

    def __init__(self, points, fill_color="#3498db", outline_color="#000000"):
        # A component is one finished polygon inside the larger drawing.
        self.points = points  # List of (x, y) tuples relative to center (0,0)
        self.fill_color = fill_color
        self.outline_color = outline_color


class ShapeDesignerApp:
    """The window where the drawing is made and saved as Turtle code."""

    def __init__(self, root):
        # Version 2 keeps the original idea but starts adding ways to correct mistakes.
        self.root = root
        self.root.title("Turtle Shape Designer - Version 2")
        self.root.geometry("1000x800")
        self.root.minsize(950, 750)

        # This is the small bit of memory the app needs while someone draws.
        # Points are temporary until the user adds them as a finished shape part.
        # Finished parts and the part currently being clicked need separate lists.
        self.components = []
        self.current_points = []
        self.current_fill = "#3498db"
        self.current_outline = "#000000"
        self.canvas_size = 550
        self.origin_x = self.canvas_size // 2
        self.origin_y = self.canvas_size // 2
        self.instructions_visible = False
        # Corner snapping is the first attempt at making separate parts join neatly.
        self.snap_enabled = True
        self.snap_distance = 12
        self.heading_font = font.Font(family="Segoe UI", size=15, weight="bold")
        self.button_font = font.Font(family="Segoe UI", size=10)
        self.body_font = font.Font(family="Segoe UI", size=10)

        # UI setup and grid drawing are kept separate so each method has one clear job.
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

        # Every click becomes a coordinate, unless it is close enough to a saved corner to snap.
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

        # Undo last shape is useful when a complete part was added too early or in the wrong place.
        self._make_button(right_frame, "Add this shape part", self._finish_component, "#24a866", "white").pack(pady=(16, 5))
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
                "4. Use 'Undo last shape' to remove the last finished part, or 'Clear entire drawing' to start over.\n\n"
                "5. Snap mode joins clicks close to saved corners. Turn it off for completely free clicking.\n\n"
                "6. Choose colours whenever you like, then click 'Save Turtle program' to create a Python file.\n\n"
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
        # Help is kept in the main window so the drawing is never lost while reading it.
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
        # The cross makes it easier to see where the Turtle origin is.
        self.canvas.create_line(0, self.origin_y, self.canvas_size, self.origin_y, fill="#bdc3c7", width=2, tags="grid")
        self.canvas.create_line(self.origin_x, 0, self.origin_x, self.canvas_size, fill="#bdc3c7", width=2, tags="grid")

    def _toggle_snap(self):
        # Turning this off gives completely free clicks when precision snapping is unwanted.
        """Turn point snapping on or off for the next clicks."""
        self.snap_enabled = not self.snap_enabled
        state = "ON" if self.snap_enabled else "OFF"
        self.snap_button.config(text=f"Snap mode: {state}")

    def _nearby_saved_point(self, screen_x, screen_y):
        """Return the closest saved corner within snap distance."""
        # Version 2 checks corners only; line snapping is a later improvement.
        closest_point = None
        closest_distance = self.snap_distance

        # Search every saved part because a new part may connect to any older part.
        for component in self.components:
            for turtle_x, turtle_y in component.points:
                point_x = turtle_x + self.origin_x
                point_y = self.origin_y - turtle_y
                distance = math.hypot(screen_x - point_x, screen_y - point_y)
                if distance <= closest_distance:
                    closest_point = (point_x, point_y)
                    closest_distance = distance

        return closest_point

    def _on_canvas_click(self, event):
        """Turn a screen click into a point relative to the centre of the grid."""
        # Tkinter measures down from the top-left; Turtle measures up from the centre.
        click_x = event.x
        click_y = event.y
        # The snap result is still stored as ordinary Turtle coordinates afterwards.
        snapped_point = self._nearby_saved_point(click_x, click_y) if self.snap_enabled else None
        if snapped_point:
            click_x, click_y = snapped_point

        turtle_x = click_x - self.origin_x
        turtle_y = self.origin_y - click_y

        self.current_points.append((turtle_x, turtle_y))
        
        # Show the unfinished outline straight away, so clicks do not feel invisible.
        self._draw_current_points()

    def _draw_current_points(self):
        # Redrawing the temporary marks keeps undo and clicking visually consistent.
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
        # This method exists in the code base but the button is introduced in Version 3.
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
        # Version 2 fixes Version 1's mistake: three points are enough for a triangle.
        if len(self.current_points) < 3:
            messagebox.showwarning("Warning", "A polygon requires at least 3 points.")
            return

        # Copy the list so later clicks cannot alter a part that has already been saved.
        component = ShapeComponent(list(self.current_points), self.current_fill, self.current_outline)
        self.components.append(component)

        # Draw the saved part so the person can see the complete shape grow.
        self._draw_component(component)

        self._clear_current()
        self.status_label.config(text=f"Added shape part {len(self.components)}. Click the grid to draw another part.")

    def _draw_component(self, component):
        # The canvas needs screen coordinates even though the saved data uses Turtle coordinates.
        """Put one saved shape part back on the canvas."""
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

        # Remove the data first, then redraw the remaining parts from their saved values.
        self.components.pop()
        self.canvas.delete("shape")
        for component in self.components:
            self._draw_component(component)

        self.status_label.config(text="Last shape part removed. Click the grid to keep drawing.")

    def _clear_current(self):
        self.current_points.clear()
        self.canvas.delete("temp")

    def _reset_all(self):
        # A full reset clears both the visible canvas and the lists behind it.
        self.components.clear()
        self.current_points.clear()
        self.canvas.delete("all")
        self._draw_grid()
        self.status_label.config(text="Drawing cleared. Click the grid to start again.")

    def _export_python_file(self):
        """Turn the drawing into a runnable Turtle program."""
        # An empty drawing cannot produce a useful Turtle program.
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

        # Write each component in the same order it was added to the drawing.
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