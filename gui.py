import customtkinter as ctk
import threading
import pandas as pd
from tkinter import ttk
import tkinter as tk
from data import get_storage_data, get_rig_count_data, get_nat_gas_reports
from dev import evaluate_ng_storage_model
from saveimg import get_weather_count
import re

class NatGasGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Natural Gas Predictor Dashboard")
        self.geometry("800x600")  # Reduced size as requested

        # Set appearance
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Configure style for Treeview (Tables)
        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure("Treeview",
                           background="#2b2b2b",
                           foreground="white",
                           fieldbackground="#2b2b2b",
                           borderwidth=0)
        self.style.map("Treeview", background=[('selected', '#3a3a3a')])
        self.style.configure("Treeview.Heading",
                           background="#333333",
                           foreground="white",
                           relief="flat")

        # Layout configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=160, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="NG Predictor", font=ctk.CTkFont(size=18, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=10, pady=(20, 10))

        self.storage_button = ctk.CTkButton(self.sidebar_frame, text="EIA Storage", command=lambda: self.select_frame("storage"))
        self.storage_button.grid(row=1, column=0, padx=10, pady=5)

        self.rig_button = ctk.CTkButton(self.sidebar_frame, text="RIG Count", command=lambda: self.select_frame("rig"))
        self.rig_button.grid(row=2, column=0, padx=10, pady=5)

        self.weather_button = ctk.CTkButton(self.sidebar_frame, text="Weather", command=lambda: self.select_frame("weather"))
        self.weather_button.grid(row=3, column=0, padx=10, pady=5)

        self.demand_button = ctk.CTkButton(self.sidebar_frame, text="Demand", command=lambda: self.select_frame("demand"))
        self.demand_button.grid(row=4, column=0, padx=10, pady=5)

        self.refresh_button = ctk.CTkButton(self.sidebar_frame, text="Refresh All", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.refresh_all_data)
        self.refresh_button.grid(row=6, column=0, padx=10, pady=20)

        # Create frames
        self.storage_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.rig_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.weather_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.demand_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")

        # Initialize labels/text areas
        self.setup_storage_view()
        self.setup_rig_view()
        self.setup_weather_view()
        self.setup_demand_view()

        # Select default frame
        self.select_frame("storage")

        # Auto-fetch data on start
        self.refresh_all_data()

    def select_frame(self, name):
        # Reset buttons colors
        self.storage_button.configure(fg_color=("gray75", "gray25") if name == "storage" else "transparent")
        self.rig_button.configure(fg_color=("gray75", "gray25") if name == "rig" else "transparent")
        self.weather_button.configure(fg_color=("gray75", "gray25") if name == "weather" else "transparent")
        self.demand_button.configure(fg_color=("gray75", "gray25") if name == "demand" else "transparent")

        # Show frame
        if name == "storage":
            self.storage_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.storage_frame.grid_forget()

        if name == "rig":
            self.rig_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.rig_frame.grid_forget()

        if name == "weather":
            self.weather_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.weather_frame.grid_forget()

        if name == "demand":
            self.demand_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.demand_frame.grid_forget()

    # --- Setup Views ---
    def setup_storage_view(self):
        self.storage_title = ctk.CTkLabel(self.storage_frame, text="EIA Weekly Storage", font=ctk.CTkFont(size=20, weight="bold"))
        self.storage_title.pack(pady=10)
        
        self.storage_bias_label = ctk.CTkLabel(self.storage_frame, text="Bias: Loading...", font=ctk.CTkFont(size=16))
        self.storage_bias_label.pack(pady=5)

        self.storage_text = ctk.CTkTextbox(self.storage_frame, width=500, height=300)
        self.storage_text.pack(padx=20, pady=10)

    def setup_rig_view(self):
        self.rig_title = ctk.CTkLabel(self.rig_frame, text="Baker Hughes Rig Count", font=ctk.CTkFont(size=20, weight="bold"))
        self.rig_title.pack(pady=10)
        
        # Create Treeview for Rig Count
        self.rig_tree_container = ctk.CTkFrame(self.rig_frame)
        self.rig_tree_container.pack(padx=20, pady=10, fill="both", expand=True)

        self.rig_tree = ttk.Treeview(self.rig_tree_container, show="headings")
        self.rig_tree.pack(side="left", fill="both", expand=True)

        self.rig_scroll = ttk.Scrollbar(self.rig_tree_container, orient="vertical", command=self.rig_tree.yview)
        self.rig_scroll.pack(side="right", fill="y")
        self.rig_tree.configure(yscrollcommand=self.rig_scroll.set)

    def setup_weather_view(self):
        self.weather_title = ctk.CTkLabel(self.weather_frame, text="Weather Insights", font=ctk.CTkFont(size=20, weight="bold"))
        self.weather_title.pack(pady=10)
        
        # Create Treeview for Weather
        self.weather_tree_container = ctk.CTkFrame(self.weather_frame)
        self.weather_tree_container.pack(padx=20, pady=10, fill="both", expand=False)

        self.weather_tree = ttk.Treeview(self.weather_tree_container, columns=("Section", "Status", "Duration"), show="headings", height=5)
        self.weather_tree.heading("Section", text="Timeframe")
        self.weather_tree.heading("Status", text="Forecast")
        self.weather_tree.heading("Duration", text="Details")
        
        self.weather_tree.column("Section", width=120)
        self.weather_tree.column("Status", width=120)
        self.weather_tree.column("Duration", width=250)
        
        self.weather_tree.pack(fill="both", expand=True)

    def setup_demand_view(self):
        self.demand_title = ctk.CTkLabel(self.demand_frame, text="Demand & Reports", font=ctk.CTkFont(size=20, weight="bold"))
        self.demand_title.pack(pady=10)
        
        self.demand_text = ctk.CTkTextbox(self.demand_frame, width=600, height=400)
        self.demand_text.pack(padx=20, pady=10)

    # --- Data Fetching ---
    def refresh_all_data(self):
        self.storage_bias_label.configure(text="Bias: Loading...")
        threading.Thread(target=self.fetch_storage, daemon=True).start()
        threading.Thread(target=self.fetch_rigs, daemon=True).start()
        threading.Thread(target=self.fetch_weather, daemon=True).start()
        threading.Thread(target=self.fetch_demand, daemon=True).start()

    def fetch_storage(self):
        try:
            raw_data = get_storage_data()
            model_output = evaluate_ng_storage_model(raw_data, "cold")
            
            self.after(0, self.update_storage_ui, model_output, raw_data)
        except Exception as e:
            self.after(0, lambda: self.storage_text.insert("0.0", f"Error: {e}"))

    def update_storage_ui(self, model, raw):
        bias = model.get("trade_bias", "Unknown")
        self.storage_bias_label.configure(text=f"Bias: {bias}")
        
        # Color code bias
        if "Bullish" in bias:
            self.storage_bias_label.configure(text_color="#2ECC71") # Brighter green
        elif "Bearish" in bias:
            self.storage_bias_label.configure(text_color="#E74C3C") # Brighter red
        else:
            self.storage_bias_label.configure(text_color="white")

        summary = f"Actual Change: {model['actual_change_bcf']} Bcf\n"
        summary += f"Expected Change: {model['expected_change_bcf']} Bcf\n"
        summary += f"Deviation: {model['weekly_deviation_bcf']} Bcf\n"
        summary += f"YoY Tightness: {model['yoy_tightness_pct']}%\n"
        summary += f"5Y Cushion: {model['five_year_cushion_pct']}%\n"
        summary += f"Expected Price Move: {model['expected_price_move_pct']}%\n"
        summary += f"Signal Strength: {model['signal_strength']}\n"
        
        self.storage_text.delete("1.0", "end")
        self.storage_text.insert("1.0", summary)

    def fetch_rigs(self):
        try:
            df = get_rig_count_data()
            self.after(0, self.update_rig_ui, df)
        except Exception as e:
            print(f"Rig fetch error: {e}")

    def update_rig_ui(self, df):
        # Clear existing
        for i in self.rig_tree.get_children():
            self.rig_tree.delete(i)

        if df.empty:
            return

        # Setup columns
        self.rig_tree["columns"] = list(df.columns)
        for col in df.columns:
            self.rig_tree.heading(col, text=col)
            self.rig_tree.column(col, width=80, anchor="center")

        # Insert data
        for index, row in df.iterrows():
            self.rig_tree.insert("", "end", values=list(row))

    def fetch_weather(self):
        try:
            report_data = get_weather_count()
            self.after(0, self.update_weather_ui, report_data)
        except Exception as e:
            print(f"Weather fetch error: {e}")

    def update_weather_ui(self, data):
        # data: [report, lat_rep, week_max_weather, range_max_weather, week_max_count, range_max_count, last_day_weather, day_1_weather]
        # Clear existing
        for i in self.weather_tree.get_children():
            self.weather_tree.delete(i)

        try:
            if len(data) >= 8:
                day_1 = data[7].upper()
                week_weather = data[2].upper()
                week_days = data[4]
                extended_weather = data[3].upper()
                extended_days = data[5]
                last_day = data[6].upper()

                self.weather_tree.insert("", "end", values=("Today (Day 1)", day_1, "Immediate outlook"))
                self.weather_tree.insert("", "end", values=("Next Week", week_weather, f"{week_days} days expected"))
                self.weather_tree.insert("", "end", values=("8-16 Days", extended_weather, f"{extended_days} days expected"))
                self.weather_tree.insert("", "end", values=("Last Day", last_day, "Final forecast day"))
            else:
                self.weather_tree.insert("", "end", values=("Error", "Data Incomplete", "Check sources"))

        except Exception as e:
            print(f"Weather UI update error: {e}")

    def fetch_demand(self):
        try:
            reps = get_nat_gas_reports()
            report_str = f"DAILY HEADLINE:\n{reps.get('daily_head', 'N/A')}\n\n"
            report_str += f"DAILY REPORT:\n{reps.get('daily_report', 'N/A')}\n\n"
            report_str += f"WEEKLY REPORT:\n{reps.get('weekly_report', 'N/A')}\n\n"
            report_str += f"DAY ONE FORECAST:\n{reps.get('day_one_rep', 'N/A')}"
            self.after(0, self.update_demand_ui, report_str)
        except Exception as e:
            self.after(0, lambda: self.demand_text.insert("0.0", f"Error: {e}"))

    def update_demand_ui(self, data):
        self.demand_text.delete("1.0", "end")
        self.demand_text.insert("1.0", data)

if __name__ == "__main__":
    app = NatGasGUI()
    app.mainloop()
