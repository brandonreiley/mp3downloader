import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import threading
import sys

def download_mp3(url_entry, save_path_var, download_btn, progress_bar, status_label, root):
    url = url_entry.get().strip()
    save_path = save_path_var.get()
    
    if not url:
        messagebox.showerror("Error", "Please enter a valid URL")
        return
    
    # Validate save path exists and is writable
    if not save_path or not os.path.exists(save_path):
        messagebox.showerror("Error", f"Invalid save path: {save_path}")
        return
    
    if not os.access(save_path, os.W_OK):
        messagebox.showerror("Error", f"No write permission for: {save_path}")
        return
    
    # Disable button and show progress bar
    download_btn.config(state=tk.DISABLED)
    progress_bar.config(value=0)
    status_label.config(text="Starting yt-dlp...")
    
    output_template = os.path.join(save_path, "[%(artist)s] %(title)s.%(ext)s")
    
    def run_download():
        saved_filename = None
        try:
            cmd = [
                "yt-dlp",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "320K",
                "--embed-thumbnail",
                "--convert-thumbnails", "jpg",
                "--ppa", "EmbedThumbnail+ffmpeg_o:-c:v mjpeg -vf crop=\"'if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'\"",
                "--embed-metadata",
                "-o", output_template,
                url
            ]

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            for line in process.stdout:
                line = line.strip()
                
                if "[info]" in line and "Downloading" in line:
                    status_label.config(text="Grabbing URL info...")
                    root.update_idletasks()
                
                if "[download]" in line:
                    if "%" in line:
                        try:
                            percent_str = line.split("[download]")[1].split("%")[0].strip()
                            percent = float(percent_str)
                            progress_bar.config(value=percent)
                            status_label.config(text=f"Downloading... {percent:.1f}%")
                            root.update_idletasks()
                        except (ValueError, IndexError):
                            pass
                    else:
                        status_label.config(text="Downloading...")
                        root.update_idletasks()
                
                if "[ExtractAudio]" in line:
                    status_label.config(text="Converting to MP3...")
                    root.update_idletasks()
                
                if "[ffmpeg]" in line and "Embed" in line:
                    status_label.config(text="Embedding thumbnail...")
                    root.update_idletasks()
                
                # Capture the destination filename
                if "Destination:" in line:
                    saved_filename = line.split("Destination:")[-1].strip()
            
            process.wait()
            
            if process.returncode == 0:
                progress_bar.config(value=100)
                status_label.config(text="Complete!")
                
                if saved_filename:
                    # Prompt to edit filename with Save As dialog
                    new_path = filedialog.asksaveasfilename(
                        title="Save MP3 as",
                        initialdir=save_path,
                        initialfile=os.path.basename(saved_filename),
                        defaultextension=".mp3",
                        filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
                    )
                    
                    if new_path:
                        if new_path != saved_filename:
                            try:
                                os.rename(saved_filename, new_path)
                                saved_filename = new_path
                            except OSError as e:
                                messagebox.showerror("Error", f"Failed to rename file: {e}")
                        messagebox.showinfo("Success", f"Download completed!\nSaved as: {os.path.basename(saved_filename)}")
                    else:
                        # User cancelled - delete the file
                        try:
                            if os.path.exists(saved_filename):
                                os.remove(saved_filename)
                        except OSError as e:
                            messagebox.showerror("Error", f"Failed to delete file: {e}")
                        status_label.config(text="Download cancelled and file removed.")
            else:
                stderr = process.stderr.read() if process.stderr else ""
                messagebox.showerror("Error", f"Failed to download:\n{stderr}")
        
        except FileNotFoundError:
            messagebox.showerror("Error", "yt-dlp not found. Please install it: pip install yt-dlp")
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")
        finally:
            download_btn.config(state=tk.NORMAL)
            status_label.config(text="")
            progress_bar.config(value=0)
    
    # Run download in background thread
    thread = threading.Thread(target=run_download, daemon=True)
    thread.start()

# Create main window with error handling
def create_ui():
    try:
        # Create main window
        root = tk.Tk()
        root.title("MP3 Downloader/Converter")
        root.geometry("600x350")

        # URL input
        tk.Label(root, text="SoundCloud/YouTube URL:").pack(pady=5)
        url_entry = tk.Entry(root, width=80)
        url_entry.pack(pady=5)
        url_entry.focus_set()

        # Save path
        tk.Label(root, text="Save Path:").pack(pady=5)
        default_save_path = os.path.expanduser("~/Desktop/DJ/New Songs")
        if not os.path.exists(default_save_path):
            default_save_path = os.path.expanduser("~")
        save_path_var = tk.StringVar(value=default_save_path)
        save_path_entry = tk.Entry(root, textvariable=save_path_var, width=80)
        save_path_entry.pack(pady=5)

        def browse_path():
            path = filedialog.askdirectory()
            if path:
                save_path_var.set(path)

        def style_button(btn):
            btn.config(relief=tk.RAISED, bd=2, padx=10, pady=5, highlightthickness=0, bg=btn.master.cget('bg'))

        browse_btn = tk.Button(root, text="Browse", command=browse_path)
        style_button(browse_btn)
        browse_btn.pack(pady=5)

        # Progress bar
        progress_bar = ttk.Progressbar(root, length=400, mode='determinate')
        progress_bar.pack(pady=10)

        # Status label
        status_label = tk.Label(root, text="", fg="white")
        status_label.pack(pady=5)

        # Download button
        download_btn = tk.Button(root, text="Download MP3", command=lambda: download_mp3(url_entry, save_path_var, download_btn, progress_bar, status_label, root))
        style_button(download_btn)
        download_btn.pack(pady=20)

        # Allow pressing Enter in the URL field to start the download
        url_entry.bind("<Return>", lambda event: download_mp3(url_entry, save_path_var, download_btn, progress_bar, status_label, root))

        root.mainloop()
    except Exception as e:
        error_msg = f"Fatal Error: {str(e)}"
        messagebox.showerror("Fatal Error", error_msg)

if __name__ == "__main__":
    create_ui()