import os
import logging
from tkinter import Tk, Label, Button, Frame
from PIL import Image, ImageTk, UnidentifiedImageError, ImageDraw

def display_files_side_by_side_gui(file1, file2):
    def on_close():
        logging.debug("Closing the Tkinter window.")
        root.quit()
        root.destroy()

    def on_error():
        logging.debug("Displaying error message for invalid image files.")
        error_label = Label(root, text="Chyba pĹ™i zobrazenĂ­ souborĹŻ", fg="red")
        error_label.grid(row=0, column=0, columnspan=2)
        close_button = Button(root, text="ZavĹ™Ă­t", command=on_close)
        close_button.grid(row=1, column=0, columnspan=2)

    def create_red_cross_image(size):
        img = Image.new('RGB', size, color='white')
        draw = ImageDraw.Draw(img)
        draw.line((0, 0) + img.size, fill='red', width=10)
        draw.line((0, img.size[1], img.size[0], 0), fill='red', width=10)
        return ImageTk.PhotoImage(img)

    def resize_images(event=None):
        logging.debug("Resizing images based on the window size.")
        screen_width = root.winfo_width()
        screen_height = root.winfo_height()
        new_width = screen_width // 2 - 150
        new_height = screen_height - 200

        img1_display = None
        img2_display = None

        try:
            img1 = Image.open(file1)
            img1.verify()  # Verify that it is a valid image
            img1 = Image.open(file1)  # Reopen image after verify
            img1.thumbnail((new_width, new_height))
            img1_display = ImageTk.PhotoImage(img1)
        except (UnidentifiedImageError, IOError) as e:
            logging.error(f"Invalid image file {file1}: {e}")

        try:
            img2 = Image.open(file2)
            img2.verify()  # Verify that it is a valid image
            img2 = Image.open(file2)  # Reopen image after verify
            img2.thumbnail((new_width, new_height))
            img2_display = ImageTk.PhotoImage(img2)
        except (UnidentifiedImageError, IOError) as e:
            logging.error(f"Invalid image file {file2}: {e}")

        if img1_display is None and img2_display is None:
            img1_display = create_red_cross_image((new_width, new_height))
            img2_display = create_red_cross_image((new_width, new_height))
        elif img1_display is None:
            img1_display = create_red_cross_image((img2_display.width(), img2_display.height()))
        elif img2_display is None:
            img2_display = create_red_cross_image((img1_display.width(), img1_display.height()))

        # Calculate dynamic padding to center the images
        total_image_width = 2 * new_width
        remaining_space = screen_width - total_image_width
        side_padding = remaining_space // 4  # Divide by 4 to distribute padding on both sides of both images

        panel1.grid_configure(padx=side_padding, pady=10)
        panel2.grid_configure(padx=side_padding, pady=10)

        panel1.config(image=img1_display)
        panel1.image = img1_display  # Keep a reference to avoid garbage collection
        panel2.config(image=img2_display)
        panel2.image = img2_display  # Keep a reference to avoid garbage collection

    root = Tk()
    root.title("Porovnat soubory")

    # Get initial screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Create a frame for images
    image_frame = Frame(root)
    image_frame.grid(row=0, column=0, columnspan=2, padx=30, pady=30)

    label1 = Label(image_frame, text=f"NeroztĹ™Ă­dÄ›nĂ˝ soubor: {file1}", wraplength=screen_width // 2 - 150)
    label1.grid(row=0, column=0, padx=10, pady=10)
    panel1 = Label(image_frame)
    panel1.grid(row=1, column=0, padx=10, pady=10)

    label2 = Label(image_frame, text=f"CĂ­lovĂ˝ soubor: {file2}", wraplength=screen_width // 2 - 150)
    label2.grid(row=0, column=1, padx=10, pady=10)
    panel2 = Label(image_frame)
    panel2.grid(row=1, column=1, padx=10, pady=10)

    # Create a frame for question and buttons
    question_frame = Frame(root)
    question_frame.grid(row=2, column=0, columnspan=2, pady=20)

    question_label = Label(question_frame, text="Chcete nahradit neroztĹ™Ă­dÄ›nĂ˝ soubor cĂ­lovĂ˝m souborem?", font=("Helvetica", 14))
    question_label.grid(row=0, column=0, columnspan=2, pady=10)

    def on_yes():
        logging.debug("Yes button clicked.")
        root.result = 'y'
        on_close()

    def on_no():
        logging.debug("No button clicked.")
        root.result = 'n'
        on_close()

    yes_button = Button(question_frame, text="Ano", command=on_yes, width=20, height=2)
    yes_button.grid(row=1, column=0, padx=20, pady=20)

    no_button = Button(question_frame, text="Ne", command=on_no, width=20, height=2)
    no_button.grid(row=1, column=1, padx=20, pady=20)

    root.geometry(f"{screen_width - 300}x{screen_height - 50}")

    root.bind("<Configure>", resize_images)  # Bind resize event to function

    root.mainloop()

    logging.debug(f"User selected: {root.result}")
    return root.result
