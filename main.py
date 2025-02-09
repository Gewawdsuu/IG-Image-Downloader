import instaloader
import re
import os
import tkinter as tk
from tkinter import messagebox, filedialog

# Function to extract shortcode from Instagram URL
def get_shortcode(instagram_url):
    match = re.search(r"instagram\.com/p/([^/?]+)", instagram_url)
    return match.group(1) if match else None

# Function to find the next available filename, filling gaps first
def get_next_filename_number(folder, filename_prefix, count):
    existing_files = os.listdir(folder)
    numbers = []

    # Extract all numbers used in filenames
    for file in existing_files:
        if file.startswith(filename_prefix) and file.endswith(".jpg"):
            try:
                num = int(file.replace(filename_prefix + "_", "").replace(".jpg", ""))
                numbers.append(num)
            except ValueError:
                continue

    numbers.sort()  # Ensure numbers are in ascending order
    next_numbers = []

    # Fill missing gaps first
    expected_num = 1
    while len(next_numbers) < count:
        if expected_num not in numbers:
            next_numbers.append(expected_num)
        expected_num += 1

    return next_numbers

# Function to download Instagram post images
def download_instagram_post():
    url = entry_url.get().strip()
    filename_prefix = entry_filename.get().strip()

    if not url:
        messagebox.showerror("Error", "Please enter a valid Instagram post URL!")
        return
    if not filename_prefix:
        messagebox.showerror("Error", "Please enter a filename prefix!")
        return

    shortcode = get_shortcode(url)
    if not shortcode:
        messagebox.showerror("Error", "Invalid Instagram URL format.")
        return

    # Select download folder
    download_folder = filedialog.askdirectory(title="Select Download Folder")
    if not download_folder:
        return  # User canceled selection

    loader = instaloader.Instaloader()

    try:
        post = instaloader.Post.from_shortcode(loader.context, shortcode)

        # Check if post has multiple images (sidecar)
        sidecar_items = list(post.get_sidecar_nodes())  # Get all images in the post

        if sidecar_items:  # If post has multiple images
            next_numbers = get_next_filename_number(download_folder, filename_prefix, len(sidecar_items))

            for item, num in zip(sidecar_items, next_numbers):
                filename = f"{filename_prefix}_{num:02d}"
                img_path = os.path.join(download_folder, filename)
                loader.download_pic(img_path, item.display_url, post.date_utc)

        else:  # Single image post
            next_number = get_next_filename_number(download_folder, filename_prefix, 1)[0]
            filename = f"{filename_prefix}_{next_number:02d}"
            img_path = os.path.join(download_folder, filename)
            loader.download_pic(img_path, post.url, post.date_utc)

        messagebox.showinfo("Success", f"Downloaded images to:\n{download_folder}")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to download post.\nError: {e}")

# Create GUI window
root = tk.Tk()
root.title("Instagram Post Downloader")
root.geometry("400x350")
root.resizable(False, False)

# UI Components
frame = tk.Frame(root, padx=10, pady=10)
frame.pack(expand=True)

label_title = tk.Label(frame, text="Instagram Post Downloader", font=("Arial", 14, "bold"))
label_title.pack(pady=5)

label_url = tk.Label(frame, text="Enter Instagram Post URL:")
label_url.pack()
entry_url = tk.Entry(frame, width=40)
entry_url.pack(pady=5)

label_filename = tk.Label(frame, text="Enter Filename Prefix:")
label_filename.pack()
entry_filename = tk.Entry(frame, width=40)
entry_filename.pack(pady=5)

btn_download = tk.Button(frame, text="Download", command=download_instagram_post, bg="#4CAF50", fg="white")
btn_download.pack(pady=10)

# Run the GUI
root.mainloop()
