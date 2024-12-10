import usb.core
import usb.util
import usb.backend.libusb1
import logging
import time
import threading
import tkinter as tk
from tkinter import messagebox
import sys
import os  

#Vendor and product ID of the missile launcher
VENDOR_ID = 0x2123
PRODUCT_ID = 0x1010

# This is my path to the libusb library, you may need to change this, or remove.. who knows, it's a mystery, i needed it atleast
LIBUSB_LIBRARY_PATH = "/opt/homebrew/Cellar/libusb/1.0.27/lib/libusb-1.0.dylib"

backend = usb.backend.libusb1.get_backend(find_library=lambda x: LIBUSB_LIBRARY_PATH)

logging.basicConfig(filename="missile_launcher.log",
                    level=logging.DEBUG,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Starting missile launcher control session")

device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID, backend=backend)

if device is None:
    logging.error("Missile launcher not found. Check USB connection.")
    raise ValueError("Missile launcher not found. Check USB connection.")

try:
    if device.is_kernel_driver_active(0):
        device.detach_kernel_driver(0)
        logging.info("Detached kernel driver successfully.")
except usb.core.USBError as e:
    logging.warning(f"Could not detach kernel driver: {e}")

try:
    device.set_configuration()
    logging.info("Device configuration set.")
except usb.core.USBError as e:
    logging.warning(f"Could not set configuration: {e}")

try:
    usb.util.claim_interface(device, 0)
    logging.info("Interface claimed successfully.")
except usb.core.USBError as e:
    logging.warning(f"Failed to claim interface 0. Proceeding anyway. Error: {e}")

REQUEST_TYPE = 0x21
REQUEST = 0x09      
VALUE = 0x0200       
INDEX = 0x00     

def send_command(cmd):
    try:
        device.ctrl_transfer(REQUEST_TYPE, REQUEST, VALUE, INDEX, cmd)
        logging.info(f"Sent command: {cmd}")
    except usb.core.USBError as e:
        logging.error(f"Error sending command {cmd}. Error: {e}")

ACTION_COMMANDS = {
    'up': 2,      
    'down': 1,     
    'left': 4,    
    'right': 8,    
    'fire': 16,   
    'stop': 0,     
}

class MissileLauncherGUI:
    def __init__(self, master):
        self.master = master
        master.title("Missile Launcher Control")

        self.up_button = tk.Button(master, text="Up", width=10)
        self.up_button.bind('<ButtonPress>', lambda event: self.move_up())
        self.up_button.bind('<ButtonRelease>', lambda event: self.stop_all())

        self.down_button = tk.Button(master, text="Down", width=10)
        self.down_button.bind('<ButtonPress>', lambda event: self.move_down())
        self.down_button.bind('<ButtonRelease>', lambda event: self.stop_all())

        self.left_button = tk.Button(master, text="Left", width=10)
        self.left_button.bind('<ButtonPress>', lambda event: self.move_left())
        self.left_button.bind('<ButtonRelease>', lambda event: self.stop_all())

        self.right_button = tk.Button(master, text="Right", width=10)
        self.right_button.bind('<ButtonPress>', lambda event: self.move_right())
        self.right_button.bind('<ButtonRelease>', lambda event: self.stop_all())

        self.fire_button = tk.Button(master, text="Fire", width=10, command=self.fire_missile)

        self.stop_button = tk.Button(master, text="Stop", width=10, command=self.stop_all)

        self.restart_button = tk.Button(master, text="Restart", width=10, command=self.restart_program)

        self.up_button.grid(row=0, column=1, padx=5, pady=5)
        self.left_button.grid(row=1, column=0, padx=5, pady=5)
        self.stop_button.grid(row=1, column=1, padx=5, pady=5)
        self.right_button.grid(row=1, column=2, padx=5, pady=5)
        self.down_button.grid(row=2, column=1, padx=5, pady=5)
        self.fire_button.grid(row=3, column=1, padx=5, pady=5)
        self.restart_button.grid(row=4, column=1, padx=5, pady=5)  

        master.bind('<KeyPress>', self.key_press)
        master.bind('<KeyRelease>', self.key_release)

    def key_press(self, event):
        if event.keysym == 'w':
            self.move_up()
        elif event.keysym == 's':
            self.move_down()
        elif event.keysym == 'a':
            self.move_left()
        elif event.keysym == 'd':
            self.move_right()
        elif event.keysym == 'space':
            self.fire_missile()

    def key_release(self, event):
        if event.keysym in ['w', 's', 'a', 'd']:
            self.stop_all()

    def move_up(self):
        send_command([2, ACTION_COMMANDS['up'], 0, 0, 0])
        logging.info("Moving up")

    def move_down(self):
        send_command([2, ACTION_COMMANDS['down'], 0, 0, 0])
        logging.info("Moving down")

    def move_left(self):
        send_command([2, ACTION_COMMANDS['left'], 0, 0, 0])
        logging.info("Moving left")

    def move_right(self):
        send_command([2, ACTION_COMMANDS['right'], 0, 0, 0])
        logging.info("Moving right")

    def fire_missile(self):
        threading.Thread(target=self._fire_missile_sequence).start()

    def _fire_missile_sequence(self):

        send_command([2, ACTION_COMMANDS['fire'], 0, 0, 0])

        logging.info("Firing missile command sent")


        logging.info("Stop command sent after firing")
        logging.info("Launcher is ready for next missile")

    def stop_all(self):
        send_command([2, ACTION_COMMANDS['stop'], 0, 0, 0])
        logging.info("Stopping all movement")

    def restart_program(self):
        self.stop_all()
        try:
            usb.util.release_interface(device, 0)
            logging.info("Released interface 0.")
        except usb.core.USBError as e:
            logging.warning(f"Could not release interface: {e}")

        usb.util.dispose_resources(device)
        logging.info("Disposed of USB device resources.")
        self.master.destroy()

        python = sys.executable
        os.execl(python, python, *sys.argv)

    def on_closing(self):
        self.stop_all()
        try:
            usb.util.release_interface(device, 0)
            logging.info("Released interface 0.")
        except usb.core.USBError as e:
            logging.warning(f"Could not release interface: {e}")

        usb.util.dispose_resources(device)
        logging.info("Disposed of USB device resources.")
        self.master.destroy()

def main():
    root = tk.Tk()
    app = MissileLauncherGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
