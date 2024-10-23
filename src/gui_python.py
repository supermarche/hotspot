import tkinter as tk
from tkinter import filedialog, messagebox
from sentinelhub import BBox, CRS

from src.utils.lst_calculator import calculate_lst
from src.utils.sentinel_data import SentinelData
# Assuming `calculate_lst` is the function that processes LST

class SentinelDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sentinel Data Downloader")

        # Set default values
        self.default_bbox = "497000,5664900,501700,5668400"  # BBox for Görlitz/Zgorzelec
        self.default_crs = "32633"  # CRS for EPSG:32633
        self.default_start_date = "2024-06-01"
        self.default_end_date = "2024-07-01"
        self.default_filter = "eo:cloud_cover < 30"

        # Input fields
        self.bbox_label = tk.Label(root, text="Bounding Box (comma-separated):")
        self.bbox_label.grid(row=0, column=0, padx=10, pady=10)
        self.bbox_entry = tk.Entry(root, width=50)
        self.bbox_entry.grid(row=0, column=1, padx=10, pady=10)
        self.bbox_entry.insert(0, self.default_bbox)

        self.crs_label = tk.Label(root, text="CRS (EPSG code):")
        self.crs_label.grid(row=1, column=0, padx=10, pady=10)
        self.crs_entry = tk.Entry(root, width=50)
        self.crs_entry.grid(row=1, column=1, padx=10, pady=10)
        self.crs_entry.insert(0, self.default_crs)

        self.start_date_label = tk.Label(root, text="Start Date (YYYY-MM-DD):")
        self.start_date_label.grid(row=2, column=0, padx=10, pady=10)
        self.start_date_entry = tk.Entry(root, width=50)
        self.start_date_entry.grid(row=2, column=1, padx=10, pady=10)
        self.start_date_entry.insert(0, self.default_start_date)

        self.end_date_label = tk.Label(root, text="End Date (YYYY-MM-DD):")
        self.end_date_label.grid(row=3, column=0, padx=10, pady=10)
        self.end_date_entry = tk.Entry(root, width=50)
        self.end_date_entry.grid(row=3, column=1, padx=10, pady=10)
        self.end_date_entry.insert(0, self.default_end_date)

        self.filter_label = tk.Label(root, text="Filter (e.g. 'eo:cloud_cover < 50'):")
        self.filter_label.grid(row=4, column=0, padx=10, pady=10)
        self.filter_entry = tk.Entry(root, width=50)
        self.filter_entry.grid(row=4, column=1, padx=10, pady=10)
        self.filter_entry.insert(0, self.default_filter)

        self.output_dir_label = tk.Label(root, text="Output Directory:")
        self.output_dir_label.grid(row=5, column=0, padx=10, pady=10)
        self.output_dir_button = tk.Button(root, text="Browse", command=self.browse_output_dir)
        self.output_dir_button.grid(row=5, column=1, padx=10, pady=10)

        # Action buttons
        self.check_dates_button = tk.Button(root, text="Check Common Dates", command=self.check_common_dates)
        self.check_dates_button.grid(row=6, column=0, padx=10, pady=10)

        self.download_button = tk.Button(root, text="Download Data", command=self.download_data)
        self.download_button.grid(row=6, column=1, padx=10, pady=10)

        self.calculate_lst_button = tk.Button(root, text="Calculate LST", command=self.calculate_lst)
        self.calculate_lst_button.grid(row=7, column=0, columnspan=2, padx=10, pady=10)
        self.calculate_lst_button.config(state="disabled")  # Initially disabled

        # Variable to store the output directory path
        self.output_dir = ""

    def browse_output_dir(self):
        self.output_dir = filedialog.askdirectory()
        if self.output_dir:
            messagebox.showinfo("Selected Directory", f"Output Directory set to: {self.output_dir}")

    def check_common_dates(self):
        try:
            # Get input values from the fields
            bbox_coords = list(map(float, self.bbox_entry.get().split(',')))
            crs = int(self.crs_entry.get())
            start_date = self.start_date_entry.get()
            end_date = self.end_date_entry.get()
            date_range = (start_date, end_date)
            filter_string = self.filter_entry.get()

            # Create a SentinelData instance and search for common dates
            sentinel_data = SentinelData()
            result = sentinel_data.search_data(bbox_coords, crs, date_range, filter=filter_string)

            # Show result in a message box
            common_dates = result.get("common_dates", [])
            if common_dates:
                messagebox.showinfo("Common Dates", f"Common dates found: {', '.join(common_dates)}")
            else:
                messagebox.showinfo("No Common Dates", "No common dates found between Sentinel-2 and Sentinel-3 data.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def download_data(self):
        try:
            # Get input values from the fields
            bbox_coords = list(map(float, self.bbox_entry.get().split(',')))
            crs = int(self.crs_entry.get())
            start_date = self.start_date_entry.get()
            end_date = self.end_date_entry.get()
            date_range = (start_date, end_date)
            filter_string = self.filter_entry.get()

            # Validate output directory
            if not self.output_dir:
                messagebox.showerror("Error", "Please select an output directory.")
                return

            # Create a SentinelData instance and download data
            sentinel_data = SentinelData()
            sentinel_data.download_data_pack(bbox_coords, crs, date_range, 10, self.output_dir, filter=filter_string)

            messagebox.showinfo("Success", "Sentinel data downloaded successfully.")
            self.calculate_lst_button.config(state="normal")  # Enable LST button after download
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def calculate_lst(self):
        try:
            # Assuming there is a `calculate_lst` function that processes LST
            # The calculation should happen on the downloaded data
            if not self.output_dir:
                messagebox.showerror("Error", "No output directory found. Please download the data first.")
                return

            # Call the function to calculate LST (replace with actual function)
            calculate_lst(self.output_dir)  # Assuming `calculate_lst` takes the output directory as an argument

            messagebox.showinfo("Success", "LST calculation completed successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during LST calculation: {e}")

# Initialize Tkinter root and run the app
root = tk.Tk()
app = SentinelDownloaderApp(root)
root.mainloop()
