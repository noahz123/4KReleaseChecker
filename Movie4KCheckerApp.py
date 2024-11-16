import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import threading
import json
import ctypes
import os

class Plex4KChecker(tk.Tk):
    def __init__(self):
        super().__init__()
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()

        # Set default font to size 16
        from tkinter import font
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=16)

        # Apply font settings to ttk widgets
        self.option_add("*TButton.Font", default_font)
        self.option_add("*TLabel.Font", default_font)
        self.option_add("*TEntry.Font", default_font)
        self.option_add("*TFrame.Font", default_font)
        self.option_add("*TLabelFrame.Font", default_font)
        self.option_add("*TScrolledText.Font", default_font)

        self.title("Plex 4K Release Checker")
        self.geometry("900x900")
        self.resizable(False, False)

        # Load saved credentials if they exist
        self.credentials = self.load_credentials()

        # Configure grid layout for the main window
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # Create main container
        self.main_container = ttk.Frame(self)
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Credentials Frame
        self.create_credentials_frame()

        # Status Label
        self.status_label = ttk.Label(self.main_container, text="")
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        # Results Area
        self.create_results_area()

        # Control Buttons
        self.create_control_buttons()

        # Counter for movies checked
        self.movies_checked = 0
        self.movies_with_4k = 0

    def load_credentials(self):
        try:
            if os.path.exists('credentials.json'):
                with open('credentials.json', 'r') as f:
                    return json.load(f)
        except:
            pass
        return {
            'plex_url': '',
            'plex_token': '',
            'tmdb_api_key': ''
        }

    def save_credentials(self):
        credentials = {
            'plex_url': self.plex_url_entry.get(),
            'plex_token': self.plex_token_entry.get(),
            'tmdb_api_key': self.tmdb_api_key_entry.get()
        }
        with open('credentials.json', 'w') as f:
            json.dump(credentials, f)

    def create_credentials_frame(self):
        cred_frame = ttk.LabelFrame(self.main_container, text="Credentials")
        cred_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5, columnspan=2)

        # Plex URL
        ttk.Label(cred_frame, text="Plex Server URL:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.plex_url_entry = ttk.Entry(cred_frame, width=50)
        self.plex_url_entry.insert(0, self.credentials['plex_url'])
        self.plex_url_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        # Plex Token
        ttk.Label(cred_frame, text="Plex Token:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.plex_token_entry = ttk.Entry(cred_frame, width=50)
        self.plex_token_entry.insert(0, self.credentials['plex_token'])
        self.plex_token_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        # TMDB API Key
        ttk.Label(cred_frame, text="TMDB API Key:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.tmdb_api_key_entry = ttk.Entry(cred_frame, width=50)
        self.tmdb_api_key_entry.insert(0, self.credentials['tmdb_api_key'])
        self.tmdb_api_key_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')

    def create_results_area(self):
        results_frame = ttk.LabelFrame(self.main_container, text="Available 4K Releases")
        results_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        # Define a larger font for the results text
        results_font = font.Font(family="TkDefaultFont", size=16)

        # Configure the scrolled text widget with the larger font
        self.results_text = scrolledtext.ScrolledText(results_frame, height=20, font=results_font)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Allow the results area to expand
        self.main_container.rowconfigure(2, weight=1)

    def create_control_buttons(self):
        btn_frame = ttk.Frame(self.main_container)
        btn_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        ttk.Button(btn_frame, text="Check 4K Releases", command=self.start_check).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Results", command=self.clear_results).pack(side=tk.LEFT, padx=5)
        #ttk.Button(btn_frame, text="Save Credentials", command=self.save_credentials).pack(side=tk.LEFT, padx=5)

    def clear_results(self):
        self.results_text.delete(1.0, tk.END)
        self.status_label.config(text="")
        self.movies_checked = 0
        self.movies_with_4k = 0

    def update_status(self):
        self.status_label.config(
            text=f"Checking movie {self.movies_checked}... Found {self.movies_with_4k} movies with 4K releases"
        )

    def append_result(self, text):
        self.results_text.insert(tk.END, text)
        self.results_text.see(tk.END)

    def get_plex_sections(self):
        headers = {
            "Accept": "application/json",
            "X-Plex-Token": self.plex_token_entry.get()
        }
        url = f"{self.plex_url_entry.get()}/library/sections"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        if response.headers.get("Content-Type", "").startswith("application/xml"):
            root = ET.fromstring(response.text)
            return [
                {
                    "id": section.attrib.get("key"),
                    "type": section.attrib.get("type")
                }
                for section in root.findall(".//Directory")
            ]
        else:
            return [
                {
                    "id": section["key"],
                    "type": section["type"]
                }
                for section in response.json()["MediaContainer"]["Directory"]
            ]

    def get_1080p_movies(self, section):
        headers = {
            "Accept": "application/json",
            "X-Plex-Token": self.plex_token_entry.get()
        }
        movies_url = f"{self.plex_url_entry.get()}/library/sections/{section}/all"
        
        response = requests.get(movies_url, headers=headers)
        response.raise_for_status()
        
        if response.headers.get("Content-Type", "").startswith("application/xml"):
            root = ET.fromstring(response.text)
            movies = []
            for video in root.findall(".//Video"):
                media = video.find(".//Media")
                if media is not None and media.attrib.get("videoResolution") == "1080":
                    movies.append({
                        "title": video.attrib.get("title", "Unknown Title"),
                        "year": video.attrib.get("year", "Unknown Year")
                    })
            return movies
        else:
            return [
                {
                    "title": movie["title"],
                    "year": movie.get("year", "Unknown Year")
                }
                for movie in response.json()["MediaContainer"].get("Metadata", [])
                if any(
                    media.get("videoResolution") == "1080"
                    for media in movie.get("Media", [])
                )
            ]

    def get_tmdb_id(self, title, year):
        url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": self.tmdb_api_key_entry.get(),
            "query": title,
            "year": year
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                return data["results"][0]["id"]
        return None

    def has_4k_release(self, tmdb_id):
        base_url = "https://api.themoviedb.org/3/movie/"
        url = f"{base_url}{tmdb_id}/release_dates"
        response = requests.get(url, params={"api_key": self.tmdb_api_key_entry.get()})
        response.raise_for_status()
        data = response.json()

        for country in data.get("results", []):
            for release in country.get("release_dates", []):
                if "4K" in release.get("note", "").upper() or "UHD" in release.get("note", "").upper():
                    if release.get("type") == 5 or release.get("type") == 4:
                        return release
        return False

    def check_4k_releases(self):
        try:
            current_date = datetime.now()
            
            # Get movie section
            movie_section = None
            for section in self.get_plex_sections():
                if section["type"] == "movie":
                    movie_section = section["id"]
                    break
            
            if not movie_section:
                self.append_result("No movie section found in Plex library.\n")
                return

            # Get 1080p movies
            movies = self.get_1080p_movies(movie_section)
            
            for movie in movies:
                title = movie["title"]
                year = movie["year"]
                
                self.movies_checked += 1
                self.update_status()
                
                tmdb_id = self.get_tmdb_id(title, year)
                if tmdb_id:
                    has_4k = self.has_4k_release(tmdb_id)
                    if has_4k:
                        self.movies_with_4k += 1
                        self.update_status()
                        
                        date = datetime.strptime(has_4k.get("release_date").split("T")[0], "%Y-%m-%d")
                        formatted_date = date.strftime("%m-%d-%Y")
                        
                        if date > current_date:
                            self.append_result(f"{title} ({year})\nTo Be Released: {formatted_date}\n\n")
                        else:
                            self.append_result(f"{title} ({year})\nAlready Released: {formatted_date}\n\n")
            
            # Final status update
            self.status_label.config(
                text=f"Scan complete! Found {self.movies_with_4k} movies with 4K releases out of {self.movies_checked} checked."
            )
                
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def start_check(self):
        # Validate inputs
        if not all([self.plex_url_entry.get(), self.plex_token_entry.get(), self.tmdb_api_key_entry.get()]):
            messagebox.showerror("Error", "Please fill in all credentials")
            return

        self.clear_results()
        
        # Run the check in a separate thread to keep UI responsive
        thread = threading.Thread(target=self.check_4k_releases)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    app = Plex4KChecker()
    app.mainloop()