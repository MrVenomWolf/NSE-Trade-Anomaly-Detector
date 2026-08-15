"""
gui.py
=======
Professional Dark Terminal Theme for Trade Anomaly Detector.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

import config
import main as engine_main


class DashboardApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("NSE Trade Anomaly Detector")
        self.geometry("1150x720")
        self.configure(bg="#121212")

        self.anomalies_map = {}
        self.stock_cache = {}

        self._apply_dark_theme()
        self._setup_ui()

    def _apply_dark_theme(self):
        """Configure dark theme styling across all Tkinter widgets."""
        style = ttk.Style(self)
        style.theme_use("clam")

        BG_DARK, PANEL_BG, TEXT_LIGHT, ACCENT_BLUE = "#121212", "#1e1e1e", "#e1e1e1", "#007acc"

        style.configure(".", background=BG_DARK, foreground=TEXT_LIGHT, font=("Segoe UI", 9))
        style.configure("TFrame", background=BG_DARK)
        style.configure("TLabelframe", background=PANEL_BG, foreground="#00e676", relief="solid")
        style.configure("TLabelframe.Label", background=PANEL_BG, foreground="#00e676", font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background=BG_DARK, foreground=TEXT_LIGHT)
        style.configure("TCheckbutton", background=BG_DARK, foreground=TEXT_LIGHT)
        style.configure("TEntry", fieldbackground="#2d2d30", foreground="#ffffff", insertcolor="#ffffff")
        style.configure("TButton", background="#2d2d30", foreground="#ffffff", borderwidth=0, font=("Segoe UI", 9, "bold"))
        style.map("TButton", background=[("active", ACCENT_BLUE), ("disabled", "#333333")])

        style.configure(
            "Treeview",
            background="#1e1e1e",
            foreground="#e1e1e1",
            fieldbackground="#1e1e1e",
            rowheight=28,
            font=("Consolas", 9),
        )
        style.configure("Treeview.Heading", background="#2d2d30", foreground="#00e676", font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", ACCENT_BLUE)], foreground=[("selected", "#ffffff")])

    def _setup_ui(self):
        ctrl = ttk.Frame(self, padding=12)
        ctrl.pack(fill=tk.X)

        ttk.Label(ctrl, text="Threshold %:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.threshold_var = tk.StringVar(value="200")
        ttk.Entry(ctrl, textvariable=self.threshold_var, width=6).pack(side=tk.LEFT, padx=(6, 20))

        self.var_equities = tk.BooleanVar(value=True)
        self.var_forex = tk.BooleanVar(value=False)
        ttk.Checkbutton(ctrl, text="NSE Equities", variable=self.var_equities).pack(side=tk.LEFT, padx=8)
        ttk.Checkbutton(ctrl, text="Forex", variable=self.var_forex).pack(side=tk.LEFT, padx=8)

        self.btn_run = ttk.Button(ctrl, text="RUN SCAN", command=self.start_scan)
        self.btn_run.pack(side=tk.RIGHT, ipadx=10)

        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        left_frame = ttk.Frame(paned, padding=5)
        paned.add(left_frame, weight=1)

        columns = ("symbol", "delta", "value")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("symbol", text="SYMBOL")
        self.tree.heading("delta", text="DELTA %")
        self.tree.heading("value", text="VOLUME")

        self.tree.column("symbol", width=110, anchor="w")
        self.tree.column("delta", width=90, anchor="e")
        self.tree.column("value", width=120, anchor="e")

        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_stock_select)

        right_frame = ttk.Frame(paned, padding=5)
        paned.add(right_frame, weight=2)

        self.info_box = ttk.LabelFrame(right_frame, text=" MARKET DATA & SIGNALS ", padding=12)
        self.info_box.pack(fill=tk.X, pady=(0, 10))

        self.lbl_price_info = tk.Label(
            self.info_box,
            text="Select a flagged stock from the left table to load chart and analysis.",
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#aaaaaa",
            anchor="w",
            justify="left",
        )
        self.lbl_price_info.pack(fill=tk.X)

        self.fig, (self.ax_price, self.ax_vol) = plt.subplots(
            2, 1, figsize=(6, 4), sharex=True, gridspec_kw={"height_ratios": [2.5, 1]}, facecolor="#1e1e1e"
        )
        self._style_dark_axes()
        self.fig.tight_layout(pad=2)

        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _style_dark_axes(self):
        for ax in (self.ax_price, self.ax_vol):
            ax.set_facecolor("#121212")
            ax.tick_params(colors="#aaaaaa", labelsize=8)
            ax.xaxis.label.set_color("#aaaaaa")
            ax.yaxis.label.set_color("#aaaaaa")
            ax.title.set_color("#ffffff")
            for spine in ax.spines.values():
                spine.set_color("#333333")

    def start_scan(self):
        self.btn_run.config(state=tk.DISABLED, text="SCANNING...")
        self.tree.delete(*self.tree.get_children())
        self.anomalies_map.clear()
        self.stock_cache.clear()

        def worker():
            try:
                threshold_pct = float(self.threshold_var.get()) / 100.0
                anomalies = engine_main.run(
                    threshold=threshold_pct,
                    include_equities=self.var_equities.get(),
                    include_forex=self.var_forex.get(),
                    include_swaps=False,
                    include_news=False,
                )
                self.after(0, self.populate_table, anomalies)
            except Exception as e:
                self.after(0, messagebox.showerror, "Scan Error", f"Failed: {str(e)}")
            finally:
                self.after(0, lambda: self.btn_run.config(state=tk.NORMAL, text="RUN SCAN"))

        threading.Thread(target=worker, daemon=True).start()

    def populate_table(self, anomalies):
        for a in anomalies:
            item_id = self.tree.insert("", tk.END, values=(a.point.symbol, a.delta_pct, f"{a.point.value:,.0f}"))
            self.anomalies_map[item_id] = a

    def on_stock_select(self, event):
        selected = self.tree.selection()
        if selected and (anomaly := self.anomalies_map.get(selected[0])):
            threading.Thread(target=self.load_stock_chart, args=(anomaly,), daemon=True).start()

    def load_stock_chart(self, anomaly):
        symbol = anomaly.point.symbol

        if symbol in self.stock_cache:
            self._process_and_update_chart(symbol, self.stock_cache[symbol])
            return

        try:
            df = yf.Ticker(symbol).history(period="1mo")
            if df.empty:
                self.after(0, self.lbl_price_info.config, {"text": f"No data found for {symbol}", "fg": "#ff5252"})
                return

            self.stock_cache[symbol] = df
            self._process_and_update_chart(symbol, df)
        except Exception as e:
            err_msg = "Rate limit hit! Wait 10s." if "Too Many Requests" in str(e) else f"Error: {e}"
            self.after(0, self.lbl_price_info.config, {"text": err_msg, "fg": "#ff5252"})

    def _process_and_update_chart(self, symbol, df):
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Remove timezone so Matplotlib scales dates correctly
        df.index = df.index.tz_localize(None)

        close_series = pd.to_numeric(df["Close"], errors="coerce").dropna()
        if close_series.empty:
            self.after(0, self.lbl_price_info.config, {"text": f"No valid prices for {symbol}", "fg": "#ff5252"})
            return

        last_close = float(close_series.iloc[-1])
        high_price = float(df["High"].iloc[-1]) if "High" in df else last_close
        low_price = float(df["Low"].iloc[-1]) if "Low" in df else last_close

        info_text = (
            f"SYMBOL: {symbol:<12} | LAST CLOSE: ₹{last_close:,.2f}\n"
            f"DAY HIGH: ₹{high_price:,.2f}  | DAY LOW: ₹{low_price:,.2f}\n"
            f"BUY ZONE: ~₹{low_price * 0.99:,.2f}  | TARGET SELL: ~₹{last_close * 1.05:,.2f}"
        )

        self.after(0, self.update_chart_ui, symbol, df, info_text)

    def update_chart_ui(self, symbol, df, info_text):
        self.lbl_price_info.config(text=info_text, fg="#00e676")

        self.ax_price.clear()
        self.ax_vol.clear()
        self._style_dark_axes()

        # Plot Price and Volume
        self.ax_price.plot(df.index, df["Close"], label="Close Price", color="#00b0ff", lw=2)
        self.ax_price.set_title(f"{symbol} — Price & Volume Trend", color="#ffffff", fontsize=10, fontweight="bold")
        self.ax_price.grid(True, linestyle=":", alpha=0.3, color="#555555")

        colors = ["#00e676" if c >= o else "#ff5252" for c, o in zip(df["Close"], df["Open"])]
        self.ax_vol.bar(df.index, df["Volume"], color=colors, alpha=0.8)
        self.ax_vol.grid(True, linestyle=":", alpha=0.3, color="#555555")

        # Rescale date limits on change
        self.ax_price.relim()
        self.ax_price.autoscale_view()
        self.ax_vol.relim()
        self.ax_vol.autoscale_view()

        self.fig.autofmt_xdate()
        self.canvas.draw()


if __name__ == "__main__":
    app = DashboardApp()
    app.mainloop()