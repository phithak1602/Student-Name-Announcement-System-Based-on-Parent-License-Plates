import sys
import cv2
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QFrame, QSpinBox,
                            QGroupBox, QGridLayout, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QLocale
from PyQt5.QtGui import QPixmap

class LineDrawWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QLabel {
                background-color: #3a4a5c;
                border: 2px solid #22c55e;
                border-radius: 12px;
            }
        """)
        self.setText("📹 กำลังรอภาพจากกล้อง...")
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        
        # Line drawing variables
        self.line_start = None
        self.line_end = None
        self.drawing = False
        self.current_frame = None
        self.scaled_frame = None
        self.scale_factor = 1.0
        
    def set_frame(self, frame):
        """Set the current frame and update display"""
        self.current_frame = frame.copy()
        self.update_display()
        
    def update_display(self):
        """Update the display with current frame and line overlay"""
        if self.current_frame is None:
            return
            
        # Scale frame to fit widget
        widget_size = self.size()
        frame_height, frame_width = self.current_frame.shape[:2]
        
        # Calculate scale factor to fit within widget
        scale_x = widget_size.width() / frame_width
        scale_y = widget_size.height() / frame_height
        self.scale_factor = min(scale_x, scale_y)
        
        new_width = int(frame_width * self.scale_factor)
        new_height = int(frame_height * self.scale_factor)
        
        self.scaled_frame = cv2.resize(self.current_frame, (new_width, new_height))
        
        # Draw line on frame if exists
        display_frame = self.scaled_frame.copy()
        if self.line_start and self.line_end:
            cv2.line(display_frame, self.line_start, self.line_end, (0, 255, 255), 3)
            cv2.circle(display_frame, self.line_start, 6, (0, 255, 0), -1)
            cv2.circle(display_frame, self.line_end, 6, (0, 0, 255), -1)
        
        # Convert to QPixmap
        height, width, channel = display_frame.shape
        bytes_per_line = 3 * width
        
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        
        # Create QImage first
        from PyQt5.QtGui import QImage
        q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        
        # Convert QImage to QPixmap
        q_pixmap = QPixmap.fromImage(q_image)
        
        self.setPixmap(q_pixmap)
        
    def get_image_position(self, event):
        """Convert widget coordinates to image coordinates"""
        if self.scaled_frame is None:
            return None
            
        # Get widget size and image size
        widget_size = self.size()
        image_height, image_width = self.scaled_frame.shape[:2]
        
        # Calculate image position within widget (centered)
        x_offset = (widget_size.width() - image_width) // 2
        y_offset = (widget_size.height() - image_height) // 2
        
        # Convert widget coordinates to image coordinates
        image_x = event.x() - x_offset
        image_y = event.y() - y_offset
        
        # Check if click is within image bounds
        if 0 <= image_x < image_width and 0 <= image_y < image_height:
            return (image_x, image_y)
        return None
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.scaled_frame is not None:
            pos = self.get_image_position(event)
            if pos:
                self.drawing = True
                self.line_start = pos
                self.line_end = None
            
    def mouseMoveEvent(self, event):
        if self.drawing and self.scaled_frame is not None:
            pos = self.get_image_position(event)
            if pos:
                self.line_end = pos
                self.update_display()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            pos = self.get_image_position(event)
            if pos:
                self.drawing = False
                self.line_end = pos
                self.update_display()
            
    def get_original_coordinates(self):
        """Get line coordinates in original frame size"""
        if not self.line_start or not self.line_end or self.scale_factor == 0:
            return None, None
            
        start_x = int(self.line_start[0] / self.scale_factor)
        start_y = int(self.line_start[1] / self.scale_factor)
        end_x = int(self.line_end[0] / self.scale_factor)
        end_y = int(self.line_end[1] / self.scale_factor)
        
        return (start_x, start_y), (end_x, end_y)
        
    def clear_line(self):
        """Clear the drawn line"""
        self.line_start = None
        self.line_end = None
        self.update_display()

class LineDetectionGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.python_file = "line_detected_plate.py"  # ไฟล์ Python ที่จะอัพเดทแบบถาวร
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("ระบบตั้งค่าเส้นตรวจจับป้ายทะเบียน")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set dark theme with purple-blue gradient similar to the images
        self.setStyleSheet("""
            QMainWindow {
               background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
            }
            QWidget {
                background-color: #1a1a2e;
                color: #ffffff;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #22c55e, stop:1 #16a34a);
                border: 1px solid #15803d;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                color: white;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #34d399, stop:1 #22c55e);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #16a34a, stop:1 #15803d);
            }
            QPushButton#stopButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ef4444, stop:1 #dc2626);
                border: 1px solid #b91c1c;
            }
            QPushButton#stopButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f87171, stop:1 #ef4444);
            }
            QPushButton#saveButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #3b82f6, stop:1 #2563eb);
                border: 1px solid #1d4ed8;
            }
            QPushButton#saveButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #60a5fa, stop:1 #3b82f6);
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 10px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(51, 65, 85, 0.9), stop:1 rgba(71, 85, 105, 0.9));
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #22c55e;
            }
            QLabel {
                font-size: 12px;
                color: #ffffff;
            }
            QSpinBox {
                background-color: #475569;
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
                color: white;
                min-width: 80px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                width: 20px;
                border-radius: 5px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left side - Video display
        left_layout = QVBoxLayout()
        
        # Title with gradient background like the images
        title_label = QLabel("🎯 ระบบตั้งค่าเส้นที่กำหนดการตรวจจับป้ายทะเบียนรถ")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #ffffff;
            padding: 15px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #667eea, stop:1 #764ba2);
            border-radius: 12px;
            margin-bottom: 10px;
        """)
        left_layout.addWidget(title_label)
        
        # Video display area
        video_group = QGroupBox("📹 ภาพจากกล้อง")
        video_layout = QVBoxLayout(video_group)
        
        self.video_widget = LineDrawWidget()
        video_layout.addWidget(self.video_widget)
        
        instruction_label = QLabel("📌 คำแนะนำ: คลิกและลากเพื่อขีดเส้นตรวจจับ")
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_label.setStyleSheet("color: #fbbf24; font-style: italic; padding: 8px; font-size: 13px;")
        video_layout.addWidget(instruction_label)
        
        left_layout.addWidget(video_group)
        
        # Right side - Controls
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)
        
        # Camera controls
        camera_group = QGroupBox("📷 ควบคุมกล้อง")
        camera_layout = QVBoxLayout(camera_group)
        
        self.start_button = QPushButton("🎬 เชื่อมต่อกล้อง")
        self.start_button.clicked.connect(self.start_camera)
        camera_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⏹️ ปิดกล้อง")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.clicked.connect(self.stop_camera)
        self.stop_button.setEnabled(False)
        camera_layout.addWidget(self.stop_button)
        
        right_layout.addWidget(camera_group)
        
        # Line coordinates display
        coords_group = QGroupBox("📊 พิกัดเส้นตรวจจับ")
        coords_layout = QGridLayout(coords_group)
        
        coords_layout.addWidget(QLabel("จุดเริ่มต้น (X):"), 0, 0)
        self.start_x_spin = QSpinBox()
        self.start_x_spin.setRange(0, 2000)
        self.start_x_spin.setValue(500)
        # ตั้งค่าให้ใช้ตัวเลขอารบิก (0-9)
        self.start_x_spin.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        coords_layout.addWidget(self.start_x_spin, 0, 1)
        
        coords_layout.addWidget(QLabel("จุดเริ่มต้น (Y):"), 1, 0)
        self.start_y_spin = QSpinBox()
        self.start_y_spin.setRange(0, 2000)
        self.start_y_spin.setValue(500)
        # ตั้งค่าให้ใช้ตัวเลขอารบิก (0-9)
        self.start_y_spin.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        coords_layout.addWidget(self.start_y_spin, 1, 1)
        
        coords_layout.addWidget(QLabel("จุดสิ้นสุด (X):"), 2, 0)
        self.end_x_spin = QSpinBox()
        self.end_x_spin.setRange(0, 2000)
        self.end_x_spin.setValue(1000)
        # ตั้งค่าให้ใช้ตัวเลขอารบิก (0-9)
        self.end_x_spin.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        coords_layout.addWidget(self.end_x_spin, 2, 1)
        
        coords_layout.addWidget(QLabel("จุดสิ้นสุด (Y):"), 3, 0)
        self.end_y_spin = QSpinBox()
        self.end_y_spin.setRange(0, 2000)
        self.end_y_spin.setValue(800)
        # ตั้งค่าให้ใช้ตัวเลขอารบิก (0-9)
        self.end_y_spin.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        coords_layout.addWidget(self.end_y_spin, 3, 1)
        
        right_layout.addWidget(coords_group)
        
        # Action buttons
        actions_group = QGroupBox("⚡ จัดการเส้นตรวจจับ")
        actions_layout = QVBoxLayout(actions_group)
        
        self.clear_button = QPushButton("🧹 ลบเส้น")
        self.clear_button.clicked.connect(self.clear_line)
        actions_layout.addWidget(self.clear_button)
        
        self.save_button = QPushButton("💾 บันทึกการตั้งค่า")
        self.save_button.setObjectName("saveButton")
        self.save_button.clicked.connect(self.save_config)
        actions_layout.addWidget(self.save_button)
        
        right_layout.addWidget(actions_group)
        
        # Status info
        status_group = QGroupBox("📋 ข้อมูลสถานะ")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("สถานะ: ไม่ได้เชื่อมต่อกล้อง")
        self.status_label.setStyleSheet("color: #ef4444; font-weight: bold; padding: 5px;")
        status_layout.addWidget(self.status_label)
        
        self.python_file_label = QLabel("ไฟล์ Python: line_detected_plate.py")
        self.python_file_label.setStyleSheet("color: #3b82f6; font-weight: bold; padding: 5px;")
        status_layout.addWidget(self.python_file_label)
        
        self.line_info_label = QLabel("เส้นตรวจจับ: ยังไม่ได้กำหนด")
        self.line_info_label.setStyleSheet("color: #fbbf24; padding: 5px;")
        status_layout.addWidget(self.line_info_label)
        
        right_layout.addWidget(status_group)
        
        # Add stretch to push controls to top
        right_layout.addStretch()
        
        # Add layouts to main layout
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)
        
        # Connect spinbox changes to update display
        self.start_x_spin.valueChanged.connect(self.update_line_from_spinbox)
        self.start_y_spin.valueChanged.connect(self.update_line_from_spinbox)
        self.end_x_spin.valueChanged.connect(self.update_line_from_spinbox)
        self.end_y_spin.valueChanged.connect(self.update_line_from_spinbox)
        
    def start_camera(self):
        # Use the same RTSP URL from the original code
        url = "rtsp://admin:Nice1234@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0"
        self.cap = cv2.VideoCapture(url)
        '''self.cap = cv2.VideoCapture("video_test/video_CCTV_test2.mp4")'''
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if self.cap.isOpened():
            self.timer.start(33)  # ~30 FPS
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("สถานะ: เชื่อมต่อกล้องแล้ว")
            self.status_label.setStyleSheet("color: #22c55e; font-weight: bold; padding: 5px;")
        else:
            QMessageBox.warning(self, "เตือน", "ไม่สามารถเชื่อมต่อกล้องได้")
            
    def stop_camera(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("สถานะ: ไม่ได้เชื่อมต่อกล้อง")
        self.status_label.setStyleSheet("color: #ef4444; font-weight: bold; padding: 5px;")
        
    def update_frame(self):
        if self.cap and self.cap.isOpened():
            # Skip frames like in original code
            for _ in range(3):
                self.cap.read()
            ret, frame = self.cap.read()
            if ret:
                self.video_widget.set_frame(frame)
                
    def update_line_from_spinbox(self):
        start_x = self.start_x_spin.value()
        start_y = self.start_y_spin.value()
        end_x = self.end_x_spin.value()
        end_y = self.end_y_spin.value()
        
        # Convert to widget coordinates if frame is available
        if self.video_widget.current_frame is not None:
            scale = self.video_widget.scale_factor
            self.video_widget.line_start = (int(start_x * scale), int(start_y * scale))
            self.video_widget.line_end = (int(end_x * scale), int(end_y * scale))
            self.video_widget.update_display()
            
        self.update_line_info()
        
    def clear_line(self):
        self.video_widget.clear_line()
        self.line_info_label.setText("เส้นตรวจจับ: ยังไม่ได้กำหนด")
        self.line_info_label.setStyleSheet("color: #fbbf24; padding: 5px;")
        
    def update_line_info(self):
        start_x = self.start_x_spin.value()
        start_y = self.start_y_spin.value()
        end_x = self.end_x_spin.value()
        end_y = self.end_y_spin.value()
        
        self.line_info_label.setText(f"เส้นตรวจจับ: ({start_x},{start_y}) → ({end_x},{end_y})")
        self.line_info_label.setStyleSheet("color: #22c55e; font-weight: bold; padding: 5px;")
        
    def save_config(self):
        # Get coordinates from drawing or spinboxes
        start_coords, end_coords = self.video_widget.get_original_coordinates()
        
        if start_coords and end_coords:
            # Update spinboxes with drawn coordinates
            self.start_x_spin.setValue(start_coords[0])
            self.start_y_spin.setValue(start_coords[1])
            self.end_x_spin.setValue(end_coords[0])
            self.end_y_spin.setValue(end_coords[1])
        
        try:
            # อัพเดทไฟล์ Python โดยตรง
            config = {
                "line_start": (self.start_x_spin.value(), self.start_y_spin.value()),
                "line_end": (self.end_x_spin.value(), self.end_y_spin.value())
            }
            self.update_python_file(config)
            
            QMessageBox.information(self, "สำเร็จ", f"บันทึกการตั้งค่าแล้ว\n✅ ไฟล์ Python: {os.path.basename(self.python_file)}")
            self.update_line_info()
        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", f"ไม่สามารถบันทึกการตั้งค่าได้: {str(e)}")
            
    def update_python_file(self, config):
        """อัพเดทค่าตัวแปรในไฟล์ line_detected_plate.py"""
        
        if not os.path.exists(self.python_file):
            raise FileNotFoundError(f"ไม่พบไฟล์ {self.python_file}")
        
        # อ่านไฟล์ Python
        with open(self.python_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # แทนที่ค่า line_start
        import re
        start_x, start_y = config['line_start']
        start_pattern = r'line_start\s*=\s*\([^)]+\)'
        start_replacement = f'line_start = ({start_x}, {start_y})'
        content = re.sub(start_pattern, start_replacement, content)
        
        # แทนที่ค่า line_end
        end_x, end_y = config['line_end']
        end_pattern = r'line_end\s*=\s*\([^)]+\)'
        end_replacement = f'line_end = ({end_x}, {end_y})'
        content = re.sub(end_pattern, end_replacement, content)
        
        # เขียนไฟล์กลับ
        with open(self.python_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ อัพเดทไฟล์ {self.python_file} เรียบร้อยแล้ว")
        print(f"   line_start = ({start_x}, {start_y})")
        print(f"   line_end = ({end_x}, {end_y})")
            
    def closeEvent(self, event):
        self.stop_camera()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Set application icon and properties
    app.setApplicationName("Line Detection GUI")
    app.setApplicationVersion("1.0")
    
    window = LineDetectionGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()