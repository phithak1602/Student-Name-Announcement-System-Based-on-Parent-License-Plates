import time
import os
from ultralytics import YOLO
from PIL import Image, ImageOps, ImageEnhance
import numpy as np
import random

# === CONFIG ===
MODEL_PATH = r"model/caracter.pt"
AUGMENT = True
RESULTS_FILE = r"txt_file/car_plate.txt"
IMAGE_FOLDER_PATH = r"result_plate"
MAX_INDEX = 20
DELETE_IMAGE = MAX_INDEX - 1

# === CLASS MAPPING ===
CLASS_MAP = {
    '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
    'A01': 'ก', 'A02': 'ข', 'A03': 'ฃ', 'A04': 'ค', 'A05': 'ฅ', 'A06': 'ฆ', 'A07': 'ง',
    'A08': 'จ', 'A09': 'ฉ', 'A10': 'ช', 'A11': 'ซ', 'A12': 'ฌ', 'A13': 'ญ', 'A14': 'ฎ',
    'A15': 'ฏ', 'A16': 'ฐ', 'A17': 'ฑ', 'A18': 'ฒ', 'A19': 'ณ', 'A20': 'ด', 'A21': 'ต',
    'A22': 'ถ', 'A23': 'ท', 'A24': 'ธ', 'A25': 'น', 'A26': 'บ', 'A27': 'ป', 'A28': 'ผ',
    'A29': 'ฝ', 'A30': 'พ', 'A31': 'ฟ', 'A32': 'ภ', 'A33': 'ม', 'A34': 'ย', 'A35': 'ร',
    'A36': 'ล', 'A37': 'ว', 'A38': 'ศ', 'A39': 'ษ', 'A40': 'ส', 'A41': 'ห', 'A42': 'ฬ',
    'A43': 'อ', 'A44': 'ฮ',
    'ACR': 'อำนาจเจริญ', 'ATG': 'อ่างทอง', 'AYA': 'พระนครศรีอยุธยา', 'BKK': 'กรุงเทพมหานคร',
    'BKN': 'บึงกาฬ', 'BRM': 'บุรีรัมย์', 'CBI': 'ชลบุรี', 'CCO': 'ฉะเชิงเทรา',
    'CMI': 'เชียงใหม่', 'CNT': 'ชัยนาท', 'CPM': 'ชัยภูมิ', 'CPN': 'ชุมพร',
    'CRI': 'เชียงราย', 'CTI': 'จันทบุรี', 'KBI': 'กระบี่', 'KKN': 'ขอนแก่น',
    'KPT': 'กำแพงเพชร', 'KRI': 'กาญจนบุรี', 'KSN': 'กาฬสินธุ์', 'LEI': 'เลย',
    'LPG': 'ลำปาง', 'LPN': 'ลำพูน', 'LRI': 'ลพบุรี', 'MDH': 'มุกดาหาร',
    'MKM': 'มหาสารคาม', 'MSN': 'แม่ฮ่องสอน', 'NAN': 'น่าน', 'NBI': 'นนทบุรี',
    'NBP': 'หนองบัวลำภู', 'NKI': 'หนองคาย', 'NMA': 'นครราชสีมา', 'NPM': 'นครพนม',
    'NPT': 'นครปฐม', 'NRT': 'นครศรีธรรมราช', 'NSN': 'นครสวรรค์', 'NWT': 'นราธิวาส',
    'NYK': 'นครนายก', 'PBI': 'เพชรบุรี', 'PCT': 'พิจิตร', 'PKN': 'ประจวบคีรีขันธ์',
    'PKT': 'ภูเก็ต', 'PLG': 'พัทลุง', 'PLK': 'พิษณุโลก', 'PNA': 'พังงา',
    'PNB': 'เพชรบูรณ์', 'PRE': 'แพร่', 'PRI': 'ปราจีนบุรี', 'PTE': 'ปทุมธานี',
    'PTN': 'ปัตตานี', 'PYO': 'พะเยา', 'RBR': 'ราชบุรี', 'RET': 'ร้อยเอ็ด',
    'RNG': 'ระนอง', 'RYG': 'ระยอง', 'SBR': 'สิงห์บุรี', 'SKA': 'สงขลา',
    'SKM': 'สมุทรสงคราม', 'SKN': 'สมุทรสาคร', 'SKW': 'สระแก้ว', 'SNI': 'สุราษฎร์ธานี',
    'SNK': 'สกลนคร', 'SPB': 'สุพรรณบุรี', 'SPK': 'สมุทรปราการ', 'SRI': 'สระบุรี',
    'SRN': 'สุรินทร์', 'SSK': 'ศรีสะเกษ', 'STI': 'สุโขทัย', 'STN': 'สตูล',
    'TAK': 'ตาก', 'TRG': 'ตรัง', 'TRT': 'ตราด', 'UBN': 'อุบลราชธานี',
    'UDN': 'อุดรธานี', 'UTI': 'อุทัยธานี', 'UTT': 'อุตรดิตถ์', 'YLA': 'ยะลา',
    'YST': 'ยโสธร','BTG':'เบตง',
}


# === UTILITIES (คงเดิม) ===
def preprocess_img(img_path, augment=True):
    img = Image.open(img_path)
    img = ImageOps.exif_transpose(img)
    img = img.resize((640, 640))
    if augment:
        brightness_factor = 1.0 + random.uniform(-0.2, 0.2)
        img = ImageEnhance.Brightness(img).enhance(brightness_factor)
        np_img = np.array(img)
        num_noisy_pixels = int(np_img.shape[0] * np_img.shape[1] * 0.0081)
        for _ in range(num_noisy_pixels):
            x = random.randint(0, np_img.shape[0] - 1)
            y = random.randint(0, np_img.shape[1] - 1)
            np_img[x, y] = random.randint(0, 255)
        img = Image.fromarray(np_img)
    return img

def iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    box1_area = (box1[2]-box1[0]) * (box1[3]-box1[1])
    box2_area = (box2[2]-box2[0]) * (box2[3]-box2[1])
    union_area = box1_area + box2_area - inter_area
    return inter_area / union_area if union_area > 0 else 0

def sort_left_right(group):
    return [b['label'] for b in sorted(group, key=lambda x: x['box'][0])]

def process_image(image_path):
    img = preprocess_img(image_path, augment=AUGMENT)
    results = model(img, conf=0.5)
    boxes_with_labels = []
    for box, conf, cls in zip(results[0].boxes.xyxy, results[0].boxes.conf, results[0].boxes.cls):
        box = box.cpu().numpy()
        class_name = model.names[int(cls)]
        label_thai = CLASS_MAP.get(class_name, class_name)
        boxes_with_labels.append({'box': box, 'conf': float(conf), 'label': label_thai, 'label_raw': class_name})

    filtered = []
    for b in boxes_with_labels:
        skip = False
        for f in filtered:
            if b['label'] == f['label'] and iou(b['box'], f['box']) > 0.5:
                if b['conf'] > f['conf']:
                    filtered.remove(f)
                    break
                else:
                    skip = True
                    break
        if not skip:
            filtered.append(b)

    group1 = []
    group2 = []
    for b in filtered:
        label = b['label_raw']
        if label.startswith('A') or label.isdigit():
            group1.append(b)
        else:
            group2.append(b)

    final_labels = sort_left_right(group1) + sort_left_right(group2)
    return ''.join(final_labels)

# === LOAD MODEL ONCE ===
model = YOLO(MODEL_PATH)

# === MAIN LOOP ===
# เปลี่ยนจาก set เป็น dict เพื่อเก็บ timestamp
processed_files = {}  # {filename: modification_time}
idx = 1
i = 1

while True:
    filename = f"plate_{i}.jpg"
    img_path = os.path.join(IMAGE_FOLDER_PATH, filename)

    if not os.path.exists(img_path):
        i += 1
        if i > MAX_INDEX:
            i = 1
        continue

    # ตรวจสอบเวลาที่ไฟล์ถูกแก้ไข
    current_mtime = os.path.getmtime(img_path)
    
    # ตรวจสอบว่าไฟล์นี้ถูกประมวลผลแล้วหรือยัง
    if filename in processed_files and processed_files[filename] == current_mtime:
        i += 1
        if i > MAX_INDEX:
            i = 1
        continue

    try:
        plate_text = process_image(img_path)
        with open(RESULTS_FILE, "a", encoding="utf-8") as f:
            if plate_text:
                print(f"📷 {filename} -> {plate_text}")
                f.write(f"{plate_text}\n")
            else:
                print(f"📷 {filename} ไม่พบป้ายทะเบียน")
                f.write(f"{idx}. ไม่พบป้ายทะเบียน\n")
        
        # บันทึก timestamp ของไฟล์ที่ประมวลผลแล้ว
        processed_files[filename] = current_mtime
        idx += 1
        
    except Exception as e:
        print(f"เกิดข้อผิดพลาดกับ {filename}: {e}")
        with open(RESULTS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{idx}. เกิดข้อผิดพลาด: {e}\n")
        idx += 1

    # ลบไฟล์เมื่อ i == 4
    if i == 19:
        for del_i in range(1, DELETE_IMAGE + 1):
            del_filename = f'plate_{del_i}.jpg'
            del_file_path = os.path.join(IMAGE_FOLDER_PATH, del_filename)
            
            if os.path.exists(del_file_path):
                try:
                    os.remove(del_file_path)
                    print(f'ลบ: {del_filename}')
                    # ลบ timestamp ออกจาก dict ด้วย
                    if del_filename in processed_files:
                        del processed_files[del_filename]
                except Exception as e:
                    print(f'ลบไม่สำเร็จ: {del_filename}, เหตุผล: {e}')
            else:
                print(f'ไม่พบไฟล์: {del_filename}')

    # รีเซต i เมื่อถึง MAX_INDEX
    if i == MAX_INDEX:
        i = 1
        
    i += 1
    time.sleep(2)