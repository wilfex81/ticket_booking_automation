import sys
import webbrowser
import requests
import random
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QTimer, QDateTime, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QComboBox, QDateTimeEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QProgressBar, QMessageBox

from helpers import load_sites, save_sites

class KBOTicketAccessApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load sites from JSON file
        self.ticket_sites = load_sites()
  
        # Configuration
        if not self.ticket_sites:
            self.ticket_sites = {
                "인터파크 (Interpark)": "https://ticket.interpark.com/",
                "티켓링크 (Ticketlink)": "https://www.ticketlink.co.kr/home/",
                "예스24 (Yes24)": "https://ticket.yes24.com/Sports/"
            }
            save_sites(self.ticket_sites)
        
        self.access_interval = 0.5  # seconds between access attempts
        self.is_running = False
        self.success = False
        self.is_maximized = False
        
        # UI Setup
        self.setWindowTitle("KBO 티켓 예매 접속 프로그램")
        self.setMinimumSize(500, 400)
        self.setup_ui()
        
        # Timer for clock update
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_current_time)
        self.clock_timer.start(1000)
        
        # Timer for access attempts
        self.access_timer = QTimer(self)
        self.access_timer.timeout.connect(self.attempt_access)
        
        # Initial time update
        self.update_current_time()
    
    def setup_ui(self):
        self.site_combo = QComboBox()
        for site in self.ticket_sites.keys():
            self.site_combo.addItem(site)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title
        title_label = QLabel("KBO 티켓 예매 접속 프로그램 (KBO Ticket Booking Access Program)")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QtGui.QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Site selection
        site_layout = QHBoxLayout()
        site_label = QLabel("예매 사이트 (Booking Site):")
        site_label.setFixedWidth(150)
        self.site_combo = QComboBox()
        for site in self.ticket_sites.keys():
            self.site_combo.addItem(site)
        site_layout.addWidget(site_label)
        site_layout.addWidget(self.site_combo)
        main_layout.addLayout(site_layout)
        
        # Custom site entry
        custom_site_layout = QVBoxLayout()
        custom_site_header = QLabel("사이트 관리")
        custom_site_header.setFont(QtGui.QFont("", 10, QtGui.QFont.Bold))
        custom_site_layout.addWidget(custom_site_header)
        
        site_name_layout = QHBoxLayout()
        site_name_label = QLabel("사이트 이름:")
        site_name_label.setFixedWidth(150)
        self.site_name_input = QtWidgets.QLineEdit()
        site_name_layout.addWidget(site_name_label)
        site_name_layout.addWidget(self.site_name_input)
        custom_site_layout.addLayout(site_name_layout)
        
        site_url_layout = QHBoxLayout()
        site_url_label = QLabel("사이트 URL:")
        site_url_label.setFixedWidth(150)
        self.site_url_input = QtWidgets.QLineEdit()
        self.site_url_input.setPlaceholderText("https://")
        site_url_layout.addWidget(site_url_label)
        site_url_layout.addWidget(self.site_url_input)
        custom_site_layout.addLayout(site_url_layout)
        
        site_buttons_layout = QHBoxLayout()
        self.add_site_button = QPushButton("추가")
        self.add_site_button.clicked.connect(self.add_custom_site)
        self.remove_site_button = QPushButton("삭제")
        self.remove_site_button.clicked.connect(self.remove_custom_site)
        self.remove_site_button.setStyleSheet("background-color: #f44336;")
        site_buttons_layout.addWidget(self.add_site_button)
        site_buttons_layout.addWidget(self.remove_site_button)
        custom_site_layout.addLayout(site_buttons_layout)
        
        main_layout.addLayout(custom_site_layout)   
        
        # Target time selection
        time_layout = QHBoxLayout()
        time_label = QLabel("예매 시작 시간:")
        time_label.setFixedWidth(150)
        self.time_edit = QDateTimeEdit()
        self.time_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.time_edit.setDateTime(QDateTime.currentDateTime().addSecs(60))
        self.time_edit.setCalendarPopup(True)
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_edit)
        main_layout.addLayout(time_layout)
        
        # Current time display
        current_time_layout = QHBoxLayout()
        current_time_label = QLabel("현재 시간:")
        current_time_label.setFixedWidth(150)
        self.current_time_display = QLabel()
        current_time_layout.addWidget(current_time_label)
        current_time_layout.addWidget(self.current_time_display)
        main_layout.addLayout(current_time_layout)
        
        # Time remaining
        remaining_layout = QHBoxLayout()
        remaining_label = QLabel("남은 시간:")
        remaining_label.setFixedWidth(150)
        self.remaining_display = QLabel()
        remaining_layout.addWidget(remaining_label)
        remaining_layout.addWidget(self.remaining_display)
        main_layout.addLayout(remaining_layout)
        
        # Status
        status_layout = QHBoxLayout()
        status_label = QLabel("상태:")
        status_label.setFixedWidth(150)
        self.status_display = QLabel("대기 중")
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_display)
        main_layout.addLayout(status_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("시작")
        self.start_button.clicked.connect(self.start_access)
        self.stop_button = QPushButton("중지")
        self.stop_button.clicked.connect(self.stop_access)
        self.stop_button.setEnabled(False)
        
        # Maximize button
        self.maximize_button = QPushButton("전체 화면")
        self.maximize_button.clicked.connect(self.toggle_maximize)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.maximize_button)
        main_layout.addLayout(button_layout)
        
        # Set some styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                font-size: 12px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)

    def toggle_maximize(self):
        if self.is_maximized:
            self.showNormal()
            self.maximize_button.setText("전체 화면")
            self.is_maximized = False
        else:
            self.showMaximized()
            self.maximize_button.setText("기본 크기")
            self.is_maximized = True
    
    def update_current_time(self):
        current_time = QDateTime.currentDateTime()
        target_time = self.time_edit.dateTime()
        
        # Format and display current time
        self.current_time_display.setText(current_time.toString("yyyy-MM-dd HH:mm:ss"))
        
        # Calculate and display remaining time
        seconds_remaining = current_time.secsTo(target_time)
        if seconds_remaining <= 0:
            self.remaining_display.setText("0:00:00 (예매 시간 도달)")
            if self.is_running and not self.access_timer.isActive():
                self.start_access_attempts()
        else:
            hours = seconds_remaining // 3600
            minutes = (seconds_remaining % 3600) // 60
            seconds = seconds_remaining % 60
            self.remaining_display.setText(f"{hours}:{minutes:02d}:{seconds:02d}")
            
            # Update progress bar for remaining time (max 30 minutes visualization)
            if seconds_remaining <= 1800:  # 30 minutes
                progress = 100 - (seconds_remaining / 1800 * 100)
                self.progress_bar.setValue(int(progress))
                
    def add_custom_site(self):
        site_name = self.site_name_input.text().strip()
        site_url = self.site_url_input.text().strip()
        
        if not site_name or not site_url:
            QMessageBox.warning(self, "입력 오류", 
                            "사이트 이름과 URL을 모두 입력하세요.")
            return
        
        if not site_url.startswith("http://") and not site_url.startswith("https://"):
            site_url = "https://" + site_url
        
        # Add to the dictionary and combobox
        self.ticket_sites[site_name] = site_url
        save_sites(self.ticket_sites)
        
        # Update combobox
        current_items = [self.site_combo.itemText(i) for i in range(self.site_combo.count())]
        if site_name not in current_items:
            self.site_combo.addItem(site_name)
        
        # Select the newly added site
        self.site_combo.setCurrentText(site_name)
        
        # Clear inputs
        self.site_name_input.clear()
        self.site_url_input.clear()
        
        QMessageBox.information(self, "사이트 추가", 
                            f"사이트가 추가되었습니다: {site_name}")

    def remove_custom_site(self):
        current_site = self.site_combo.currentText()
        
        if current_site in self.ticket_sites:
            # Ensure there's more than one site before allowing removal
            if len(self.ticket_sites) > 1:
                confirm = QMessageBox.question(self, "사이트 삭제",
                                            f"'{current_site}'를 삭제하시겠습니까?'{current_site}'?)",
                                            QMessageBox.Yes | QMessageBox.No)
                
                if confirm == QMessageBox.Yes:
                    # Remove from dictionary and combobox
                    del self.ticket_sites[current_site]
                    save_sites(self.ticket_sites)
                    self.site_combo.removeItem(self.site_combo.currentIndex())
                    QMessageBox.information(self, "사이트 삭제", "선택한 사이트가 삭제되었습니다.")  # "The selected site has been removed."
            else:
                # Show a warning if there's only one site left
                QMessageBox.warning(self, "오류", "최소한 하나의 사이트는 남겨두어야 합니다.")  # "At least one site must remain"
        
    
    def start_access(self):
        self.is_running = True
        self.success = False
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.site_combo.setEnabled(False)
        self.time_edit.setEnabled(False)
        
        target_time = self.time_edit.dateTime()
        current_time = QDateTime.currentDateTime()
        seconds_remaining = current_time.secsTo(target_time)
        
        if seconds_remaining <= 0:
            # If target time has already passed, start access attempts immediately
            self.start_access_attempts()
        else:
            # Otherwise, wait for the target time
            self.status_display.setText("예매 시작 시간 대기 중...")
            
            # If we're within the last 5 seconds, prepare for access
            if seconds_remaining <= 5:
                self.status_display.setText("접속 준비 중...")
    
    def start_access_attempts(self):
        self.status_display.setText("접속 시도 중...")
        self.access_count = 0
        
        # Start the access timer
        self.access_timer.start(int(self.access_interval * 1000))
    
    def attempt_access(self):
        self.access_count += 1
        site_name = self.site_combo.currentText()
        site_url = self.ticket_sites[site_name]
        
        # Update status
        self.status_display.setText(f"접속 시도 중... (시도 #{self.access_count}) (Attempt #{self.access_count})")
        
        try:
            # Randomize user agent to avoid detection
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
            ]
            headers = {
                'User-Agent': random.choice(user_agents),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1"  
                }
            
            #Create a session to maintain cookies
            session = requests.Session()
            
            
            
            # Make HEAD request first to check if site is available
            response = session.head(site_url, headers=headers, timeout=3)
            
            # If successful, make a GET request to check for waiting room
            if response.status_code == 200:
                response = session.get(site_url, headers=headers, timeout=5)
                
                # Check if in waiting room (this is site-specific and would need customization)
                if "대기" in response.text or "waiting" in response.text.lower():
                    self.status_display.setText("대기실에 진입했습니다. 자동 새로고침 중...")
                else:
                    # Success! Open the browser and stop the program
                    self.access_success(site_url)
            elif response.status_code == 503 or response.status_code == 429:
                # Service unavailable or too many requests
                self.status_display.setText(f"사이트가 혼잡합니다. 재시도 중... (상태 코드: {response.status_code})")
            else:
                # Some other status code
                self.status_display.setText(f"재시도 중... (Retrying...) (상태 코드: {response.status_code})")
                
        except requests.exceptions.RequestException as e:
            # Connection failed, retry
            self.status_display.setText(f"연결 실패, 재시도 중... (오류: {str(e)[:30]})")
        
        # Incremental backoff if we've made many attempts
        if self.access_count > 10:
            self.access_interval = min(2.0, self.access_interval * 1.1)  # Gradually increase interval up to 2 seconds
            self.access_timer.setInterval(int(self.access_interval * 1000))
    
    def access_success(self, url):
        self.success = True
        self.status_display.setText("접속 성공! 브라우저에서 열기...")
        self.stop_access()
        
        # # Show success message
        # QMessageBox.information(self, "접속 성공", "예매 사이트에 접속했습니다! 브라우저를 열고 예매를 진행하세요.")
        
        # Open browser
        webbrowser.open(url)
        
        QApplication.quit()
    
    def stop_access(self):
        self.is_running = False
        self.access_timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.site_combo.setEnabled(True)
        self.time_edit.setEnabled(True)
        
        if self.success:
            self.status_display.setText("접속 성공! 프로그램을 종료하세요.")
        else:
            self.status_display.setText("대기 중")
        
        # Reset access interval
        self.access_interval = 0.5

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KBOTicketAccessApp()
    window.show()
    sys.exit(app.exec_())