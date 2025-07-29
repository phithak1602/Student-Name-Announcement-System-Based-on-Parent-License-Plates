import paho.mqtt.client as mqtt

# อ่าน IP จากไฟล์
with open("txt_file/mqtt_broker_ip.txt", "r") as f:
    MQTT_BROKER = f.read().strip()
#MQTT_BROKER = "192.168.1.103"  # เปลี่ยนจาก "localhost" เป็น IP ที่ใช้จริง
MQTT_PORT = 1883
TOPIC_COMMANDS = "esp8266/commands"
TOPIC_FEEDBACK = "esp8266/feedback"

sensor_status = 0
servo_set = 0
last_delay_value = None  # จำค่าล่าสุด

# ฟังก์ชันเมื่อเชื่อมต่อ MQTT สำเร็จ
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("เชื่อมต่อ MQTT สำเร็จ")
        client.subscribe(TOPIC_COMMANDS)
    else:
        print("เชื่อมต่อ MQTT ล้มเหลว, รหัส:", rc)

# ฟังก์ชันเมื่อมีข้อความเข้ามา
def on_message(client, userdata, message):
    command = message.payload.decode()
    
    if command == "start":
        print(f"📥 Received MQTT command: {command}")
        sensor_status = 1
        with open('txt_file/sensor_state.txt', 'w') as f:
            f.write(str(sensor_status))
        print(f"sensor_status: {sensor_status}")
        
    elif command == "stop":
        print(f"📥 Received MQTT command: {command}")
        sensor_status = 0
        with open('txt_file/sensor_state.txt', 'w') as f:
            f.write(str(sensor_status))
        print(f"sensor_status: {sensor_status}")
    
    else:
        print(f"📥 Unknown command: {command}")

# ฟังก์ชันสำหรับส่ง feedback กลับไปยัง ESP32
def send_feedback(message):
    client.publish(TOPIC_FEEDBACK, message)
    print(f"📤 Sent feedback: {message}")

def read_servo_set():
    try:
        with open('txt_file/servo_state.txt', 'r') as f:
            value = f.read().strip()
            return int(value)
    except (FileNotFoundError, ValueError):
        return 0  # ค่า default ถ้าไม่มีไฟล์หรือไฟล์ผิดพลาด

def read_delay_servo():
    try:
        with open('txt_file/delay_servo.txt', 'r') as f:
            value = f.read().strip()
            return int(value)
    except (FileNotFoundError, ValueError):
        return 3000  # default ถ้าไม่มีไฟล์หรือไฟล์ผิดพลาด

# ฟังก์ชันเริ่มต้น MQTT
def start_mqtt():
    global client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

# === เริ่มการเชื่อมต่อ MQTT ===
start_mqtt()

# ทำให้รันต่อเนื่อง
try:
    while True:
        # อ่าน delay ปัจจุบันจากไฟล์
        current_delay_value = read_delay_servo()

        # ถ้า delay เปลี่ยน → ค่อยส่ง
        if current_delay_value != last_delay_value:
            send_feedback(f"delay={current_delay_value}")
            print(f"📤 delay_servo changed → {current_delay_value} ms")
            last_delay_value = current_delay_value  # อัปเดตค่าล่าสุด

        servo_set = read_servo_set()
        if servo_set == 1:
            send_feedback("open")
            print("send_feedback'open'")
            servo_set = 0
            with open('txt_file/servo_state.txt', 'w') as f:
                f.write(str(servo_set))
        pass
except KeyboardInterrupt:
    print("หยุดโปรแกรม")
    client.loop_stop()
    client.disconnect()