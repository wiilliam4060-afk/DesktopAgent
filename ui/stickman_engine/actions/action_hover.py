# Desktop_Agent/ui/stickman_engine/actions/action_hover.py
import math
from PyQt5.QtCore import QPointF

class ActionHover:
    @staticmethod
    def calculate_v_nodes(agent, v_head, v_chest_base, v_hips_base, t, current_vx, current_vy):
        fly_dir = 1 if current_vx > 0 else -1
        stage = getattr(agent, 'hover_seq_stage', "IDLE")
        
        # 🌟 修复姿态：彻底释放空气动力学！
        if stage == "START_SEQUENCE":
            target_theta = 75.0  # 起飞加速：极度前倾
        elif stage == "BRAKING":
            target_theta = -30.0 # 猛烈刹车：身体猛然后仰张开，利用胸腔风阻减速
        elif stage == "STABILIZING" or stage == "IDLE":
            target_theta = 0.0   # 悬停：垂直站立
        else:
            target_theta = 82.0  # 🚀 巡航：近乎完全水平！像导弹一样的超人姿态

        current_theta = getattr(agent, 'sm_hover_theta', 0.0)
        
        # 平滑过渡theta角度，防止瞬间突变抽搐
        lerp_speed = 0.05 if stage == "BRAKING" else 0.032
        current_theta += (target_theta - current_theta) * lerp_speed
        agent.sm_hover_theta = current_theta

        rad = math.radians(current_theta)
        chest_dist = agent.h * 0.2
        hips_dist = agent.h * 0.45
        
        # 根据 theta 角度，计算胸腔和骨盆的虚拟IK目标点。不需要随呼吸微动了。
        v_chest = v_head + QPointF(math.sin(rad) * -fly_dir * chest_dist, math.cos(rad) * chest_dist)
        v_hips = v_head + QPointF(math.sin(rad) * -fly_dir * hips_dist, math.cos(rad) * hips_dist)
            
        return v_chest, v_hips

    @staticmethod
    def get_spine_params(agent, t, current_vx, current_vy):
        fly_dir = 1 if current_vx > 0 else -1
        stage = getattr(agent, 'hover_seq_stage', "IDLE")
        
        if stage == "BRAKING":
            t_hl, t_fa = 0.8 * fly_dir, 35 * fly_dir  # 刹车：低头，背部肌肉极限紧绷
        elif stage == "STABILIZING" or stage == "IDLE":
            t_hl, t_fa = 0.0, 5 * fly_dir             
        else:
            # 🚀 巡航：身体水平时，头必须抬起来看前方，背部形成流线型微曲
            t_hl, t_fa = -0.6 * fly_dir, -15 * fly_dir 

        # 平滑过渡脊柱参数
        c_hl = getattr(agent, 'sm_spine_hl', t_hl)
        c_fa = getattr(agent, 'sm_spine_fa', t_fa)
        
        ls = 0.035
        c_hl += (t_hl - c_hl) * ls
        c_fa += (t_fa - c_fa) * ls
        
        agent.sm_spine_hl = c_hl
        agent.sm_spine_fa = c_fa
        
        return c_hl, c_fa

    @staticmethod
    def calculate_limbs(agent, t, current_vx, current_vy, target_pos, p_hips, p_chest, sh_l, sh_r):
        fly_dir = 1 if current_vx > 0 else -1
        stage = getattr(agent, 'hover_seq_stage', "IDLE")
        
        arm_reach = (agent.arm_len_up + agent.arm_len_low) * 0.98
        leg_reach = (agent.leg_len_up + agent.leg_len_low) * 0.98

        if stage == "START_SEQUENCE":
            # 起飞加速：四肢微蜷缩
            t_hr_v = QPointF(-arm_reach * 0.9 * fly_dir, 0)
            t_hl_v = QPointF(-arm_reach * 0.8 * fly_dir, 0)
            t_fr_v = QPointF(-leg_reach * fly_dir, 5)
            t_fl_v = QPointF(-leg_reach * 0.95 * fly_dir, 0)
            
        elif stage == "BRAKING":
            # 钢铁侠式双掌前推刹车
            t_hr_v = QPointF(arm_reach * fly_dir, 5) 
            t_hl_v = QPointF(arm_reach * 0.95 * fly_dir, 0)
            t_fr_v = QPointF(40 * fly_dir, leg_reach * 0.9)
            t_fl_v = QPointF(-10 * fly_dir, leg_reach)
            
        elif stage == "STABILIZING" or stage == "IDLE":
            # 悬停状态：自然下垂并微微晃动
            t_hr_v = QPointF(12 * fly_dir, arm_reach)   
            t_hl_v = QPointF(-12 * fly_dir, arm_reach)  
            t_fr_v = QPointF(10 * fly_dir, leg_reach)   
            t_fl_v = QPointF(-10 * fly_dir, leg_reach)
            
        else:
            # 🚀 巡航：核心修复！双手紧贴大腿向后方并拢，双腿笔直向后，脚尖绷紧！
            t_hr_v = QPointF(-arm_reach * 0.98 * fly_dir, 5)
            t_hl_v = QPointF(-arm_reach * 0.98 * fly_dir, 0)
            t_fr_v = QPointF(-leg_reach * 0.98 * fly_dir, 0)
            t_fl_v = QPointF(-leg_reach * 0.98 * fly_dir, -5)

        # 所有的肢体目标点必须平滑过渡，否则高速飞行时 IK 会爆炸导致肢体撕裂抽搐！
        c_hr_v_x = getattr(agent, 'sm_hr_v_x', t_hr_v.x())
        c_hr_v_y = getattr(agent, 'sm_hr_v_y', t_hr_v.y())
        c_hl_v_x = getattr(agent, 'sm_hl_v_x', t_hl_v.x())
        c_hl_v_y = getattr(agent, 'sm_hl_v_y', t_hl_v.y())
        c_fr_v_x = getattr(agent, 'sm_fr_v_x', t_fr_v.x())
        c_fr_v_y = getattr(agent, 'sm_fr_v_y', t_fr_v.y())
        c_fl_v_x = getattr(agent, 'sm_fl_v_x', t_fl_v.x())
        c_fl_v_y = getattr(agent, 'sm_fl_v_y', t_fl_v.y())

        ls = 0.05 
        c_hr_v_x += (t_hr_v.x() - c_hr_v_x) * ls; c_hr_v_y += (t_hr_v.y() - c_hr_v_y) * ls
        c_hl_v_x += (t_hl_v.x() - c_hl_v_x) * ls; c_hl_v_y += (t_hl_v.y() - c_hl_v_y) * ls
        c_fr_v_x += (t_fr_v.x() - c_fr_v_x) * ls; c_fr_v_y += (t_fr_v.y() - c_fr_v_y) * ls
        c_fl_v_x += (t_fl_v.x() - c_fl_v_x) * ls; c_fl_v_y += (t_fl_v.y() - c_fl_v_y) * ls

        agent.sm_hr_v_x, agent.sm_hr_v_y = c_hr_v_x, c_hr_v_y
        agent.sm_hl_v_x, agent.sm_hl_v_y = c_hl_v_x, c_hl_v_y
        agent.sm_fr_v_x, agent.sm_fr_v_y = c_fr_v_x, c_fr_v_y
        agent.sm_fl_v_x, agent.sm_fl_v_y = c_fl_v_x, c_fl_v_y

        sway = math.sin(t * 6.0) * 2 if (stage == "STABILIZING" or stage == "IDLE") else 0
        
        h_r = p_chest + QPointF(c_hr_v_x, c_hr_v_y)
        h_l = sh_l + QPointF(c_hl_v_x, c_hl_v_y)
        f_r = p_hips + QPointF(c_fr_v_x, c_fr_v_y + sway)
        f_l = p_hips + QPointF(c_fl_v_x, c_fl_v_y - sway)

        agent.smooth_r_hand = h_r
        return f_l, f_r, h_l, agent.smooth_r_hand