import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkintermapview import TkinterMapView
import numpy as np
import rasterio  # To handle the raster file (GeoTIFF)
from geopy.geocoders import Nominatim
from sentinelhub import BBox, CRS

from src.utils.gis_helpers import plot_geotiff, convert_bbox_to_utm
from src.utils.lst_calculator import calculate_lst
from src.utils.sentinel_data import SentinelData
from src.utils.ui_calculator import calculate_ui  # Assuming a new UI calculation function


class SentinelDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sentinel Data Downloader and Processor")

        # Create a main frame to hold the notebook and map side by side
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Configure the main_frame grid
        self.main_frame.columnconfigure(0, weight=3)  # Tabs will have more width
        self.main_frame.columnconfigure(1, weight=2)  # Map will have less width
        self.main_frame.rowconfigure(0, weight=1)

        # Create the notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Create tabs
        self.download_tab = ttk.Frame(self.notebook)
        self.ui_tab = ttk.Frame(self.notebook)
        self.lst_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.download_tab, text="Download Data")
        self.notebook.add(self.ui_tab, text="Calculate UI")
        self.notebook.add(self.lst_tab, text="Calculate LST")

        # Set up the Download tab
        self.setup_download_tab()

        # Set up the LST tab
        self.setup_lst_tab()

        # Set up the UI tab
        self.setup_ui_tab()

        # Variable to store the output directory path
        self.output_dir = ""

        # Create the map section
        self.setup_map_section()

    def setup_download_tab(self):
        # Use a grid layout manager to organize widgets
        # Create a frame inside the download tab to hold all widgets
        self.download_frame = tk.Frame(self.download_tab)
        self.download_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Input fields for downloading data
        self.bbox_label = tk.Label(self.download_frame, text="Bounding Box (comma-separated):")
        self.bbox_label.grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.bbox_entry = tk.Entry(self.download_frame, width=40)
        self.bbox_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.bbox_entry.insert(0, "497000,5664900,501700,5668400")  # Default BBox

        self.crs_label = tk.Label(self.download_frame, text="CRS (EPSG code):")
        self.crs_label.grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.crs_entry = tk.Entry(self.download_frame, width=40)
        self.crs_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        self.crs_entry.insert(0, "32633")  # Default CRS

        self.start_date_label = tk.Label(self.download_frame, text="Start Date (YYYY-MM-DD):")
        self.start_date_label.grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.start_date_entry = tk.Entry(self.download_frame, width=40)
        self.start_date_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        self.start_date_entry.insert(0, "2024-06-01")  # Default start date

        self.end_date_label = tk.Label(self.download_frame, text="End Date (YYYY-MM-DD):")
        self.end_date_label.grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.end_date_entry = tk.Entry(self.download_frame, width=40)
        self.end_date_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        self.end_date_entry.insert(0, "2024-07-01")  # Default end date

        self.filter_label = tk.Label(self.download_frame, text="Filter (e.g. 'eo:cloud_cover < 50'):")
        self.filter_label.grid(row=4, column=0, padx=5, pady=5, sticky='e')
        self.filter_entry = tk.Entry(self.download_frame, width=40)
        self.filter_entry.grid(row=4, column=1, padx=5, pady=5, sticky='w')
        self.filter_entry.insert(0, "eo:cloud_cover < 30")  # Default filter

        # Output directory label, entry, and browse button in the same row
        self.output_dir_label = tk.Label(self.download_frame, text="Output Directory:")
        self.output_dir_label.grid(row=5, column=0, padx=5, pady=5, sticky='e')
        self.output_dir_entry = tk.Entry(self.download_frame, width=30)  # Reduced width
        self.output_dir_entry.grid(row=5, column=1, padx=5, pady=5, sticky='w')
        self.output_dir_button = tk.Button(self.download_frame, text="Browse", command=self.browse_output_dir)
        self.output_dir_button.grid(row=5, column=2, padx=5, pady=5, sticky='w')

        # Adjust column weights for proper resizing
        self.download_frame.columnconfigure(1, weight=1)

        # Action buttons for downloading, placed in one row
        self.button_frame = tk.Frame(self.download_frame)
        self.button_frame.grid(row=6, column=0, columnspan=3, pady=10)

        self.download_s2_s3_button = tk.Button(self.button_frame, text="Download S2 & S3 Data (LST)",
                                               command=self.download_s2_s3_data)
        self.download_s2_s3_button.pack(side=tk.LEFT, padx=5)

        self.download_weekly_s2_button = tk.Button(self.button_frame, text="Download S2 Weekly (UI)",
                                                   command=self.download_weekly_s2)
        self.download_weekly_s2_button.pack(side=tk.LEFT, padx=5)

    def setup_lst_tab(self):
        # Add a header or description for the tab
        self.lst_description_label = tk.Label(self.lst_tab, text="Land Surface Temperature (LST) - Alpha Version",
                                              font=("Arial", 14, "bold"))
        self.lst_description_label.pack(padx=10, pady=10)

        # Add a sub-description about the version status
        self.lst_version_label = tk.Label(self.lst_tab,
                                          text="Note: This feature is in alpha version and may not work as expected.",
                                          fg="red")
        self.lst_version_label.pack(padx=10, pady=5)

        # Button to calculate LST (Land Surface Temperature)
        self.calculate_lst_button = tk.Button(self.lst_tab, text="Calculate LST", command=self.calculate_lst)
        self.calculate_lst_button.pack(padx=10, pady=10)

    def setup_ui_tab(self):
        # Add a header or description for the tab
        self.ui_description_label = tk.Label(self.ui_tab, text="Urban Index (UI) Calculation - Alpha Version",
                                             font=("Arial", 14, "bold"))
        self.ui_description_label.pack(padx=10, pady=10)

        # Add a sub-description about the method
        # Use a Text widget with a scrollbar for the long text
        text_frame = tk.Frame(self.ui_tab)
        text_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.ui_text = tk.Text(text_frame, height=10, wrap='word', fg='red')
        self.ui_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = tk.Scrollbar(text_frame, command=self.ui_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ui_text['yscrollcommand'] = scrollbar.set

        # Insert the text into the Text widget
        ui_info = (
            "This method identifies and masks water bodies using the Normalized Difference Water Index (NDWI) "
            "and the Modified NDWI (MNDWI), calculates the Urban Index (UI) to detect urban areas, and aggregates the results.\n\n"
            "• NDWI enhances water features while suppressing vegetation and soil noise.\n"
            "• MNDWI improves water detection by reducing urban area interference.\n"
            "• UI distinguishes urban areas from other land covers.\n\n"
            "Note: This is an alpha version; water may still be misidentified as roofs or other urban structures."
        )
        self.ui_text.insert(tk.END, ui_info)
        self.ui_text.configure(state='disabled')  # Make the text read-only

        # UI parameters: NDWI threshold, MNDWI threshold, and method
        self.ui_params_frame = tk.Frame(self.ui_tab)
        self.ui_params_frame.pack(padx=10, pady=10)

        self.ndwi_label = tk.Label(self.ui_params_frame, text="NDWI Threshold:")
        self.ndwi_label.grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.ndwi_entry = tk.Entry(self.ui_params_frame, width=20)
        self.ndwi_entry.grid(row=0, column=1, padx=5, pady=5)
        self.ndwi_entry.insert(0, "0.3")  # Default value

        self.mndwi_label = tk.Label(self.ui_params_frame, text="MNDWI Threshold:")
        self.mndwi_label.grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.mndwi_entry = tk.Entry(self.ui_params_frame, width=20)
        self.mndwi_entry.grid(row=1, column=1, padx=5, pady=5)
        self.mndwi_entry.insert(0, "0.3")  # Default value

        self.method_label = tk.Label(self.ui_params_frame, text="Aggregation Method:")
        self.method_label.grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.method_combobox = ttk.Combobox(self.ui_params_frame, values=["average", "median", "max", "min"])
        self.method_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.method_combobox.set("average")  # Default value

        # Button to calculate UI
        self.calculate_ui_button = tk.Button(self.ui_tab, text="Calculate UI", command=self.calculate_ui)
        self.calculate_ui_button.pack(padx=10, pady=10)

    def setup_map_section(self):
        # Map Section: Integrating OpenStreetMap with a bounding box selector
        self.map_frame = tk.Frame(self.main_frame)
        # Configure the map_frame grid
        self.map_frame.rowconfigure(0, weight=1)
        self.map_frame.columnconfigure(0, weight=1)

        # Place the map_frame in the main_frame grid
        self.map_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Create the map widget
        self.map_widget = TkinterMapView(self.map_frame)
        self.map_widget.grid(row=0, column=0, sticky="nsew")

        # City search field and button in one row
        self.search_frame = tk.Frame(self.map_frame)
        self.search_frame.grid(row=1, column=0, pady=5)

        self.city_entry = tk.Entry(self.search_frame, width=20)
        self.city_entry.pack(side=tk.LEFT, padx=5)
        self.search_button = tk.Button(self.search_frame, text="Search City", command=self.search_city)
        self.search_button.pack(side=tk.LEFT, padx=5)

        # Buttons under the map in one row
        self.map_button_frame = tk.Frame(self.map_frame)
        self.map_button_frame.grid(row=2, column=0, pady=5)

        self.update_bbox_button = tk.Button(self.map_button_frame, text="Update BBox from Map",
                                            command=self.update_bbox_from_map)
        self.update_bbox_button.pack(side=tk.LEFT, padx=5)

        # Set default map position and zoom
        self.map_widget.set_position(51.155, 14.988)  # Default location Görlitz/Zgorzelec
        self.map_widget.set_zoom(10)


    def browse_output_dir(self):
        self.output_dir = filedialog.askdirectory()
        if self.output_dir:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, self.output_dir)
            messagebox.showinfo("Selected Directory", f"Output Directory set to: {self.output_dir}")

    def update_bbox_from_map(self):
        # Get the current map extent (bounding box)
        # Update widget dimensions
        self.map_widget.update_idletasks()
        width = self.map_widget.winfo_width()
        height = self.map_widget.winfo_height()
        # Convert all four corners
        top_left = self.map_widget.convert_canvas_coords_to_decimal_coords(0, 0)
        top_right = self.map_widget.convert_canvas_coords_to_decimal_coords(width, 0)
        bottom_left = self.map_widget.convert_canvas_coords_to_decimal_coords(0, height)
        bottom_right = self.map_widget.convert_canvas_coords_to_decimal_coords(width, height)

        # Calculate min and max latitudes and longitudes
        lats = [top_left[0], top_right[0], bottom_left[0], bottom_right[0]]
        lngs = [top_left[1], top_right[1], bottom_left[1], bottom_right[1]]

        min_lat = min(lats)
        max_lat = max(lats)
        min_lng = min(lngs)
        max_lng = max(lngs)
        bounding_box_utm, crs_info = convert_bbox_to_utm(max_lat, min_lat, max_lng, min_lng)

        # Convert to the bounding box format
        bbox_str = f"{bounding_box_utm['west_x']},{bounding_box_utm['south_y']},{bounding_box_utm['east_x']},{bounding_box_utm['north_y']}"
        self.bbox_entry.delete(0, tk.END)
        self.bbox_entry.insert(0, bbox_str)
        self.crs_entry.delete(0, tk.END)
        self.crs_entry.insert(0, str(crs_info['epsg_code']))
        messagebox.showinfo("BBox Updated", f"New Bounding Box: {bbox_str}")

    def search_city(self):
        geolocator = Nominatim(user_agent="bbox_search")
        city_name = self.city_entry.get()

        if not city_name:
            messagebox.showerror("Error", "Please enter a city name.")
            return

        try:
            location = geolocator.geocode(city_name)
            if location:
                self.map_widget.set_position(location.latitude, location.longitude)
                self.map_widget.set_zoom(12)
            else:
                messagebox.showerror("Error", "City not found.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def download_s2_s3_data(self):
        try:
            # Get input values
            bbox_coords = list(map(float, self.bbox_entry.get().split(',')))
            crs = int(self.crs_entry.get())
            start_date = self.start_date_entry.get()
            end_date = self.end_date_entry.get()
            date_range = (start_date, end_date)
            filter_string = self.filter_entry.get()

            # Validate output directory
            if not self.output_dir_entry.get():
                messagebox.showerror("Error", "Please select an output directory.")
                return

            # Create a SentinelData instance and download Sentinel-2 and Sentinel-3 data
            sentinel_data = SentinelData()
            sentinel_data.download_s2_s3_data_pack(bbox_coords, crs, date_range, 10, self.output_dir_entry.get(),
                                                   filter=filter_string)

            messagebox.showinfo("Success", "Sentinel-2 and Sentinel-3 data downloaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def download_weekly_s2(self):
        try:
            # Get input values
            bbox_coords = list(map(float, self.bbox_entry.get().split(',')))
            crs = int(self.crs_entry.get())
            start_date = self.start_date_entry.get()
            end_date = self.end_date_entry.get()
            date_range = (start_date, end_date)

            # Validate output directory
            if not self.output_dir_entry.get():
                messagebox.showerror("Error", "Please select an output directory.")
                return

            # Create a SentinelData instance and download data for each week
            sentinel_data = SentinelData()
            sentinel_data.download_s2_data_weekly(bbox_coords, crs, date_range, 10, self.output_dir_entry.get())

            messagebox.showinfo("Success", "Sentinel-2 weekly data downloaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def calculate_lst(self):
        try:
            if not self.output_dir_entry.get():
                messagebox.showerror("Error", "No output directory found. Please download the data first.")
                return

            # Call the function to calculate LST
            calculate_lst(self.output_dir_entry.get())
            messagebox.showinfo("Success", "LST calculation completed successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during LST calculation: {e}")

    def calculate_ui(self):
        try:
            if not self.output_dir_entry.get():
                messagebox.showerror("Error", "No output directory found. Please download the data first.")
                return

            # Get the UI calculation parameters
            ndwi_threshold = float(self.ndwi_entry.get())
            mndwi_threshold = float(self.mndwi_entry.get())
            method = self.method_combobox.get()

            # Call the function to calculate UI (Urban Index)
            raster_path = calculate_ui(self.output_dir_entry.get(), ndwi_threshold, mndwi_threshold, method)
            messagebox.showinfo("Success", f"UI calculation completed. Raster saved at {raster_path}")

            # Plot the generated raster on the map (if possible)
            plot_geotiff(raster_path)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during UI calculation: {e}")


# Initialize Tkinter root and run the app
root = tk.Tk()
app = SentinelDownloaderApp(root)
root.mainloop()
