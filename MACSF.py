import sys
import threading
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLineEdit, QLabel
from PyQt5.QtGui import QIcon
from scapy.all import ARP, Ether, get_if_hwaddr, srp
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class MACSF(QWidget):
    # Create the GUI
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MACSF")
        self.setWindowIcon(QIcon("C:/Users/USER/Documents/Python Scripts/network_testing/web.jpg"))
        self.setStyleSheet("background-color:grey")
        self.layout = QVBoxLayout()

        # Create a label for the Available Mac Addresses
        available_mac_label = QLabel("Available MAC")
        available_mac_label.setStyleSheet("font-size: 18px;color:orange;border:none;") 
        self.layout.addWidget(available_mac_label)

        # Create a text area for the Available Mac Addresses
        self.list_widget = QListWidget()
        self.list_widget.setMaximumHeight(100)
        self.list_widget.setStyleSheet("border:1px solid black;border-radius:5px;color:orange")
        self.layout.addWidget(self.list_widget)

         # Create a label for the description 
        description_label = QLabel("Description")
        description_label.setStyleSheet("font-size: 18px;color:orange;")
        self.layout.addWidget(description_label)
        # Create an input for the description
        self.description_input = QLineEdit()
        self.description_input.setStyleSheet("border:1px solid black;border-radius:5px;color:orange;")
        self.layout.addWidget(self.description_input)

        # Create a label for the Banned Mac Addresses
        banned_mac_label = QLabel("Banned MAC")
        banned_mac_label.setStyleSheet("font-size: 18px;color:orange;")  
        self.layout.addWidget(banned_mac_label)

        # Create a input for the Banned Mac Addresses(read-only)
        self.banned_mac_input = QLineEdit()
        self.banned_mac_input.setReadOnly(True)
        self.banned_mac_input.setStyleSheet("border:1px solid black;border-radius:5px;color:orange")
        self.banned_mac_input.setMaximumHeight(60)
        self.layout.addWidget(self.banned_mac_input)

        #Create timer for scaning
        self.timer_label = QLabel()
        self.timer_label.setStyleSheet("font-size: 14px; color: red;") 
        self.layout.addWidget(self.timer_label)
        #Create button Add
        button_layout = QHBoxLayout()  
        self.button_add = QPushButton("Add")
        self.button_add.setStyleSheet("color: orange; font-size: 16px; background-color: black; border: none; border-radius: 5px;padding-bottom:6px;")
        self.button_add.setMaximumHeight(40) 
        self.button_add.setMaximumWidth(100)
        self.button_add.clicked.connect(self.add_selected_mac)
        button_layout.addWidget(self.button_add)
        #Create button Delete
        self.button_delete = QPushButton("Delete")
        self.button_delete.setStyleSheet("color: orange; font-size: 16px; background-color: black; border: none; border-radius: 5px;padding-bottom:6px;") 
        self.button_delete.setMaximumHeight(40) 
        self.button_delete.setMaximumWidth(100)  
        self.button_delete.clicked.connect(self.delete_selected_mac)
        button_layout.addWidget(self.button_delete)

        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)

        self.selected_macs = []
        self.scan_timeout = 10  # Timeout for scanning in seconds

        self.driver = None  # WebDriver instance
    #function for scaning mac address
    def scan_mac_addresses(self):
        target_ip = "192.168.7.0/24"
        host_mac = get_if_hwaddr('Wi-Fi')  
        arp = ARP(pdst=target_ip)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether / arp
        result = srp(packet, timeout=self.scan_timeout, verbose=0)[0]
        active_devices = [received.hwsrc.upper() for sent, received in result if received.hwsrc != host_mac]
        return active_devices
    #update the mac address list with the scanned mac addresses
    def update_mac_list(self):
        active_devices = self.scan_mac_addresses()
        self.list_widget.clear()
        self.list_widget.addItems(active_devices)
        #when mac address in the mac list is double clicked it will be selected
        self.list_widget.itemDoubleClicked.connect(self.add_selected_mac)
    #add function when pressed add in the gui perform automation to add the selected mac address
    def add_selected_mac(self):
     selected_items = self.list_widget.selectedItems()
     for item in selected_items:
        selected_mac = item.text()
        if selected_mac not in self.selected_macs:
            self.selected_macs.append(selected_mac.upper())
            self.update_selected_mac_input()

            
            try:
                
                add_element = self.driver.find_element(By.CSS_SELECTOR, "div.table-add")
                add_element.click()

                time.sleep(2)

                try:
                    #add the mac address in its input place
                    model_element = self.driver.find_element(By.CSS_SELECTOR, "div.modal-content")
                    input_list = model_element.find_elements(By.CSS_SELECTOR, "input[type='text']")
                    MAC_input = input_list[0]
                    MAC_input.send_keys(selected_mac)
                except NoSuchElementException:
                    print("MAC address elements not found.")

                try:
                    #add the description of the mac address in its input
                    description_input = input_list[1]
                    description_input.send_keys(self.description_input.text())
                except NoSuchElementException:
                    print("Description input element not found.")

                try:
                    #press confirm button after adding the corresponding inputs
                    confirm_button = self.driver.find_element(By.XPATH, "//button[text()='Confirm']")
                    confirm_button.click()
                    time.sleep(2)


                    
                    self.description_input.setText("")
                except NoSuchElementException:
                    print("Confirm button not found.")
            except NoSuchElementException:
                print("Add button not found.")


    def delete_selected_mac(self):
        #select the mac address from the available mac addresses then delet it from the banned mac address input  
        selected_item = self.list_widget.currentItem()
        if selected_item is not None:
            selected_mac = selected_item.text()
            if selected_mac in self.selected_macs:
                self.selected_macs.remove(selected_mac)
                self.update_selected_mac_input()
        try:
            #find the mac address in the mac address table and delete it
            tbody = self.driver.find_element(By.CSS_SELECTOR, "tbody.tbody")
            rows = tbody.find_elements(By.TAG_NAME, "tr")

            for row in rows:
                td_elements = row.find_elements(By.TAG_NAME, "td")
                if len(td_elements) >= 3:
                    if td_elements[0].text == selected_mac:
                        delete_button = td_elements[2].find_element(By.CSS_SELECTOR, "button[type='danger']")
                        delete_button.click()
                        time.sleep(2)
        except NoSuchElementException:
            print("Delete button not found.")

    def update_selected_mac_input(self):
        self.banned_mac_input.setText("\n".join(self.selected_macs))

    def update_timer(self):
        #update timer for scanning to appear on the GUI
        self.timer_label.setText(f"Scanning: {self.scan_timeout} seconds")
        self.scan_timeout -= 1
        if self.scan_timeout >= 0:
            #to recall the function(update_timer every one second)to be executed asynchronously with updat_timer
            threading.Timer(1, self.update_timer).start()
    #start the scan 
    def start_scanning(self):
        self.update_mac_list()
        self.update_timer()
    #close the driver
    def closeEvent(self, event):
        self.driver.quit()
        event.accept()
#function responsible for the automation till the mac address table filter
def automate_login_and_navigation(window):
    options = Options()

    #download the chrome driver for 24 hours
    window.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

  
    window.driver.get("http://192.168.7.1/")

    window.driver.implicitly_wait(10)
    #enters the passsword for the website to enter the router configuration page
    password_input = window.driver.find_element(By.CSS_SELECTOR, "div.login-form input[type='password']")
    password_input.send_keys("admin")

    time.sleep(2)

    login_button = window.driver.find_element(By.CSS_SELECTOR, "div.login-form button.login-btn")
    login_button.click()

    time.sleep(2)
    #search for the advanced button
    buttons = window.driver.find_elements(By.CSS_SELECTOR, "div.bar-button button")

    for button in buttons:
        if button.text == "Advanced":
            button.click()
            break

    time.sleep(3)
    #click the Advanced element in the nav bar
    target_element = window.driver.find_element(By.CSS_SELECTOR, "a.m-menu__link.o-nav__link[index='4']")
    target_element.click()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    #open the GUI
    window = MACSF()
    window.show()
    #starts a thread for the navigation
    threading.Thread(target=automate_login_and_navigation, args=(window,)).start()
    #start the scaning 
    window.start_scanning()
    #when press exit in the GUI it exit and shut the system all down
    sys.exit(app.exec_())

