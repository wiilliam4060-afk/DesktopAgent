# Desktop_Agent/ui/stickman_engine/actions/action_climb.py
import math
from PyQt5.QtCore import QPointF

class ActionClimb:
    @staticmethod
    def calculate_v_nodes(agent, v_chest_base, v_hips_base, t, current_vx, current_vy, is_moving):
        v_chest = QPointF(v_chest_base)
        v_hips = QPointF(v_hips_base)
        if is_moving:
            is_horizontal = abs(current_vx) > abs(current_vy) * 1.5
            if is_horizontal:
                # 横向爬行：臀部保持平稳，只随惯性微动，不再夸张扭曲
                v_hips.setX(v_hips.x() - current_vx * 0.2)
                v_hips.setY(v_hips.y() + 2)
            else:
                # 纵向爬行：躯干发力扭动，但收紧幅度
                v_hips.setX(v_hips.x() + math.cos(t) * 10)
                v_hips.setY(v_hips.y() + math.sin(t*2) * 5)
        return v_chest, v_hips

    @staticmethod
    def get_spine_params(agent, t, current_vx, current_vy, is_moving):
        is_horizontal = abs(current_vx) > abs(current_vy) * 1.5
        if is_horizontal:
            # 横向时脊柱基本挺直
            head_lag = -current_vx * 0.01 if is_moving else 0.02
            flex_amount = 2 
        else:
            # 纵向时收紧弓背幅度
            head_lag = -math.sin(t*2)*0.1 if is_moving else math.cos(t*1.5)*0.05
            flex_amount = math.cos(t)*5 if is_moving else math.cos(t*1.5)*4
        return head_lag, flex_amount

    @staticmethod
    def get_climb_target(agent, ph, lock_key, anchor_x, anchor_y, offset_x, offset_y, current_vx, current_vy, state, custom_stride=None):
        planted_pos = agent.climb_locks[lock_key]
        s_vx, s_vy = current_vx + agent.smooth_ax, current_vy + agent.smooth_ay
        mag = math.hypot(s_vx, s_vy)
        
        # 🌟 恢复经典逻辑：静止时默认朝上抓取，不再乱劈开
        dir_x, dir_y = (s_vx / mag, s_vy / mag) if mag > 0.1 else (0, -1)
        
        stride = custom_stride if custom_stride else 65
        swing_x = -math.cos(ph) * stride * dir_x
        swing_y = -math.cos(ph) * stride * dir_y
        
        # 🌟 恢复经典逻辑：延长抓墙时间，彻底去除导致劈叉的法线外扩
        is_on_wall = math.sin(ph) < 0.2 

        if state in ["CLIMBING_IDLE", "CLIMBING_TARGET"]:
            if planted_pos is None:
                 agent.climb_locks[lock_key] = QPointF(anchor_x + offset_x, anchor_y + offset_y)
            return agent.climb_locks[lock_key]
        elif is_on_wall:
            if planted_pos is None:
                agent.climb_locks[lock_key] = QPointF(anchor_x + offset_x + swing_x, anchor_y + offset_y + swing_y)
            return agent.climb_locks[lock_key]
        else:
            agent.climb_locks[lock_key] = None
            # 🌟 恢复经典逻辑：抬手时只在 Y 轴或运动方向内收缩，绝对不向外岔开
            return QPointF(anchor_x + offset_x + swing_x, anchor_y + offset_y + swing_y - math.sin(ph)*15)

    @staticmethod
    def calculate_limbs(agent, t, current_vx, current_vy, target_pos, p_hips, p_chest, sh_l, sh_r, state, is_moving):
        v_chest_y, v_hips_y = agent.virtual_y + agent.h * 0.2, agent.virtual_y + agent.h * 0.65
        is_horizontal = is_moving and abs(current_vx) > abs(current_vy) * 1.5
        
        if is_horizontal:
            # 🌟 横向极简爬行：双手间距极小(x=±15)，交替抓取
            h_l = ActionClimb.get_climb_target(agent, t, 'hl', agent.virtual_x, v_chest_y, -15, -55, current_vx, current_vy, state, custom_stride=70)
            h_r = ActionClimb.get_climb_target(agent, t - math.pi, 'hr', agent.virtual_x, v_chest_y, 15, -55, current_vx, current_vy, state, custom_stride=70)
            
            # 🌟 恢复完美的自然下垂腿：紧凑间距(x=±8)，根据速度物理摇摆
            sway = -current_vx * 0.08 - agent.smooth_ax * 0.15
            sway = max(-0.8, min(0.8, sway))
            hang_dist = agent.total_leg_len * 0.95
            
            f_l = QPointF(p_hips.x() - 8 + math.sin(sway)*hang_dist, p_hips.y() + math.cos(sway)*hang_dist)
            f_r = QPointF(p_hips.x() + 8 + math.sin(sway)*hang_dist, p_hips.y() + math.cos(sway)*hang_dist)
            
            # 悬空下垂时必须清除腿部的墙壁锁，防止脚黏在空中
            agent.climb_locks['fl'] = agent.climb_locks['fr'] = None
        else:
            # 🌟 纵向发力爬行：手臂伸得更高(y=-60)，四肢核心收紧(x=±25)
            h_l = ActionClimb.get_climb_target(agent, t, 'hl', agent.virtual_x, v_chest_y, -25, -60, current_vx, current_vy, state)
            f_r = ActionClimb.get_climb_target(agent, t - math.pi/2, 'fr', agent.virtual_x, v_hips_y, 25, 35, current_vx, current_vy, state)
            h_r = ActionClimb.get_climb_target(agent, t - math.pi, 'hr', agent.virtual_x, v_chest_y, 25, -60, current_vx, current_vy, state)
            f_l = ActionClimb.get_climb_target(agent, t - 3*math.pi/2, 'fl', agent.virtual_x, v_hips_y, -25, 35, current_vx, current_vy, state)
            
        agent.smooth_r_hand = h_r
        return f_l, f_r, h_l, h_r