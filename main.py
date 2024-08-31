import tkinter as tk
from tkinter import simpledialog, messagebox
import hashlib
import json
from smartcard.System import readers
from smartcard.util import HexListToBinString, toHexString, toBytes

# Initialize global variables
api_endpoint = ""
api_eventName = ""
api_dataCollection = []


# Available hashCID, DOB, CID, FIRSTNAME, LASTNAME, FISTNAME_E, LASTNAME_E

def thai2unicode(data):
    result = bytes(data).decode('tis-620')
    return result.strip()


def getData(connection, cmd, req=[0x00, 0xc0, 0x00, 0x00]):
    data, sw1, sw2 = connection.transmit(cmd)
    data, sw1, sw2 = connection.transmit(req + [cmd[-1]])
    return [data, sw1, sw2]


def check_card():
    try:
        readerList = readers()
        if len(readerList) == 0:
            sub_label1.config(fg="red")
            sub_label1.config(text="No smart card reader detected")
            return None
        reader = readerList[0]
        connection = reader.createConnection()
        connection.connect()
        atr = connection.getATR()
        return connection
    except Exception as e:
        sub_label1.config(fg="red")
        sub_label1.config(text="โปรดเสียบบัตรประจำตัวประชาชนของคุณ")
        return None


def on_enter(event):
    sub_label1_.config(text="")
    input_text = entry.get()
    print(f"Text entered: {input_text}")
    entry.delete(0, tk.END)

    sub_label1.config(fg="yellow")
    sub_label1.config(text="กำลังตรวจสอบ ...")

    root.after(1000)

    readerList = readers()
    have_reader = False
    for readerIndex, readerItem in enumerate(readerList):
        have_reader = True

    if not have_reader:
        sub_label1.config(fg="red")
        sub_label1.config(text="ติดต่อเจ้าหน้าที่ (READER NOT FOUND)")
        return

    connection = None
    error_num = 0
    while connection is None:
        connection = check_card()
        root.after(1000)
        error_num += 1
        if error_num > 10:
            sub_label1.config(fg="red")
            sub_label1.config(text="ไม่พบบัตรประจำตัวประชาชน")
            return
        root.update()

    atr = connection.getATR()
    if (atr[0] == 0x3B & atr[1] == 0x67):
        req = [0x00, 0xc0, 0x00, 0x01]
    else:
        req = [0x00, 0xc0, 0x00, 0x00]

    data, sw1, sw2 = connection.transmit(SELECT + THAI_CARD)
    data = getData(connection, CMD_CID, req)
    cid = thai2unicode(data[0])
    print("CID: " + cid)

    if len(cid) != 13:
        sub_label1.config(fg="red")
        sub_label1.config(text="!!!บัตรชำรุดหรือไม่ใช่บัตรประจำตัวประชาชน!!!")
        return

    sha1_cid = hashlib.sha1(cid.encode()).hexdigest()
    print("SHA1 CID: " + sha1_cid)

    data = getData(connection, CMD_BIRTH, req)
    print("Date of birth: " + thai2unicode(data[0]))

    sub_label1.config(fg="green")
    sub_label1_.config(fg="green")
    sub_label1.config(text="XXXX-0001 - การยืนยันสมบูรณ์!")
    sub_label1_.config(text="โปรดนำบัตรประจำตัวประชาชนออก / เรียนเชิญท่านต่อไป")

    sub_label1.config(fg="red")
    sub_label1_.config(fg="red")
    sub_label1.config(text="บัตรนี้ถูกลงทะเบียนให้กับบัตรเข้าร่วมงานอื่นแล้ว!!!")
    sub_label1_.config(text="โปรดติดต่อสต๊าฟ (XXXX-0001 - XXXX-0002)")


def update_api_settings():
    global api_endpoint, api_eventName, api_dataCollection

    # Create a simple input dialog for JSON data
    json_data = simpledialog.askstring("API Settings", "Enter API settings in JSON format:",
                                       initialvalue='{"api_endpoint": "", "api_eventName": "", "api_dataCollection": []}')

    try:
        settings = json.loads(json_data)
        api_endpoint = settings.get("api_endpoint", "")
        api_eventName = settings.get("api_eventName", "")
        api_dataCollection = settings.get("api_dataCollection", [])
        title_label.config(text=api_eventName+" eCheck-in")

        #back to focus on main screen


#        messagebox.showinfo("Success", "API settings updated successfully!")
    except json.JSONDecodeError:
#        messagebox.showerror("Error", "Invalid JSON format. Please try again.")
        update_api_settings()  # Retry if invalid JSON


# Constants for smart card commands
SELECT = [0x00, 0xA4, 0x04, 0x00, 0x08]
THAI_CARD = [0xA0, 0x00, 0x00, 0x00, 0x54, 0x48, 0x00, 0x01]
CMD_CID = [0x80, 0xb0, 0x00, 0x04, 0x02, 0x00, 0x0d]
CMD_BIRTH = [0x80, 0xb0, 0x00, 0xD9, 0x02, 0x00, 0x08]

# Create the main window
root = tk.Tk()
root.title("eCheck-in")

# Set the window to full-screen mode
root.attributes("-fullscreen", True)

# Add the top label
title_label = tk.Label(root, text="XXXXX eCheck-in", font=("Arial", 48))
title_label.pack(pady=5)

# Add the second label
sub_label = tk.Label(root,
                     text="การลงทะเบียนด้วยตนเองหมายถึงคุณได้ยอมรับในข้อตกลงและเงื่อนไขในการร่วมงานเฟอร์สแควร์และเงื่อนไขความเป็นส่วนตัวของเรา ",
                     font=("Arial", 12))
sub_label.pack(pady=5)
sub_label = tk.Label(root, text="เราจะดำเนินเก็บ เลขเฉพาะ (HASH) และ อายุ โดยจะลบออกเมื่องานสิ้นสุดลง ใน 12 ชั่วโมง",
                     font=("Arial", 12))
sub_label.pack(pady=5)
sub_label = tk.Label(root, text="สแกน QR บัตรเข้าร่วมงานของคุณ", font=("Arial", 24))
sub_label.pack(pady=20)

entry = tk.Entry(root, show="*", font=("Arial", 16), justify='center')
entry.pack(pady=20)

sub_label1 = tk.Label(root, text="... รอ ...", font=("Arial", 48), fg="black")
sub_label1.pack(pady=5)
sub_label1_ = tk.Label(root, text="", font=("Arial", 36), fg="red")
sub_label1_.pack(pady=20)

sub_label1_line = tk.Label(root, text="----------------------------------------", font=("Arial", 24), fg="black")
sub_label1_line.pack(pady=5)
sub_label2 = tk.Label(root, text="FOR NON-THAI CITIZENS, PLEASE CONTACT STAFF", font=("Arial", 30), fg="blue")
sub_label2.pack(pady=5)
sub_label3 = tk.Label(root, text="非泰国公民请联系工作人员 / 非泰國公民請聯絡工作人員", font=("Arial", 24), fg="blue")
sub_label3.pack(pady=5)
sub_label3 = tk.Label(root, text="Công dân không phải người Thái Lan vui lòng liên hệ với nhân viên",
                      font=("Arial", 20), fg="blue")
sub_label3.pack(pady=5)
sub_label3 = tk.Label(root, text="태국 국민이 아닌 경우 직원에게 문의하세요. / Warga negara non-Thailand harap menghubungi staf",
                      font=("Arial", 16), fg="blue")
sub_label3.pack(pady=5)

entry.focus()
entry.bind("<Return>", on_enter)  # Bind the Enter key to the on_enter function

# Show popup to update API settings
update_api_settings()

root.mainloop()
