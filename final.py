#final

import cv2
from ultralytics import YOLO
import supervision as sv
import numpy as np
import json
import tkinter as tk
from tkinter import messagebox, Entry, Button
from PIL import Image, ImageTk
import qrcode
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import ssl
import sys
import threading
import logging

LINE_START = sv.Point(320, 0)
LINE_END = sv.Point(320, 480)

# Load prices from JSON file
with open("prices.json", "r") as file:
    prices = json.load(file)

# Google Pay UPI ID
upi_id = "sakshisingh3801@okhdfcbank"

# Email credentials
email_sender = 'sakships2223@ascn.sies.edu.in'
email_password = 'Sakshi@1234'

# Setup logging configuration
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='shopping_app.log',
                    filemode='a')

def check_price(name):
    for item in prices:
        if item["name"] == name:
            return item["price"]
    return "Price not available"

def create_upi_payment_link(total_price):
    upi_payment_link = (
        f"upi://pay?pa={upi_id}&pn=Your%20Name&am={total_price}&cu=INR"
    )
    return upi_payment_link

def show_qr(payment_url, email_entry, total_label):
    qr = qrcode.make(payment_url)
    qr.save("payment_qr.png")

    qr_window = tk.Toplevel()
    qr_window.title("Scan QR to Pay")

    qr_img = Image.open("payment_qr.png")
    qr_img_tk = ImageTk.PhotoImage(qr_img)
    qr_label = tk.Label(qr_window, image=qr_img_tk)
    qr_label.image = qr_img_tk
    qr_label.pack()

    # Wait for the QR window to close before sending the email
    qr_window.protocol("WM_DELETE_WINDOW", lambda: on_qr_window_close(qr_window, email_entry, total_label))

def on_qr_window_close(qr_window, email_entry, total_label):
    qr_window.destroy()  # Close the QR window
    send_email_with_invoice(email_entry, total_label)

def send_email_with_invoice(email_entry, total_label):
    global cart
    
    total_price = sum([item["price"] for item in cart])
    logging.info(f"Total Price: {total_price}")

    customer_email = email_entry.get()

    try:
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        pdf.cell(200, 10, txt="Invoice", ln=True, align='C')
        pdf.cell(200, 10, txt="====================", ln=True, align='C')
        
        for item in cart:
            pdf.cell(200, 10, txt=f"{item['name']} : ${item['price']}", ln=True, align='L')
        
        pdf.cell(200, 10, txt="====================", ln=True, align='C')
        pdf.cell(200, 10, txt=f"Total: ${total_price:.2f}", ln=True, align='L')
        
        pdf_filename = "invoice.pdf"
        pdf.output(pdf_filename)

        # Send Email
        msg = MIMEMultipart()
        msg['From'] = email_sender
        msg['To'] = customer_email
        msg['Subject'] = 'Your Invoice'

        with open(pdf_filename, "rb") as f:
            attach = MIMEApplication(f.read(), _subtype="pdf")
            attach.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
            msg.attach(attach)
        
        # Create SSL context
        context = ssl.create_default_context()

        # Send email using SMTP with TLS
        smtp_server = 'smtp.office365.com'
        port = 587
        with smtplib.SMTP(smtp_server, port) as smtp:
            smtp.starttls(context=context)
            smtp.login(email_sender, email_password)
            smtp.send_message(msg)
            logging.info("Email sent successfully")
            messagebox.showinfo("Email Sent", "Invoice email sent successfully!")
        
        # Optionally, update GUI elements after email is sent
        cart.clear()
        update_total_label(total_label)

        # Stop the program after sending the email
        sys.exit()

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        messagebox.showerror("Email Error", f"An error occurred: {str(e)}")


def move_to_payment(root, email_entry, total_label):
    global cart
    
    total_price = sum([item["price"] for item in cart])
    logging.info(f"Total Price: {total_price}")
    
    confirmation = messagebox.askyesno("Payment Confirmation", "Do you want to proceed with the payment?")
    
    if confirmation:
        payment_url = create_upi_payment_link(total_price)
        show_qr(payment_url, email_entry, total_label)
    else:
        messagebox.showinfo("Payment Cancelled", "Payment cancelled.")
    
    # Instead of root.quit(), withdraw the window or hide it
    root.withdraw()  # Hide the root window

# Modify the cart to store items with quantities
# Example structure: cart = [{"name": "Item Name", "price": 10.0, "quantity": 1}, ...]
cart = []

# Function to add an item to the cart or increase its quantity
def add_item_to_cart(item_name, price):
    global cart
    
    # Check if the item is already in the cart
    for item in cart:
        if item["name"] == item_name:
            item["quantity"] += 1
            return
    
    # If not in cart, add new item with quantity 1
    cart.append({"name": item_name, "price": price, "quantity": 1})
    
    # Update the GUI
    update_cart_display()

# Function to remove an item from the cart or decrease its quantity
def remove_item_from_cart(index):
    global cart
    
    if 0 <= index < len(cart):
        if cart[index]["quantity"] > 1:
            cart[index]["quantity"] -= 1
        else:
            cart.pop(index)
        
        # Update the GUI
        update_cart_display()
    else:
        logging.warning("Invalid index to remove from cart")

# Function to update the GUI (listbox and total label)
def update_cart_display():
    listbox.delete(0, tk.END)
    total_price = 0.0
    
    for item in cart:
        item_total = item["price"] * item["quantity"]
        total_price += item_total
        listbox.insert(tk.END, f"{item['name']} : {item['price']} x {item['quantity']} = {item_total:.2f}")
    
    total_label.config(text=f"Total: ₹{total_price:.2f}")

# Modify the main function to integrate quantity management
def main():
    global cart
    detect_more = True  # Flag to indicate whether to continue detecting

    root = tk.Tk()
    root.title("Shopping Cart")
    frame = tk.Frame(root)
    frame.pack()

    label = tk.Label(frame, text="Cart:")
    label.pack()

    listbox = tk.Listbox(frame)
    listbox.pack()

    total_label = tk.Label(frame, text="Total: ₹0.00")
    total_label.pack()

    email_label = tk.Label(frame, text="Enter your Email:")
    email_label.pack()

    email_entry = Entry(frame, width=50)
    email_entry.pack()

    payment_button = tk.Button(frame, text="Proceed to Payment", command=lambda: move_to_payment(root, email_entry, total_label))
    payment_button.pack()

    # Function to handle right-click menu for removing items
    def on_listbox_right_click(event):
        selection_index = listbox.nearest(event.y)
        remove_item_from_cart(selection_index)

    # Bind right-click event to the listbox
    listbox.bind("<Button-3>", on_listbox_right_click)

    line_counter = sv.LineZone(start=LINE_START, end=LINE_END)
    line_annotator = sv.LineZoneAnnotator(thickness=2, text_thickness=1, text_scale=0.5)
    box_annotator = sv.BoxAnnotator(
        thickness=2,
        text_thickness=1,
        text_scale=0.5
    )

    model = YOLO("yolov8l.pt")

    def process_video():
        nonlocal root, frame, listbox, total_label, email_entry
        for result in model.track(source=0, show=False, stream=True, agnostic_nms=True):
            frame = result.orig_img

            # Extracting detections from the result object
            if result.boxes is not None:
                boxes = result.boxes.xyxy.cpu().numpy()
                confidences = result.boxes.conf.cpu().numpy()
                class_ids = result.boxes.cls.cpu().numpy().astype(int)
                tracker_ids = np.arange(len(boxes))  # Assuming no tracker ids, generate unique ids

                detections = sv.Detections(
                    xyxy=boxes,
                    confidence=confidences,
                    class_id=class_ids,
                    tracker_id=tracker_ids
                )

                for i in range(len(boxes)):
                    item_name = model.model.names[class_ids[i]]
                    price = check_price(item_name)
                    if price != "Price not available":
                        add_item_to_cart(item_name, price)
                        logging.info(f"Added to cart: {item_name}")

                detections = detections[(detections.class_id != 60) & (detections.class_id != 0)]
                labels = [
                    f"{tracker_id} {model.model.names[class_id]} {confidence:0.2f} Price: {check_price(model.model.names[class_id])}"
                    for box, confidence, class_id, tracker_id in zip(boxes, confidences, class_ids, tracker_ids)
                ]

                frame = box_annotator.annotate(
                    scene=frame, 
                    detections=detections,
                    labels=labels
                )

                line_counter.trigger(detections=detections)
                line_annotator.annotate(frame=frame, line_counter=line_counter)

                update_cart_display()  # Update the GUI

                # Save the frame to a file instead of using cv2.imshow()
                cv2.imwrite('output.jpg', frame)

                # Display the saved image in the Tkinter window
                img = Image.open('output.jpg')
                img_tk = ImageTk.PhotoImage(img)
                img_label = tk.Label(root, image=img_tk)
                img_label.image = img_tk
                img_label.pack()

                root.update()

    # Run the video processing in a separate thread for responsiveness
    video_thread = threading.Thread(target=process_video)
    video_thread.start()

    root.mainloop()




def update_total_label(label):
    total_price = sum([item["price"] for item in cart])
    label.config(text=f"Total: ₹{total_price:.2f}")

if __name__ == "__main__":
    main()
