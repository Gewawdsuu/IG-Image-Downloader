import instaloader
import re
import os
import requests
from io import BytesIO
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox, filedialog, ttk

# Function to extract shortcode from Instagram URL
def get_shortcode(instagram_url):
    match = re.search(r"instagram\.com/p/([^/?]+)", instagram_url.split('?')[0])
    return match.group(1) if match else None

# Function to fetch Instagram post images
def fetch_images():
    global image_urls, checkboxes, image_vars
    
    url = entry_url.get().strip()
    if not url:
        messagebox.showerror("Error", "Please enter a valid Instagram post URL!")
        return
    
    shortcode = get_shortcode(url)
    if not shortcode:
        messagebox.showerror("Error", "Invalid Instagram URL format.")
        return
    
    loader = instaloader.Instaloader()
    
    try:
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        image_urls = [post.url]  # Default to single-image post
        
        sidecar_items = list(post.get_sidecar_nodes())
        if sidecar_items:
            image_urls = [item.display_url for item in sidecar_items]
        
        # Clear previous checkboxes
        for widget in preview_canvas.winfo_children():
            widget.destroy()
        checkboxes.clear()
        image_vars.clear()
        
        for i, img_url in enumerate(image_urls):
            response = requests.get(img_url)
            img_data = Image.open(BytesIO(response.content))
            img_data.thumbnail((150, 150))  # Resize for preview
            img = ImageTk.PhotoImage(img_data)
            
            row, col = divmod(i, 4)
            
            frame = tk.Frame(preview_canvas)
            frame.grid(row=row, column=col, padx=5, pady=5)
            
            var = tk.BooleanVar()
            
            def toggle_checkbox(var=var):
                var.set(not var.get())
            
            img_label = tk.Label(frame, image=img)
            img_label.image = img  # Keep a reference
            img_label.pack()
            img_label.bind("<Button-1>", lambda e, var=var: toggle_checkbox(var))
            
            checkbox = tk.Checkbutton(frame, variable=var)
            checkbox.pack()
            
            checkboxes.append(checkbox)
            image_vars.append(var)
        
        # Adjust scroll region
        preview_canvas.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
    
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch images: {str(e)}")
        return

# Function to download selected images
def download_selected_images():
    filename_prefix = entry_filename.get().strip()
    if not filename_prefix:
        messagebox.showerror("Error", "Please enter a filename prefix!")
        return
    
    download_folder = filedialog.askdirectory(title="Select Download Folder")
    if not download_folder:
        return  # User canceled selection
    
    selected_urls = [img_url for img_url, var in zip(image_urls, image_vars) if var.get()]
    if not selected_urls:
        messagebox.showerror("Error", "No images selected!")
        return
    
    existing_files = [f for f in os.listdir(download_folder) if f.startswith(filename_prefix) and f.endswith(".jpg")]
    existing_numbers = sorted([int(re.search(r"_(\d+).jpg", f).group(1)) for f in existing_files if re.search(r"_(\d+).jpg", f)])
    
    next_numbers = []
    expected_num = 1
    for _ in range(len(selected_urls)):
        while expected_num in existing_numbers:
            expected_num += 1
        next_numbers.append(expected_num)
        expected_num += 1
    
    for img_url, num in zip(selected_urls, next_numbers):
        response = requests.get(img_url)
        img_path = os.path.join(download_folder, f"{filename_prefix}_{num:02d}.jpg")
        with open(img_path, "wb") as file:
            file.write(response.content)
    
    messagebox.showinfo("Success", f"Downloaded {len(selected_urls)} images to {download_folder}")

# GUI Setup
root = tk.Tk()
root.title("Instagram Image Selector")
root.geometry("600x700")
root.iconbitmap(os.path.abspath("app.ico"))  # Set application icon

# Center the window on the screen
def center_window():
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

root.after(100, center_window)  # Ensure it centers after UI elements load

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(expand=True, fill="both")

tk.Label(frame, text="Enter Instagram Post URL:").pack()
entry_url = tk.Entry(frame, width=50)
entry_url.pack(pady=5)

tk.Button(frame, text="Fetch Images", command=fetch_images).pack(pady=5)

tk.Label(frame, text="Enter Filename Prefix:").pack()
entry_filename = tk.Entry(frame, width=50)
entry_filename.pack(pady=10)  # Increased spacing

tk.Frame(frame, height=2, bg="black").pack(fill="x", pady=10)  # Line separator

# Scrollable Preview Area
preview_container = tk.Frame(frame)
preview_container.pack(expand=True, fill="both")
canvas = tk.Canvas(preview_container)
scrollbar = tk.Scrollbar(preview_container, orient="vertical", command=canvas.yview)
preview_canvas = tk.Frame(canvas)

preview_canvas.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=preview_canvas, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

tk.Button(frame, text="Download Selected Images", command=download_selected_images, bg="#4CAF50", fg="white").pack(pady=10)

checkboxes = []
image_vars = []
image_urls = []

root.mainloop()
