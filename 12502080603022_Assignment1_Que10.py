import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
import os


DATA_FILE = "assignments.json"


class AssignmentTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Assignment Tracker")
        self.root.geometry("1100x650")

        self.records = []
        self.load_data()
        self.create_widgets()
        self.refresh_table()

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            self.records = []
            return

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, list):
                self.records = data
            else:
                self.records = []

        except (json.JSONDecodeError, OSError):
            self.records = []

    def save_data(self):
        temp_file = DATA_FILE + ".tmp"

        try:
            with open(temp_file, "w", encoding="utf-8") as file:
                json.dump(self.records, file, indent=2)

            os.replace(temp_file, DATA_FILE)

        except OSError as error:
            if os.path.exists(temp_file):
                os.remove(temp_file)

            messagebox.showerror("Error", str(error))

    def create_widgets(self):
        title = ttk.Label(
            self.root,
            text="Assignment Tracker",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=10)

        form = ttk.Frame(self.root)
        form.pack(fill="x", padx=20, pady=10)

        ttk.Label(form, text="Enrollment").grid(
            row=0, column=0, padx=5, pady=5
        )

        self.enrollment_entry = ttk.Entry(form, width=18)
        self.enrollment_entry.grid(
            row=0, column=1, padx=5, pady=5
        )

        ttk.Label(form, text="Name").grid(
            row=0, column=2, padx=5, pady=5
        )

        self.name_entry = ttk.Entry(form, width=18)
        self.name_entry.grid(
            row=0, column=3, padx=5, pady=5
        )

        ttk.Label(form, text="Assignment").grid(
            row=0, column=4, padx=5, pady=5
        )

        self.assignment_entry = ttk.Entry(form, width=18)
        self.assignment_entry.grid(
            row=0, column=5, padx=5, pady=5
        )

        ttk.Label(form, text="Marks").grid(
            row=1, column=0, padx=5, pady=5
        )

        self.marks_entry = ttk.Entry(form, width=18)
        self.marks_entry.grid(
            row=1, column=1, padx=5, pady=5
        )

        ttk.Label(form, text="Remarks").grid(
            row=1, column=2, padx=5, pady=5
        )

        self.remarks_entry = ttk.Entry(form, width=18)
        self.remarks_entry.grid(
            row=1, column=3, padx=5, pady=5
        )

        ttk.Button(
            form,
            text="Add Submission",
            command=self.add_record
        ).grid(
            row=1, column=4, padx=5, pady=5
        )

        ttk.Button(
            form,
            text="Update Marks",
            command=self.update_marks
        ).grid(
            row=1, column=5, padx=5, pady=5
        )

        controls = ttk.Frame(self.root)
        controls.pack(fill="x", padx=20, pady=5)

        ttk.Label(controls, text="Filter").pack(side="left")

        self.filter_var = tk.StringVar(value="All")

        self.filter_box = ttk.Combobox(
            controls,
            textvariable=self.filter_var,
            values=["All", "Pending", "Completed"],
            state="readonly",
            width=15
        )
        self.filter_box.pack(side="left", padx=10)
        self.filter_box.bind(
            "<<ComboboxSelected>>",
            lambda event: self.refresh_table()
        )

        ttk.Button(
            controls,
            text="Export CSV",
            command=self.export_csv
        ).pack(side="right")

        columns = (
            "enrollment",
            "name",
            "assignment",
            "status",
            "marks",
            "remarks"
        )

        table_frame = ttk.Frame(self.root)
        table_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        self.table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "enrollment": "Enrollment",
            "name": "Name",
            "assignment": "Assignment",
            "status": "Status",
            "marks": "Marks",
            "remarks": "Remarks"
        }

        widths = {
            "enrollment": 130,
            "name": 160,
            "assignment": 160,
            "status": 100,
            "marks": 80,
            "remarks": 250
        }

        for column in columns:
            self.table.heading(
                column,
                text=headings[column]
            )
            self.table.column(
                column,
                width=widths[column]
            )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.table.yview
        )

        self.table.configure(
            yscrollcommand=scrollbar.set
        )

        self.table.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.table.bind(
            "<<TreeviewSelect>>",
            self.select_record
        )

    def get_form_data(self):
        enrollment = self.enrollment_entry.get().strip()
        name = self.name_entry.get().strip()
        assignment = self.assignment_entry.get().strip()
        marks_text = self.marks_entry.get().strip()
        remarks = self.remarks_entry.get().strip()

        if not enrollment or not name or not assignment:
            messagebox.showwarning(
                "Invalid Data",
                "Enrollment, name and assignment are required."
            )
            return None

        if marks_text:
            try:
                marks = float(marks_text)

                if marks < 0:
                    raise ValueError

            except ValueError:
                messagebox.showwarning(
                    "Invalid Marks",
                    "Marks must be a non-negative number."
                )
                return None
        else:
            marks = None

        status = "Completed" if marks is not None else "Pending"

        return {
            "enrollment": enrollment,
            "name": name,
            "assignment": assignment,
            "status": status,
            "marks": marks,
            "remarks": remarks
        }

    def add_record(self):
        record = self.get_form_data()

        if record is None:
            return

        self.records.append(record)
        self.save_data()
        self.clear_form()
        self.refresh_table()

    def select_record(self, event=None):
        selected = self.table.selection()

        if not selected:
            return

        index = int(selected[0])
        record = self.filtered_records[index]

        self.enrollment_entry.delete(0, tk.END)
        self.enrollment_entry.insert(
            0,
            record["enrollment"]
        )

        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(
            0,
            record["name"]
        )

        self.assignment_entry.delete(0, tk.END)
        self.assignment_entry.insert(
            0,
            record["assignment"]
        )

        self.marks_entry.delete(0, tk.END)

        if record["marks"] is not None:
            self.marks_entry.insert(
                0,
                str(record["marks"])
            )

        self.remarks_entry.delete(0, tk.END)
        self.remarks_entry.insert(
            0,
            record["remarks"]
        )

    def update_marks(self):
        selected = self.table.selection()

        if not selected:
            messagebox.showwarning(
                "Selection",
                "Select a submission first."
            )
            return

        marks_text = self.marks_entry.get().strip()

        try:
            marks = float(marks_text)

            if marks < 0:
                raise ValueError

        except ValueError:
            messagebox.showwarning(
                "Invalid Marks",
                "Enter valid marks."
            )
            return

        index = int(selected[0])
        record = self.filtered_records[index]

        record["marks"] = marks
        record["status"] = "Completed"
        record["remarks"] = self.remarks_entry.get().strip()

        self.save_data()
        self.refresh_table()

    def refresh_table(self):
        for item in self.table.get_children():
            self.table.delete(item)

        selected_filter = self.filter_var.get()

        if selected_filter == "All":
            self.filtered_records = self.records
        else:
            self.filtered_records = [
                record
                for record in self.records
                if record["status"] == selected_filter
            ]

        for index, record in enumerate(self.filtered_records):
            self.table.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    record["enrollment"],
                    record["name"],
                    record["assignment"],
                    record["status"],
                    "" if record["marks"] is None
                    else record["marks"],
                    record["remarks"]
                )
            )

    def clear_form(self):
        self.enrollment_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.assignment_entry.delete(0, tk.END)
        self.marks_entry.delete(0, tk.END)
        self.remarks_entry.delete(0, tk.END)

    def export_csv(self):
        if not self.records:
            messagebox.showinfo(
                "Export",
                "No records available."
            )
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if not path:
            return

        try:
            with open(
                path,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "enrollment",
                    "name",
                    "assignment",
                    "status",
                    "marks",
                    "remarks"
                ])

                for record in self.records:
                    writer.writerow([
                        record["enrollment"],
                        record["name"],
                        record["assignment"],
                        record["status"],
                        record["marks"],
                        record["remarks"]
                    ])

            messagebox.showinfo(
                "Export",
                "CSV exported successfully."
            )

        except OSError as error:
            messagebox.showerror(
                "Export Error",
                str(error)
            )


def main():
    root = tk.Tk()
    AssignmentTracker(root)
    root.mainloop()


if __name__ == "__main__":
    main()