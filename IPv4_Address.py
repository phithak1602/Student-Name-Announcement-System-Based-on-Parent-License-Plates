import subprocess, re

def get_wifi_ipv4():
    output = subprocess.check_output("ipconfig", encoding="utf-8")
    match = re.search(r"Wireless LAN adapter Wi-Fi:(.*?)(?:\r\n\r\n|\Z)", output, re.DOTALL)
    if match:
        section = match.group(1)
        ip_match = re.search(r"IPv4 Address[^\d]*([\d\.]+)", section)
        if ip_match:
            return ip_match.group(1)
    return None

ip = get_wifi_ipv4()
print(ip)
if ip:
    with open("txt_file/mqtt_broker_ip.txt", "w") as f:
        f.write(ip)
