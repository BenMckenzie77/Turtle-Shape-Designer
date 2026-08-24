"""
Interactive Turtle Shape Designer

The idea is to let students draw a shape with clicks instead of having to
guess a long list of coordinates first. The finished drawing can then become
real Turtle code that they can open, edit, and learn from.
"""

# Tkinter supplies the window, canvas, buttons, labels, and file dialogs.
import tkinter as tk
# These tools handle colours, saving, and simple user feedback.
from tkinter import colorchooser, filedialog, messagebox


class ShapeComponent:
    """Keep the points and colours for one part of the drawing."""

    def __init__(self, points, fill_color="#3498db", outline_color="#000000"):
        # Each part keeps its own points, so one drawing can contain several polygons.
        self.points = points  # Coordinates are measured from the centre of the canvas.
        # Keeping colours with the part means later parts can look different.
        self.fill_color = fill_color
        self.outline_color = outline_color


class ShapeDesignerApp:
    """The window where the drawing is made and saved as Turtle code."""

    def __init__(self, root):
        # The root object is the main window created at the bottom of the file.
        self.root = root
        self.root.title("Turtle Shape Designer - Version 1")
        self.root.geometry("820x650")

        # These lists are the working memory: current_points is still being drawn,
        # while components contains parts that have already been saved.
        self.components = []
        self.current_points = []
        # These colours are used for the next part until the user chooses new ones.
        self.current_fill = "#3498db"
        self.current_outline = "#000000"
        # A centre origin keeps the coordinates compatible with Turtle.
        self.canvas_size = 450
        self.origin_x = self.canvas_size // 2
        self.origin_y = self.canvas_size // 2
        # Version 1 deliberately uses every click exactly where it was placed.
        self.instructions_visible = False
        self.snap_enabled = False

        self._build_ui()
        self._draw_grid()

    def _build_ui(self):
        """Build the drawing area and the controls beside it."""
        # The drawing area is on the left and the controls stay together on the right.
        # The extra space around the controls stops the buttons feeling squeezed in.
        left_frame = tk.Frame(self.root)
        self.left_frame = left_frame
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = tk.Frame(self.root, width=340, bg="#f0f4f8")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Every click on this canvas becomes one coordinate in the unfinished shape.
        self.canvas = tk.Canvas(
            left_frame, width=self.canvas_size, height=self.canvas_size, bg="white", cursor="cross"
        )
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # The status line gives basic feedback while the user works.
        self.status_label = tk.Label(
            left_frame, text="Click points, then press Add shape part.", font=("Arial", 9)
        )
        self.status_label.pack()

        # Headings separate the drawing controls from the export controls.
        tk.Label(right_frame, text="Shape controls", font=("Arial", 12, "bold"), bg="#f0f4f8").pack(anchor="w", pady=5)

        # The buttons open colour pickers and the small labels preview the current choices.
        tk.Button(right_frame, text="Choose inside colour", command=self._pick_fill, width=22).pack(pady=5)
        self.fill_preview = tk.Label(right_frame, text="  Inside colour  ", bg=self.current_fill, fg="white")
        self.fill_preview.pack(pady=2)

        tk.Button(right_frame, text="Choose outside line", command=self._pick_outline, width=22).pack(pady=5)
        self.outline_preview = tk.Label(right_frame, text="  Outside line  ", bg=self.current_outline, fg="white")
        self.outline_preview.pack(pady=2)

        # Version 1 keeps editing simple: add a part or reset the whole drawing.
        tk.Button(right_frame, text="Add this shape part", command=self._finish_component, bg="#2ecc71", fg="white", width=22).pack(pady=15)
        tk.Button(right_frame, text="Clear entire drawing", command=self._reset_all, bg="#e74c3c", fg="white", width=22).pack(pady=3)

        # The two exports have different jobs: a runnable program and a readable point list.
        tk.Label(right_frame, text="Save your work", font=("Arial", 14, "bold"), bg="#f0f4f8").pack(anchor="w", pady=(20, 5))
        tk.Button(right_frame, text="Save Turtle program", command=self._export_python_file, bg="#3498db", fg="white", width=22).pack(pady=5)
        tk.Button(right_frame, text="Save point list", command=self._export_tuples_file, width=22).pack(pady=3)
        self.instructions_button = tk.Button(right_frame, text="Show instructions", command=self._show_instructions, width=22)
        self.instructions_button.pack(pady=(15, 5))

        # The help panel explains the intended workflow inside the same window.
        self.instructions_panel = tk.Frame(self.root, bg="white", relief=tk.GROOVE, borderwidth=1)
        tk.Label(
            self.instructions_panel,
            text="How to make a shape",
            font=("Arial", 18, "bold"),
            bg="white",
        ).pack(anchor="w", pady=(12, 8), padx=30)
        tk.Label(
            self.instructions_panel,
            text=(
                "1. Click on the grid to place the corners of one part of your shape.\n\n"
                "2. Click 'Add this shape part' when that part is complete. You need at least 3 points.\n\n"
                "3. Keep clicking to draw another part, such as an eye, wheel, or handle.\n\n"
                "4. Use 'Clear entire drawing' to start over.\n\n"
                "5. Choose colours whenever you like, then click 'Save Turtle program' to create a Python file.\n\n"
                "The grey cross is the centre (0, 0)."
            ),
            justify=tk.LEFT,
            anchor="w",
            font=("Arial", 10),
            bg="white",
        ).pack(anchor="w", padx=30, pady=(0, 12))

    def _show_instructions(self):
        # Showing help uses the spare bottom area; hiding it restores the drawing view.
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
        # The cross makes it easier to find the Turtle origin.
        self.canvas.create_line(0, self.origin_y, self.canvas_size, self.origin_y, fill="#bdc3c7", width=2, tags="grid")
        self.canvas.create_line(self.origin_x, 0, self.origin_x, self.canvas_size, fill="#bdc3c7", width=2, tags="grid")

    def _on_canvas_click(self, event):
        """Turn a screen click into a point relative to the centre of the grid."""
        # Tkinter measures from the top-left, while Turtle measures from the centre.
        # Flipping the Y value makes the saved coordinates behave correctly in Turtle.
        turtle_x = event.x - self.origin_x
        turtle_y = self.origin_y - event.y

        self.current_points.append((turtle_x, turtle_y))
        
        # Redraw the temporary marks so every click is visible immediately.
        self.canvas.delete("temp")
        for point_x, point_y in self.current_points:
            screen_x = point_x + self.origin_x
            screen_y = self.origin_y - point_y
            self.canvas.create_oval(screen_x - 3, screen_y - 3, screen_x + 3, screen_y + 3, fill="black", tags="temp")

    def _draw_current_points(self):
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

    def _pick_fill(self):
        # The chosen fill colour is stored for the next shape part.
        color = colorchooser.askcolor(title="Choose Fill Color")[1]
        if color:
            self.current_fill = color
            self.fill_preview.config(bg=color)

    def _pick_outline(self):
        # The outline is separate so the border can contrast with the inside colour.
        color = colorchooser.askcolor(title="Choose Outline Color")[1]
        if color:
            self.current_outline = color
            self.outline_preview.config(bg=color)

    def _finish_component(self):
        """Turn the current clicks into one permanent part of the shape."""
        # Testing later showed that this first rule rejects a valid triangle.
        # That boundary issue is intentionally fixed in Version 2.
        if len(self.current_points) <= 3:
            self.status_label.config(text="Add more points before saving this shape.")
            return

        # Copy the points so new clicks cannot change a part that was already saved.
        component = ShapeComponent(list(self.current_points), self.current_fill, self.current_outline)
        self.components.append(component)

        # Draw the saved part so the person can see the complete shape grow.
        self._draw_component(component)

        self._clear_current()
        self.status_label.config(text=f"Added shape part {len(self.components)}. Click the grid to draw another part.")

    def _draw_component(self, component):
        """Put one saved shape part back on the canvas."""
        # Convert Turtle-style centre coordinates back into screen positions.
        canvas_points = []
        for x, y in component.points:
            canvas_points.extend([x + self.origin_x, self.origin_y - y])

        self.canvas.create_polygon(
            canvas_points, fill=component.fill_color, outline=component.outline_color, width=2, tags="shape"
        )

    def _clear_current(self):
        # This clears only the unfinished part and leaves completed parts alone.
        self.current_points.clear()
        self.canvas.delete("temp")

    def _reset_all(self):
        # Resetting clears both the stored data and the marks on the canvas.
        self.components.clear()
        self.current_points.clear()
        self.canvas.delete("all")
        self._draw_grid()
        self.status_label.config(text="Drawing cleared. Click the grid to start again.")

    def _export_python_file(self):
        """Turn the drawing into a runnable Turtle program."""
        if not self.components:
            # Version 1 only updates the status line when there is nothing to save.
            self.status_label.config(text="Nothing to export yet.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py")])
        if not file_path:
            return

        # Build the program as text so the saved file can be opened and studied.
        code_lines = [
            '"""Turtle program for my custom shape."""',
            'import turtle\n',
            '# Set up screen',
            'screen = turtle.Screen()',
            'screen.bgcolor("#f0f4f8")\n',
            '# Keep all of the shape parts together',
            'custom_shape = turtle.Shape("compound")\n'
        ]

        # Each saved part becomes one component in Turtle's compound shape.
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
            # There are no coordinates to write until at least one part is finished.
            self.status_label.config(text="Nothing to export yet.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not file_path:
            return

        # The point list makes it easy to inspect the coordinates without running Python.
        lines = []
        for idx, comp in enumerate(self.components, 1):
            lines.append(f"Shape part {idx} ({comp.fill_color}, {comp.outline_color}):")
            lines.append(str(tuple(comp.points)) + "\n")

        with open(file_path, "w", encoding="utf-8") as file:
            file.write("\n".join(lines))

        messagebox.showinfo("Success", f"Tuples saved to:\n{file_path}")


if __name__ == "__main__":
    # Create the window, attach the designer, and listen for mouse input.
    root = tk.Tk()
    app = ShapeDesignerApp(root)
    root.mainloop()