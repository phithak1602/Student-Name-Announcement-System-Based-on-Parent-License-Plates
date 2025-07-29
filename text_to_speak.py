from gtts import gTTS
from pydub import AudioSegment
import subprocess
import time
import os
from datetime import datetime

FILENAME = 'txt_file/names.txt'
LOGFILE = 'txt_file/log.txt'
MAX_LINES = 20
last_index = 0

print("📢 เริ่มตรวจจับไฟล์ names.txt และบันทึก log...")

def get_file_mtime(path):
    try:
        return os.path.getmtime(path)
    except FileNotFoundError:
        return None

while True:
    try:
        # บันทึกเวลาแก้ไขก่อนอ่าน
        before_read_mtime = get_file_mtime(FILENAME)

        with open(FILENAME, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file if line.strip()]

        # บรรทัดใหม่
        if last_index < len(lines):
            new_lines = lines[last_index:]
            for name in new_lines:
                full_text = f"น้อง {name} ผู้ปกครองมารับแล้ว"
                print(f"🔊 กำลังเล่น: {full_text}")

                tts = gTTS(full_text, lang='th')
                mp3_filename = f"voice_{int(time.time())}.mp3"
                tts.save(mp3_filename)

                audio = AudioSegment.from_mp3(mp3_filename)
                duration = len(audio) / 1000.0

                subprocess.Popen(["start", mp3_filename], shell=True)
                time.sleep(duration + 1)
                os.remove(mp3_filename)

                with open(LOGFILE, 'a', encoding='utf-8') as log:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    log.write(f"[{timestamp}] ผู้ปกครองของน้อง {name}\n")

            last_index = len(lines)

        # ตรวจสอบเงื่อนไขรีเซ็ต
        if len(lines) >= MAX_LINES:
            # ตรวจสอบว่าไม่มีการเปลี่ยนแปลงไฟล์ระหว่างอ่าน
            after_read_mtime = get_file_mtime(FILENAME)
            if before_read_mtime == after_read_mtime:
                print(f"⚠️ ครบ {MAX_LINES} บรรทัดแล้ว กำลังรีเซ็ต names.txt")
                with open(FILENAME, 'w', encoding='utf-8') as f:
                    f.write("")
                last_index = 0
            else:
                print("⏳ ตรวจพบการแก้ไขไฟล์ระหว่างเตรียมลบ — ยกเลิกการรีเซ็ตชั่วคราว")

    except FileNotFoundError:
        print("❗ ไม่พบไฟล์ names.txt รอการสร้างใหม่...")

    time.sleep(2)
