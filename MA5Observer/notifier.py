# notifier.py
import platform
import os
import asyncio

# 同时引入 toast 和 toast_async
try:
    from win11toast import toast, toast_async
except ImportError:
    toast = None
    toast_async = None

class Notifier:
    """
    根据系统平台选择不同的通知方法:
      - Windows: win11toast (同步与异步)
      - MacOS:   通过 AppleScript (osascript) 发送系统通知
    """

    def __init__(self):
        self.system = platform.system().lower()  # 获取操作系统类型

    # ---------------------------
    # 同步版本发送通知
    # ---------------------------
    def send_notification(self, title, message, on_click=None):
        """
        根据操作系统不同，发送系统通知(同步):
         - Windows: 使用 win11toast.toast
         - MacOS:   调用 osascript 执行系统通知
        """
        if "windows" in self.system:
            self._win_notify(title, message, on_click)
        elif "darwin" in self.system:
            self._mac_notify(title, message)
        else:
            print(f"[INFO] 当前系统 {self.system} 暂未实现通知，可使用print替代。")
            print(f"[NOTIFY] {title} : {message}")

    def _win_notify(self, title, message, on_click=None):
        if toast is None:
            # 如果未安装 win11toast，则打印提示
            print("[WARN] win11toast 未安装 (同步模式)，无法发送Windows通知，改为print输出。")
            print(f"[NOTIFY] {title} : {message}")
        else:
            # 使用同步版本toast发送通知
            toast(title, message, on_click=on_click)

    def _mac_notify(self, title, message):
        """
        通过 AppleScript 的方式发送 Mac OS 通知。
        也可以用 pync 等第三方库，这里只演示系统自带命令。
        """
        # 注意转义特殊字符
        cmd = f"osascript -e 'display notification \"{message}\" with title \"{title}\"'"
        os.system(cmd)


# 以下为简单测试
if __name__ == '__main__':
    # 测试同步
    # print("[TEST] 测试同步通知...")
    notifier = Notifier()
    notifier.send_notification("同步通知标题", "同步通知内容")

    print("[INFO] 测试完成。")
