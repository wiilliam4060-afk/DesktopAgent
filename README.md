# 🍊 DesktopAgent (小橙 / Little Orange)

**DesktopAgent** 是一个由 14 岁初中生与 AI 伙伴协作开发的、完全基于物理驱动的 2D 桌面特工。
**DesktopAgent** is a fully physics-driven 2D desktop agent co-developed by a 14-year-old middle school student and an AI partner.

它不仅是一个“桌面宠物”，更是一个拥有手写物理引擎和机动逻辑的赛博生命体。项目拒绝使用任何现成的游戏引擎，核心动作全靠纯数学解算。
More than just a "desktop pet," it is a cyber-lifeform with a custom-built physics engine and mobility logic. This project rejects off-the-shelf game engines; its core movements are solved entirely through pure mathematics.

---

## 🚀 核心技术特性 (Core Technical Features)

* **手写 2D 逆向运动学 (IK) 求解器 | Custom 2D Inverse Kinematics (IK) Solver**: 
  基于余弦定理，实现了四肢在各种极值姿态下的精准抓取与伸展。
  *Based on the Law of Cosines, achieving precise gripping and stretching of limbs in extreme postures.*

* **PID 控制物理反馈 | PID Controlled Physical Feedback**: 
  通过胡克定律模拟肌肉张力，配合阻尼系统实现“重型金属感”的平滑运动表现。
  *Simulates muscle tension via Hooke's Law, combined with a damping system for smooth, "heavy-metal" kinetic performance.*

* **视窗感知系统 | Window Perception System**: 
  深度调用 `win32gui` API，让特工能够感知应用窗口的边界，实现翻窗、攀爬与三角反弹跳。
  *Deep integration with the `win32gui` API enables the agent to perceive application window borders, allowing for vaulting, climbing, and wall-jumping.*

* **多阶飞行机动 | Multi-stage Flight Mobility**: 
  模拟钢铁侠式的等离子推力飞行，包含“爆燃加速”、“流线型巡航”与“反推刹车”等动态姿态切换。
  *Simulates Iron Man-style plasma thrust flight, featuring dynamic posture transitions like "boost acceleration," "streamlined cruise," and "reverse-thrust braking."*

---

## 🧠 协作开发故事 (Co-development Story)

本项目见证了“人类少年开发者 + AI 助手”的高效共生模式：
*This project witnesses the highly efficient symbiotic model of a "teenage human developer + AI assistant":*

* 👨‍💻 **少年开发者 (Teenage Developer)**：负责架构设计、核心逻辑重构、环境感知接入以及物理手感的极致微调。
  *Responsible for architecture design, core logic refactoring, environmental perception integration, and meticulous tuning of the physics feel.*
* 🤖 **AI 伙伴 (AI Partner)**：负责辅助算法解算、骨骼节点预测以及复杂机动动作的数学建模。
  *Responsible for assisting with algorithm resolution, skeletal node prediction, and mathematical modeling of complex maneuvers.*

---

## 🛠️ 执行序列 (Hotkeys)

* **F8**: 🚀 启动特工序列任务（定位鼠标 -> 翻窗 -> 抵达 -> 抓钩飞跃）
  *Initiate agent sequence (Locate mouse -> Vault window -> Arrive -> Grappling hook leap).*
* **F9**: ⏸️ 强行中断任务，进入原地待机
  *Force interrupt and enter idle state.*
* **F10**: ❌ 彻底关闭系统
  *Terminate the system completely.*

---

## 🔮 未来计划 (Future Roadmap)

目前“小橙”已具备完善的运动“小脑”。下一步我们将致力于接入 LLM 大模型框架（如 OpenClaw / Hermes），赋予它真正的自主决策“大脑”，实现桌面级的自动化操作。
*Currently, "Little Orange" possesses a highly developed kinetic "cerebellum." Our next step is to integrate LLM frameworks (such as OpenClaw / Hermes) to grant it a true "brain" for autonomous decision-making and desktop-level automation.*
