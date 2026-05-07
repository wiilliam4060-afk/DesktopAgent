# Desktop_Agent/core/event_bus.py

class EventBus:
    """轻量级事件总线，用于解耦各个子系统"""
    def __init__(self):
        # 字典结构：{ "事件名称": [回调函数1, 回调函数2, ...] }
        self._subscribers = {}

    def subscribe(self, event_type, callback):
        """订阅事件：当 event_type 发生时，执行 callback"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)

    def publish(self, event_type, data=None):
        """发布事件：触发所有订阅了 event_type 的回调函数"""
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                callback(data)