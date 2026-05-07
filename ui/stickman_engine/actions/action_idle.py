# Desktop_Agent/ui/stickman_engine/actions/action_idle.py
import math
from PyQt5.QtCore import QPointF

class ActionIdle:
    @staticmethod
    def calculate_v_nodes(agent, v_chest_base, v_hips_base, t, current_vx, current_vy):
        breath_y = math.sin(t * 1.2) * 2.5       
        sway_x = math.cos(t * 0.6) * 1.5         
        
        chest = v_chest_base + QPointF(sway_x, breath_y)
        # 🌟 修复蜷腿：骨盆上提 12 像素，抵消重力下沉，使得双腿能彻底绷直！
        hips = v_hips_base + QPointF(sway_x * 0.5, breath_y * 0.3 - 12) 
        
        return chest, hips

    @staticmethod
    def get_spine_params(agent, t, current_vx, current_vy):
        head_lag = math.sin(t * 1.5) * 0.08
        flex_amount = 2.0 + math.sin(t * 0.8) * 1.5 
        return head_lag, flex_amount

    @staticmethod
    def calculate_limbs(agent, t, current_vx, current_vy, target_pos, p_hips, p_chest, sh_l, sh_r, state):
        ground_y = agent.ground_line - agent.thickness / 2
        
        foot_shift = max(0, math.sin(t * 0.5)) 
        lift_y = 0
        if foot_shift > 0.95: 
            lift_y = (foot_shift - 0.95) * 30 
            
        # 🌟 修复蜷腿：站距缩小（偏移从 16 减小到 8），双腿并拢立正
        f_l = QPointF(agent.virtual_x - 8, ground_y - lift_y)
        f_r = QPointF(agent.virtual_x + 8, ground_y)
        
        arm_sway = math.sin(t * 1.2 + 1.0) * 2.5
        h_l = sh_l + QPointF(-10 + arm_sway, agent.arm_len_up + agent.arm_len_low - 5 - arm_sway)
        
        if state == "CLIMBING_IDLE":
            # 🌟 修复蜷崖边抽搐：悬挂时双腿必须伸展到 95% 的总腿长，不能只伸出一半
            hang_len = agent.total_leg_len * 0.95
            f_l = p_hips + QPointF(-8, hang_len)
            f_r = p_hips + QPointF(8 + math.sin(t * 2) * 4, hang_len + math.cos(t * 2) * 3) 
            h_l = sh_l + QPointF(-18, -10)
            target_r_hand = sh_r + QPointF(18, -10)
        else:
            target_r_hand = sh_r + QPointF(10 + arm_sway, agent.arm_len_up + agent.arm_len_low - 5 + arm_sway)

        if state == "TARGET":
            agent.smooth_r_hand += (target_pos - agent.smooth_r_hand) * 0.25
        else:
            agent.smooth_r_hand += (target_r_hand - agent.smooth_r_hand) * 0.25
        h_r = agent.smooth_r_hand

        return f_l, f_r, h_l, h_r