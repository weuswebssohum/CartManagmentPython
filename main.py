import cv2
from ultralytics import YOLO
import supervision as sv
import numpy as np
import json
import tkinter as tk
import razorpay

LINE_START = sv.Point(320, 0)
LINE_END = sv.Point(320, 480)

# Load prices from JSON file
with open("prices.json", "r") as file:
    prices = json.load(file)

def check_price(name):
    for item in prices:
        if item["name"] == name:
            return item["price"]
    return "Price not available"

def move_to_payment(root):
    from tkinter import messagebox

    total_price = sum([item["price"] for item in cart])
    print("Total Price:", total_price)
    confirmation = messagebox.askyesno("Payment Confirmation", "Do you want to proceed with the payment?")
    if confirmation:
        messagebox.showinfo("Payment Success", "Payment successful!")
    else:
        messagebox.showinfo("Payment Cancelled", "Payment cancelled.")

    root.quit()

def main():
    global cart
    cart = []
    detect_more = True  # Flag to indicate whether to continue detecting

    root = tk.Tk()
    root.title("Shopping Cart")
    frame = tk.Frame(root)
    frame.pack()

    label = tk.Label(frame, text="Cart:")
    label.pack()

    listbox = tk.Listbox(frame)
    listbox.pack()

    total_label = tk.Label(frame, text="Total: $0.00")
    total_label.pack()

    payment_button = tk.Button(frame, text="Proceed to Payment", command=lambda: move_to_payment(root))
    payment_button.pack()

    line_counter = sv.LineZone(start=LINE_START, end=LINE_END)
    line_annotator = sv.LineZoneAnnotator(thickness=2, text_thickness=1, text_scale=0.5)
    box_annotator = sv.BoxAnnotator(
        thickness=2,
        text_thickness=1,
        text_scale=0.5
    )

    model = YOLO("yolov8l.pt")

    for result in model.track(source=0, show=True, stream=True, agnostic_nms=True):

        # if not detect_more:
        #     break  # Stop processing if flag is False

        frame = result.orig_img
        detections = sv.Detections.from_yolov8(result)


        for _, confidence, class_id, tracker_id in detections:
            item_name = model.model.names[class_id]
            price = check_price(item_name)
            if price != "Price not available":
                if not any(item["name"] == item_name for item in cart):
                    cart.append({"name": item_name, "price": price})
                    print("Added to cart:", item_name)
                    update_total_label(total_label)
                # detect_more = False  # Set flag to False to stop further detection

        detections = detections[(detections.class_id != 60) & (detections.class_id != 0)]
        labels = [
            f"{tracker_id} {model.model.names[class_id]} {confidence:0.2f} Price: {check_price(model.model.names[class_id])}"
            for _, confidence, class_id, tracker_id
            in detections
        ]

        frame = box_annotator.annotate(
            scene=frame, 
            detections=detections,
            labels=labels
        )

        line_counter.trigger(detections=detections)
        line_annotator.annotate(frame=frame, line_counter=line_counter)

        listbox.delete(0, tk.END)
        for item in cart:
            listbox.insert(tk.END, f"{item['name']} : {item['price']}")

        root.update()

    root.mainloop()

def update_total_label(label):
    total_price = sum([item["price"] for item in cart])
    label.config(text=f"Total: ${total_price:.2f}")

if __name__ == "__main__":
    main()