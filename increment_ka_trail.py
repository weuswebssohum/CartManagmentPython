import cv2
from ultralytics import YOLO
import supervision as sv
import numpy as np
import json
import tkinter as tk
from tkinter import messagebox, Entry, Button, Label, Frame, Listbox, Scrollbar
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
    
    total_price = sum(item["price"] * item["quantity"] for item in cart)

    customer_email = email_entry.get()

    try:
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        pdf.cell(200, 10, txt="Invoice", ln=True, align='C')
        pdf.cell(200, 10, txt="====================", ln=True, align='C')
        
        for item in cart:
            pdf.cell(200, 10, txt=f"{item['name']} : ${item['price']} x {item['quantity']} = ${item['price'] * item['quantity']:.2f}", ln=True, align='L')
        
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
            messagebox.showinfo("Email Sent", "Invoice email sent successfully!")
        
        # Optionally, update GUI elements after email is sent
        cart.clear()
        update_total_label(total_label)

    except Exception as e:
        messagebox.showerror("Email Error", f"An error occurred: {str(e)}")

def increase_quantity(item_name, listbox, total_label):
    global cart
    for item in cart:
        if item["name"] == item_name:
            item["quantity"] += 1
            update_cart_listbox(listbox)
            update_total_label(total_label)
            break

def decrease_quantity(item_name, listbox, total_label):
    global cart
    for item in cart:
        if item["name"] == item_name:
            if item["quantity"] > 1:
                item["quantity"] -= 1
            update_cart_listbox(listbox)
            update_total_label(total_label)
            break

def move_to_payment(root, email_entry, total_label, cart_listbox):
    global cart
    
    total_price = sum(item["price"] * item["quantity"] for item in cart)
    
    confirmation = messagebox.askyesno("Payment Confirmation", "Do you want to proceed with the payment?")
    
    if confirmation:
        payment_url = create_upi_payment_link(total_price)
        show_qr(payment_url, email_entry, total_label)
    else:
        messagebox.showinfo("Payment Cancelled", "Payment cancelled.")
    
    # Instead of root.quit(), withdraw the window or hide it
    root.withdraw()  # Hide the root window

def main():
    global cart
    cart = []
    detect_more = True  # Flag to indicate whether to continue detecting

    root = tk.Tk()
    root.title("Shopping Cart")
    frame = Frame(root)
    frame.pack()

    label = Label(frame, text="Cart:")
    label.pack()

    listbox_frame = Frame(frame)
    listbox_frame.pack()

    listbox = Listbox(listbox_frame)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = Scrollbar(listbox_frame, orient=tk.VERTICAL)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    scrollbar.config(command=listbox.yview)

    total_label = Label(frame, text="Total: ₹0.00")
    total_label.pack()

    email_label = Label(frame, text="Enter your Email:")
    email_label.pack()

    email_entry = Entry(frame, width=50)
    email_entry.pack()

    payment_button = Button(frame, text="Proceed to Payment", command=lambda: move_to_payment(root, email_entry, total_label, listbox))
    payment_button.pack()

    def add_to_cart(item_name):
        nonlocal listbox, total_label
        price = check_price(item_name)
        if price != "Price not available":
            for item in cart:
                if item["name"] == item_name:
                    item["quantity"] += 1
                    update_cart_listbox(listbox)
                    update_total_label(total_label)
                    return
            cart.append({"name": item_name, "price": price, "quantity": 1})
            update_cart_listbox(listbox)
            update_total_label(total_label)

    def update_cart_listbox(listbox):
        listbox.delete(0, tk.END)
        for item in cart:
            listbox.insert(tk.END, f"{item['name']} : {item['price']} x {item['quantity']}")

    def create_buttons_for_item(item_name):
        item_frame = Frame(listbox)
        item_frame.pack(fill=tk.X)

        label = Label(item_frame, text=f"{item_name}:")
        label.pack(side=tk.LEFT, padx=5)

        decrease_button = Button(item_frame, text="-", command=lambda: decrease_quantity(item_name, listbox, total_label))
        decrease_button.pack(side=tk.LEFT, padx=5)

        quantity_label = Label(item_frame, text="1")
        quantity_label.pack(side=tk.LEFT, padx=5)

        increase_button = Button(item_frame, text="+", command=lambda: increase_quantity(item_name, listbox, total_label))
        increase_button.pack(side=tk.LEFT, padx=5)

    line_counter = sv.LineZone(start=LINE_START, end=LINE_END)
    line_annotator = sv.LineZoneAnnotator(thickness=2, text_thickness=1, text_scale=0.5)
    box_annotator = sv.BoxAnnotator(
        thickness=2,
        text_thickness=1,
        text_scale=0.5
    )

    model = YOLO("yolov8l.pt")

    def process_video():
        nonlocal root
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
                        if not any(item["name"] == item_name for item in cart):
                            cart.append({"name": item_name, "price": price, "quantity": 1})
                            logging.info(f"Added to cart: {item_name}")
                            create_buttons_for_item(item_name)

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

                update_cart_listbox(listbox)

                # Save the frame to a file instead of using cv2.imshow()
                cv2.imwrite('output.jpg', frame)

                # Display the saved image in the Tkinter window
                img = Image.open('output.jpg')
                img_tk = ImageTk.PhotoImage(img)
                img_label = Label(root, image=img_tk)
                img_label.image = img_tk
                img_label.pack()

                root.update()

    threading.Thread(target=process_video, daemon=True).start()

    root.mainloop()

def update_total_label(label):
    global cart
    total_price = sum(item["price"] * item["quantity"] for item in cart)
    label.config(text=f"Total: ₹{total_price:.2f}")

if __name__ == "__main__":
    main()
