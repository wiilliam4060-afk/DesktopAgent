# Desktop_Agent/ui/stickman_engine/actions/action_parkour.py
import math
from PyQt5.QtCore import QPointF

class ActionParkour:
    @staticmethod
    def calculate_v_nodes(agent, v_head, v_chest_base, v_hips_base, t, current_vx, current_vy):
        # 引体向上发力：胸口前倾贴近边缘，臀部收缩
        v_chest = v_chest_base + QPointF(0, 15)
        v_hips = v_hips_base + QPointF(0, -10)
        return v_chest, v_hips

    @staticmethod
    def get_spine_params(agent, t, current_vx, current_vy):
        # 抬着头紧紧盯着边缘，身体弓起发力
        head_lag = 0.25 
        flex_amount = 18 * agent.dir 
        return head_lag, flex_amount

    @staticmethod
    def calculate_limbs(agent, t, current_vx, current_vy, target_pos, p_hips, p_chest, sh_l, sh_r):
        # 🌟 灵魂所在：双手死死扣住目标边缘 (ground_line)
        grab_y = agent.ground_line
        h_l = QPointF(p_chest.x() - 15, grab_y)
        h_r = QPointF(p_chest.x() + 15, grab_y)
        agent.smooth_r_hand = h_r
        
        # 🌟 身体往上拔时，双腿悬空努力往上收
        leg_spread = 15
        f_l = QPointF(p_hips.x() - leg_spread, p_hips.y() + 30 + math.sin(t*3)*10)
        f_r = QPointF(p_hips.x() + leg_spread, p_hips.y() + 20 - math.sin(t*3)*10)
        
        return f_l, f_r, h_l, h_r