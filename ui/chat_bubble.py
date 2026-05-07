# Desktop_Agent/ui/chat_bubble.py
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import QRectF, Qt

class ChatBubble:
    def __init__(self):
        self.text = ""
        self.visible = False
        self.timer = 0
        
    def show_message(self, text, duration=180):
        """显示气泡，duration为帧数 (默认约3秒)"""
        self.text = text
        self.visible = True
        self.timer = duration
        
    def update(self):
        if self.visible:
            self.timer -= 1
            if self.timer <= 0:
                self.visible = False
                
    def draw(self, painter: QPainter, head_x, head_y):
        if not self.visible:
            return
            
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 气泡矩形 (在头部右上方)
        rect = QRectF(head_x + 20, head_y - 70, 220, 60)
        
        # 绘制半透明背景
        painter.setBrush(QColor(255, 255, 255, 230))
        painter.setPen(QPen(QColor(40, 40, 40), 2))
        painter.drawRoundedRect(rect, 12, 12)
        
        # 绘制文本
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        painter.drawText(rect, Qt.AlignCenter | Qt.TextWordWrap, self.text)