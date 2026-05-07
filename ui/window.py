# Desktop_Agent/ui/window.py
import yaml, math, ctypes, random
import win32gui
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QCursor, QPen, QColor, QPainterPath

from ui.stickman_engine.core import StickmanPhysical
from ui.chat_bubble import ChatBubble

try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
except: pass

class OverlayWindow(QWidget):
    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        self.load_config()
        
        screen_size = QApplication.primaryScreen().size()
        self.screen_w = screen_size.width()
        self.screen_h = screen_size.height()
        self.base_ground = self.screen_h 
        
        self.s = StickmanPhysical(
            self.cfg['agent']['color'],
            self.cfg['agent']['line_thickness'],
            self.cfg['agent']['base_height'],
            self.screen_w / 2,
            self.screen_h 
        )
        self.s.color = "#FF8C00" 
        self.bubble = ChatBubble()
        
        self.vx, self.vy = 0.0, 0.0 
        self.anim_state = "IDLE"
        
        self.mission_state = "IDLE"
        self.next_mission_state = "IDLE" 
        self.wait_timer = 0              
        
        self.mission_target = None
        self.grapple_length = 0
        self.landing_timer = 0 
        self.swing_dir = 1     
        
        self.capture_sequence_stage = "IDLE"
        self.capture_seq_frame = 0
        self.braking_timer = 0
        self.wall_jump_timer = 0
        
        self.cmd_queue = []
        self.bus.subscribe("UI_SET_STATE", lambda s: self.cmd_queue.append(("STATE", s)))
        
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.engine_loop)
        self.timer.start(1000 // self.cfg['system']['fps'])

    def load_config(self):
        with open("config.yaml", "r", encoding="utf-8") as f:
            self.cfg = yaml.safe_load(f)

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0, self.screen_w, self.screen_h)
        self.show()

    def process_commands(self):
        while self.cmd_queue:
            cmd, data = self.cmd_queue.pop(0)
            if cmd == "STATE":
                if data == "START_MISSION":
                    self.mission_target = QCursor.pos() 
                    self.mission_state = "MOVE_UP_1"
                    self.s.hover_seq_stage = "IDLE" 
                else:
                    self.mission_state = "IDLE"
                    self.anim_state = data
                    if data == "IDLE": self.s.hover_seq_stage = "IDLE"

    def trigger_wait(self, next_state, frames):
        self.mission_state = "WAIT"
        self.next_mission_state = next_state
        self.wait_timer = frames

    def get_active_window_rect(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            if win32gui.IsIconic(hwnd) or not win32gui.IsWindowVisible(hwnd): return None
            class_name = win32gui.GetClassName(hwnd)
            if class_name in ["WorkerW", "Progman", "Shell_TrayWnd"]: return None
            return win32gui.GetWindowRect(hwnd)
        except: return None

    def engine_loop(self):
        self.process_commands()
        
        # 维护飞行帧数计数器
        if self.anim_state == "HOVER":
            if not hasattr(self.s, 'hover_seq_frame'): self.s.hover_seq_frame = 0
            self.s.hover_seq_frame += 1
            
        rect = self.get_active_window_rect()
        target_ground = self.base_ground
        is_grabbing_ledge = False
        can_collide = self.mission_state not in ["START_GRAPPLE", "THROWING", "GRAPPLING"]

        if rect and can_collide:
            left, top, right, bottom = rect
            if left <= self.s.virtual_x <= right:
                standing_y_top = top - self.s.total_leg_len * 0.95 - self.s.h * 0.65
                standing_y_bot = bottom - self.s.total_leg_len * 0.95 - self.s.h * 0.65
                if standing_y_bot < self.s.virtual_y < bottom + 45:
                    target_ground = bottom; is_grabbing_ledge = True
                elif self.s.virtual_y <= standing_y_bot and self.s.virtual_y > top: target_ground = bottom
                elif standing_y_top < self.s.virtual_y < top + 45:
                    target_ground = top; is_grabbing_ledge = True
                elif self.s.virtual_y <= standing_y_top: target_ground = top

        if target_ground != self.base_ground: self.s.ground_line = target_ground  
        else: self.s.ground_line = self.base_ground 
            
        head_ground_limit = self.s.ground_line - self.s.total_leg_len * 0.95 - self.s.h * 0.65
        active_target = QPointF(self.s.virtual_x, self.s.virtual_y)
        
        in_air = self.s.virtual_y < head_ground_limit - 5
        
        in_window_bounds = False
        win_left, win_top, win_right, win_bottom = 0, 0, 0, 0
        if rect:
            win_left, win_top, win_right, win_bottom = rect
            if win_left - 10 <= self.s.virtual_x <= win_right + 10 and win_top - 50 <= self.s.virtual_y <= win_bottom + 50:
                in_window_bounds = True

        if self.mission_state == "WAIT":
            self.wait_timer -= 1
            if in_air: self.anim_state = "CLIMBING_IDLE"
            else: self.anim_state = "IDLE"
            # 🌟 修复抽搐：这里绝对不准刚性归零！用惯性平滑减速，防止骨折！
            self.vx *= 0.6; self.vy *= 0.6 
            if self.wait_timer <= 0:
                self.mission_state = self.next_mission_state
                
        elif self.mission_state == "MOVE_UP_1" or self.mission_state == "MOVE_UP_2":
            if self.mission_target:
                active_target = QPointF(self.s.virtual_x, self.mission_target.y() if self.mission_state == "MOVE_UP_2" else -100) 
                
                if in_window_bounds:
                    if self.anim_state != "WALL_JUMP" and abs(self.vx) > 3.0:
                        self.anim_state = "WALL_JUMP"
                        self.wall_jump_timer = 22 
                        dist_to_left = abs(self.s.virtual_x - win_left)
                        dist_to_right = abs(self.s.virtual_x - win_right)
                        self.s.wall_jump_dir = 1 if dist_to_left < dist_to_right else -1
                        # 物理引擎里的反抽搐锁 Clamp delta_V 会处理，这里保留一部分撞击动能
                        self.vx *= 0.3; self.vy *= 0.3
                else:
                    if is_grabbing_ledge: self.anim_state = "PARKOUR"
                    else: self.anim_state = "CLIMBING"

                if self.mission_state == "MOVE_UP_1":
                    if self.s.virtual_y <= head_ground_limit + 5 and target_ground != self.base_ground: 
                        self.trigger_wait("MOVE_HORIZ", 20) 
                    elif self.mission_target and self.s.virtual_y <= self.mission_target.y(): 
                        self.trigger_wait("MOVE_HORIZ", 20)
                elif self.mission_state == "MOVE_UP_2":
                    if is_grabbing_ledge: self.anim_state = "PARKOUR"
                    elif self.s.virtual_y <= self.mission_target.y() + 15: 
                        self.trigger_wait("START_GRAPPLE", 60) 

        elif self.mission_state == "MOVE_HORIZ":
            if self.mission_target:
                active_target = QPointF(self.mission_target.x(), self.s.virtual_y) 
                dist = abs(self.s.virtual_x - self.mission_target.x())
                
                if in_air and not is_grabbing_ledge:
                    # 修复锁死：一旦进入 HOVER 就不准掉回爬行状态，直到抵达目标点容差范围
                    if self.anim_state == "HOVER":
                        pass
                    elif dist > 180:
                        self.anim_state = "HOVER"
                        self.s.hover_seq_stage = "START_SEQUENCE"
                        self.s.hover_seq_frame = 0
                    else:
                        self.anim_state = "CLIMBING"
                else: 
                    if self.anim_state == "RUNNING":
                        if dist <= 80: self.anim_state = "CLIMBING"
                    else:
                        if dist > 180: self.anim_state = "RUNNING"
                        else: self.anim_state = "CLIMBING"
                
                if dist < 15: 
                    # 🌟 修复抽搐：这里绝对不要写 vx=0.0！彻底干掉急刹！
                    self.trigger_wait("MOVE_UP_2", 20) 
                    
        elif self.mission_state == "WANDER":
            if self.mission_target:
                active_target = QPointF(self.mission_target.x(), self.s.virtual_y) 
                dist = abs(self.s.virtual_x - self.mission_target.x())
                self.anim_state = "CLIMBING" 
                if dist < 15: 
                    # 🌟 修复抽搐：WANDER溜达状态也不要强制急刹！
                    self.trigger_wait("IDLE", 30)

        elif self.mission_state == "START_GRAPPLE":
            if head_ground_limit - self.s.virtual_y < self.s.h * 1.5: self.mission_state = "DROP"
            else:
                self.swing_dir = 1 if self.mission_target.x() > self.s.virtual_x else -1
                target_lowest_y = head_ground_limit - self.s.h * 0.25 
                dy = target_lowest_y - 0 
                current_dy = max(1.0, self.s.virtual_y - 0)
                if dy**2 - current_dy**2 > 0: dx = math.sqrt(dy**2 - current_dy**2)
                else: dx = 300 
                anchor_x = self.s.virtual_x + dx * self.swing_dir
                anchor_x = max(100, min(self.screen_w - 100, anchor_x))
                self.s.target_anchor = QPointF(anchor_x, 0)
                self.s.hook_pos = QPointF(self.s.smooth_r_hand) 
                self.grapple_length = math.hypot(self.s.virtual_x - anchor_x, self.s.virtual_y - 0)
                self.mission_state = "THROWING"
                self.anim_state = "GRAPPLING"

        elif self.mission_state == "THROWING":
            self.anim_state = "GRAPPLING"
            hx, hy = self.s.hook_pos.x(), self.s.hook_pos.y()
            tx, ty = self.s.target_anchor.x(), self.s.target_anchor.y()
            dist = math.hypot(tx - hx, ty - hy)
            speed = 95.0 
            if dist > speed: self.s.hook_pos += QPointF((tx-hx)/dist * speed, (ty-hy)/dist * speed)
            else:
                self.s.hook_pos = self.s.target_anchor
                self.mission_state = "GRAPPLING"
                self.vx = 2.0 * self.swing_dir 

        elif self.mission_state == "GRAPPLING":
            self.anim_state = "GRAPPLING"
            passed_lowest = (self.swing_dir == 1 and self.s.virtual_x >= self.s.target_anchor.x()) or \
                            (self.swing_dir == -1 and self.s.virtual_x <= self.s.target_anchor.x())
            if passed_lowest:
                self.mission_state = "DROP"
                self.s.hook_pos = None; self.s.target_anchor = None
                self.anim_state = "IDLE" 

        elif self.mission_state == "DROP":
            self.anim_state = "IDLE" 
            if self.s.virtual_y >= head_ground_limit - 10:
                self.mission_state = "LANDING"
                self.anim_state = "LANDING"
                self.landing_timer = 50 
                self.vx *= 0.3 

        elif self.mission_state == "LANDING":
            self.landing_timer -= 1
            self.vx *= 0.8
            if self.landing_timer <= 15: self.anim_state = "IDLE" 
            else: self.anim_state = "LANDING"
            if self.landing_timer <= 0: self.mission_state = "IDLE"
                
        elif self.mission_state == "IDLE":
            if not hasattr(self, 'idle_timer'): self.idle_timer = 0
            
            if is_grabbing_ledge: 
                self.anim_state = "PARKOUR"
                self.idle_timer = 0 
            else:
                if in_air: 
                    self.anim_state = "CLIMBING_IDLE"
                    self.idle_timer = 0 
                else: 
                    self.anim_state = "IDLE"
                    if abs(self.vx) < 0.2 and abs(self.vy) < 0.2:
                        self.idle_timer += 1
                    else:
                        self.idle_timer = 0
                        
                    if self.idle_timer > 240:
                        self.idle_timer = 0
                        offset = random.randint(60, 120) * random.choice([-1, 1])
                        target_x = self.s.virtual_x + offset
                        target_x = max(50, min(self.screen_w - 50, target_x)) 
                        if rect: 
                            win_left, win_top, win_right, win_bottom = rect
                            if win_left <= self.s.virtual_x <= win_right:
                                target_x = max(win_left + 20, min(win_right - 20, target_x))
                        
                        self.mission_target = QPointF(target_x, self.s.virtual_y)
                        self.mission_state = "WANDER"

        # ==========================================
        # 🌟 到达转向（Arrival Steering）完美动力引擎
        # ==========================================
        if self.mission_state == "WAIT" or self.capture_sequence_stage != "IDLE": pass 
        
        elif self.anim_state == "WALL_JUMP" and in_window_bounds:
            self.s.wall_jump_timer = self.wall_jump_timer
            if self.wall_jump_timer > 10:
                target_x = win_left + 15 if self.s.wall_jump_dir == 1 else win_right - 15
                self.s.virtual_x += (target_x - self.s.virtual_x) * 0.5 
                self.vx *= 0.1; self.vy *= 0.5 
            elif self.wall_jump_timer == 10:
                self.vx = 18.0 * self.s.wall_jump_dir; self.vy = -16.0
            else:
                self.vx *= 0.96; self.vy += 0.8 
            
            self.wall_jump_timer -= 1
            if self.wall_jump_timer <= 0:
                self.wall_jump_timer = 22 
                self.s.wall_jump_dir *= -1
                
        elif self.anim_state == "PARKOUR":
            if self.s.virtual_y - 12.0 <= head_ground_limit: self.vy = head_ground_limit - self.s.virtual_y 
            else: self.vy = -12.0 
            self.vx *= 0.5

        elif self.anim_state == "GRAPPLING":
            self.vy += 1.8 
            if self.mission_state == "GRAPPLING" and self.s.hook_pos:
                gx, gy = self.s.hook_pos.x(), self.s.hook_pos.y()
                dx = self.s.virtual_x - gx; dy = self.s.virtual_y - gy
                dist = math.hypot(dx, dy)
                if dist > self.grapple_length:
                    nx, ny = dx / dist, dy / dist
                    self.s.virtual_x = gx + nx * self.grapple_length
                    self.s.virtual_y = gy + ny * self.grapple_length
                    v_dot_n = self.vx * nx + self.vy * ny
                    if v_dot_n > 0: self.vx -= v_dot_n * nx; self.vy -= v_dot_n * ny
            self.vx *= 0.998; self.vy *= 0.998 
            
        elif self.anim_state in ["RUNNING", "CLIMBING", "HOVER"]:
            move_dx = active_target.x() - self.s.virtual_x
            move_dy = active_target.y() - self.s.virtual_y if self.anim_state in ["CLIMBING", "HOVER"] else 0
            move_dist = max(1.0, math.hypot(move_dx, move_dy))
            
            if self.anim_state == "HOVER":
                max_speed = 22.0
                braking_dist = 200.0
                
                # 🌟 核心：距离映射平滑刹车算法
                if move_dist < 60:
                    self.s.hover_seq_stage = "STABILIZING"
                    target_speed = max_speed * (move_dist / braking_dist)
                    lerp_factor = 0.1
                elif move_dist < braking_dist:
                    self.s.hover_seq_stage = "BRAKING"
                    target_speed = max_speed * (move_dist / braking_dist) 
                    lerp_factor = 0.08
                else:
                    if getattr(self.s, 'hover_seq_frame', 0) < 40:
                        self.s.hover_seq_stage = "START_SEQUENCE"
                    else:
                        self.s.hover_seq_stage = "CRUISING"
                    target_speed = max_speed
                    lerp_factor = 0.04

                target_vx = (move_dx / move_dist) * target_speed
                target_vy = (move_dy / move_dist) * target_speed

                self.vx += (target_vx - self.vx) * lerp_factor
                self.vy += (target_vy - self.vy) * lerp_factor
                
            else:
                if self.anim_state == "RUNNING": 
                    max_speed = 18.0
                    lerp_factor = 0.12
                else:
                    max_speed = 6.5 
                    lerp_factor = 0.08
                
                target_vx = (move_dx / move_dist) * max_speed
                target_vy = (move_dy / move_dist) * max_speed if self.anim_state == "CLIMBING" else 0
                
                self.vx += (target_vx - self.vx) * lerp_factor
                self.vy += (target_vy - self.vy) * lerp_factor
            
        else:
            self.vx *= 0.75 
            if self.anim_state == "CLIMBING_IDLE": self.vy *= 0.70  
            elif self.s.virtual_y < head_ground_limit - 5: self.vy += 0.8 
            else: self.vy *= 0.70 
                
            if abs(self.vx) < 0.1: self.vx = 0
            if abs(self.vy) < 0.1 and self.s.virtual_y >= head_ground_limit - 5: self.vy = 0
            
        self.s.virtual_x += self.vx
        self.s.virtual_y += self.vy
        
        if self.s.virtual_y > head_ground_limit:
            self.s.virtual_y = head_ground_limit
            if self.vy > 0: self.vy = 0
            
        future_x = self.s.virtual_x
        if future_x < 20: self.s.virtual_x = 20; self.vx = 0
        elif future_x > self.screen_w - 20: self.s.virtual_x = self.screen_w - 20; self.vx = 0
            
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        
        if self.anim_state == "GRAPPLING" and self.s.hook_pos:
            painter.setRenderHint(QPainter.Antialiasing)
            hx, hy = self.s.smooth_r_hand.x(), self.s.smooth_r_hand.y()
            tx, ty = self.s.hook_pos.x(), self.s.hook_pos.y()
            dist = max(1.0, math.hypot(hx - tx, hy - ty))
            
            pen_rope = QPen(QColor(80, 80, 80), 3, Qt.SolidLine)
            painter.setPen(pen_rope)
            
            if self.mission_state == "THROWING" or (self.mission_state == "GRAPPLING" and dist < self.grapple_length - 5):
                path = QPainterPath()
                path.moveTo(hx, hy)
                slack = 40 if self.mission_state == "THROWING" else (self.grapple_length - dist) * 0.8
                path.quadTo((hx+tx)/2, (hy+ty)/2 + slack, tx, ty)
                painter.drawPath(path)
            else:
                bend_factor = 0.8
                bend_x = (hx + tx) / 2 - self.vx * bend_factor
                bend_y = (hy + ty) / 2 - self.vy * bend_factor + 10 
                path = QPainterPath()
                path.moveTo(hx, hy)
                path.quadTo(bend_x, bend_y, tx, ty)
                painter.drawPath(path)
            
            pen_hook = QPen(QColor(180, 180, 180), 4, Qt.SolidLine)
            pen_hook.setCapStyle(Qt.RoundCap)
            painter.setPen(pen_hook)
            painter.drawLine(QPointF(tx - 10, ty + 12), QPointF(tx, ty))
            painter.drawLine(QPointF(tx + 10, ty + 12), QPointF(tx, ty))
            painter.drawLine(QPointF(tx, ty + 15), QPointF(tx, ty))
            
            painter.setBrush(Qt.NoBrush) 

        self.s.draw(painter, self.anim_state, QPointF(self.s.virtual_x, self.s.virtual_y), current_vx=self.vx, current_vy=self.vy)