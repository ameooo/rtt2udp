#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI管理器模块
负责用户界面的创建和管理
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
import queue
from device_selector import DeviceSelector

class QueueHandler(logging.Handler):
    """日志队列处理器"""
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)

class GUIManager:
    def __init__(self, root, config, on_start, on_stop):
        self.root = root
        self.config = config
        self.on_start = on_start
        self.on_stop = on_stop
        
        # 设置窗口
        self.root.title("RTT2UDP 转换器")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # 创建日志队列和处理器
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        self.queue_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # 配置日志记录器
        self.logger = logging.getLogger()
        self.logger.addHandler(self.queue_handler)
        
        # 创建UI组件
        self._create_ui()
        
        # 启动日志处理
        self._start_log_processing()
    
    def _create_ui(self):
        """创建用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建所有变量
        self._create_variables()
        
        # 配置区域
        self._create_config_section(main_frame)
        
        # 控制按钮
        self._create_control_section(main_frame)
        
        # 日志区域
        self._create_log_section(main_frame)
    
    def _create_variables(self):
        """创建所有UI变量"""
        # JLink设备选择
        self.jlink_device_var = tk.StringVar()
        
        # 目标设备
        self.target_device_var = tk.StringVar(value=self.config.target_device)
        
        # 调试接口
        self.debug_interface_var = tk.StringVar(value=self.config.debug_interface)
        
        # 调试速度
        self.debug_speed_var = tk.StringVar(value=self.config.debug_speed)
        
        # RTT配置
        self.buffer_index_var = tk.IntVar(value=self.config.rtt_buffer_index)
        self.rtt_mode_var = tk.StringVar(
            value="auto" if self.config.rtt_ctrl_block_addr == 0 else "manual"
        )
        self.rtt_addr_var = tk.StringVar(
            value=f"0x{self.config.rtt_ctrl_block_addr:X}" if self.config.rtt_ctrl_block_addr else ""
        )
        self.rtt_search_start_var = tk.StringVar(
            value=f"0x{self.config.rtt_search_start:X}"
        )
        self.rtt_search_length_var = tk.StringVar(
            value=f"0x{self.config.rtt_search_length:X}"
        )
        self.rtt_search_step_var = tk.IntVar(value=self.config.rtt_search_step)
        
        # UDP配置
        self.udp_ip_var = tk.StringVar(value=self.config.udp_ip)
        self.udp_port_var = tk.IntVar(value=self.config.udp_port)
        self.local_port_var = tk.IntVar(value=self.config.local_port)
        
        # 其他配置
        self.polling_interval_var = tk.DoubleVar(value=self.config.polling_interval)
        self.debug_var = tk.BooleanVar(value=self.config.debug)
        self.auto_save_var = tk.BooleanVar(value=self.config.auto_save)
        
        # 状态
        self.status_var = tk.StringVar(value="就绪")
    
    def _create_config_section(self, parent):
        """创建配置区域"""
        config_frame = ttk.LabelFrame(parent, text="配置", padding="10")
        config_frame.pack(fill=tk.X, pady=5)
        
        # JLink设备选择
        self._create_jlink_config(config_frame)
        
        # RTT配置
        self._create_rtt_config(config_frame)
        
        # UDP配置
        self._create_udp_config(config_frame)
        
        # 其他选项
        self._create_other_options(config_frame)
    
    def _create_jlink_config(self, parent):
        """创建JLink配置区域"""
        jlink_frame = ttk.LabelFrame(parent, text="JLink配置", padding="5")
        jlink_frame.pack(fill=tk.X, pady=5)
        
        # JLink设备选择
        device_frame = ttk.Frame(jlink_frame)
        device_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(device_frame, text="JLink设备:").pack(side=tk.LEFT)
        self.jlink_device_combo = ttk.Combobox(
            device_frame, 
            textvariable=self.jlink_device_var,
            state="readonly",
            width=30
        )
        self.jlink_device_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            device_frame,
            text="刷新",
            command=self._refresh_jlink_devices
        ).pack(side=tk.LEFT)
        
        # 目标设备
        target_frame = ttk.Frame(jlink_frame)
        target_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(target_frame, text="目标设备:").pack(side=tk.LEFT)
        ttk.Entry(
            target_frame,
            textvariable=self.target_device_var,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            target_frame,
            text="选择设备",
            command=self._select_target_device
        ).pack(side=tk.LEFT)
        
        # 调试接口和速度
        debug_frame = ttk.Frame(jlink_frame)
        debug_frame.pack(fill=tk.X, pady=2)
        
        # 调试接口
        interface_frame = ttk.Frame(debug_frame)
        interface_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(interface_frame, text="调试接口:").pack(side=tk.LEFT)
        ttk.Radiobutton(
            interface_frame,
            text="SWD",
            variable=self.debug_interface_var,
            value="SWD",
            command=self._on_config_change
        ).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(
            interface_frame,
            text="JTAG",
            variable=self.debug_interface_var,
            value="JTAG",
            command=self._on_config_change
        ).pack(side=tk.LEFT, padx=2)
        
        # 调试速度
        speed_frame = ttk.Frame(debug_frame)
        speed_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(speed_frame, text="调试速度:").pack(side=tk.LEFT)
        speed_values = [
            "auto", "adaptive",
            50000, 33000, 25000, 20000, 10000,
            5000, 3000, 2000, 1000, 500,
            200, 100, 50, 20, 10, 5
        ]
        ttk.OptionMenu(
            speed_frame,
            self.debug_speed_var,
            self.config.debug_speed,
            *speed_values,
            command=lambda _: self._on_config_change()
        ).pack(side=tk.LEFT, padx=5)
        ttk.Label(speed_frame, text="kHz").pack(side=tk.LEFT)
    
    def _create_rtt_config(self, parent):
        """创建RTT配置区域"""
        rtt_frame = ttk.LabelFrame(parent, text="RTT配置", padding="5")
        rtt_frame.pack(fill=tk.X, pady=5)
        
        # RTT基本配置
        basic_frame = ttk.Frame(rtt_frame)
        basic_frame.pack(fill=tk.X, pady=2)
        
        # 缓冲区索引
        ttk.Label(basic_frame, text="缓冲区索引:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(
            basic_frame,
            from_=0,
            to=10,
            textvariable=self.buffer_index_var,
            width=5,
            command=self._on_config_change
        ).pack(side=tk.LEFT, padx=5)
        
        # 控制块模式
        ttk.Label(basic_frame, text="控制块模式:").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            basic_frame,
            text="自动",
            variable=self.rtt_mode_var,
            value="auto",
            command=self._on_rtt_mode_change
        ).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(
            basic_frame,
            text="手动",
            variable=self.rtt_mode_var,
            value="manual",
            command=self._on_rtt_mode_change
        ).pack(side=tk.LEFT, padx=2)
        
        # 手动设置模式配置
        self.manual_frame = ttk.Frame(rtt_frame)
        self.manual_frame.pack(fill=tk.X, pady=2)
        ttk.Label(self.manual_frame, text="控制块地址:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(
            self.manual_frame,
            textvariable=self.rtt_addr_var,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        self.rtt_addr_var.trace_add("write", self._on_config_change)
        
        # 搜索模式配置
        self.search_frame = ttk.Frame(rtt_frame)
        self.search_frame.pack(fill=tk.X, pady=2)
        
        # 搜索起始地址
        start_frame = ttk.Frame(self.search_frame)
        start_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(start_frame, text="起始地址:").pack(side=tk.LEFT)
        ttk.Entry(
            start_frame,
            textvariable=self.rtt_search_start_var,
            width=10
        ).pack(side=tk.LEFT, padx=2)
        
        # 搜索长度
        length_frame = ttk.Frame(self.search_frame)
        length_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(length_frame, text="搜索长度:").pack(side=tk.LEFT)
        ttk.Entry(
            length_frame,
            textvariable=self.rtt_search_length_var,
            width=10
        ).pack(side=tk.LEFT, padx=2)
        
        # 根据当前模式显示/隐藏相应的框架
        self._on_rtt_mode_change()
    
    def _create_udp_config(self, parent):
        """创建UDP配置区域"""
        udp_frame = ttk.LabelFrame(parent, text="UDP配置", padding="5")
        udp_frame.pack(fill=tk.X, pady=5)
        
        # 目标IP和端口
        target_frame = ttk.Frame(udp_frame)
        target_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(target_frame, text="目标IP:").pack(side=tk.LEFT)
        ttk.Entry(
            target_frame,
            textvariable=self.udp_ip_var,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(target_frame, text="目标端口:").pack(side=tk.LEFT)
        ttk.Entry(
            target_frame,
            textvariable=self.udp_port_var,
            width=6
        ).pack(side=tk.LEFT, padx=5)
        
        # 本地端口
        local_frame = ttk.Frame(udp_frame)
        local_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(local_frame, text="本地端口:").pack(side=tk.LEFT)
        ttk.Entry(
            local_frame,
            textvariable=self.local_port_var,
            width=6
        ).pack(side=tk.LEFT, padx=5)
        ttk.Label(local_frame, text="(0表示自动分配)").pack(side=tk.LEFT)
    
    def _create_other_options(self, parent):
        """创建其他选项区域"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        # 轮询间隔
        ttk.Label(frame, text="轮询间隔(秒):").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(
            frame,
            from_=0.001,
            to=1.0,
            increment=0.01,
            textvariable=self.polling_interval_var,
            width=5
        ).pack(side=tk.LEFT, padx=5)
        
        # 调试模式
        ttk.Checkbutton(
            frame,
            text="调试模式",
            variable=self.debug_var
        ).pack(side=tk.LEFT, padx=5)
        
        # 自动保存
        ttk.Checkbutton(
            frame,
            text="自动保存配置",
            variable=self.auto_save_var
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_control_section(self, parent):
        """创建控制按钮区域"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=10)
        
        # 启动按钮
        self.start_button = ttk.Button(
            control_frame,
            text="启动",
            command=self._on_start_click
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # 停止按钮
        self.stop_button = ttk.Button(
            control_frame,
            text="停止",
            command=self._on_stop_click,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 状态显示
        ttk.Label(control_frame, text="状态:").pack(side=tk.RIGHT)
        ttk.Label(
            control_frame,
            textvariable=self.status_var
        ).pack(side=tk.RIGHT, padx=5)
    
    def _create_log_section(self, parent):
        """创建日志区域"""
        log_frame = ttk.LabelFrame(parent, text="日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
    
    def _start_log_processing(self):
        """启动日志处理"""
        self.log_thread_running = True
        self.root.after(100, self._process_logs)
    
    def _process_logs(self):
        """处理日志队列"""
        while True:
            try:
                record = self.log_queue.get_nowait()
                self._display_log(record)
            except queue.Empty:
                break
        
        if self.log_thread_running:
            self.root.after(100, self._process_logs)
    
    def _display_log(self, record):
        """显示日志记录"""
        msg = self.queue_handler.format(record)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # 设置日志颜色
        tag = "normal"
        if record.levelno >= logging.ERROR:
            tag = "error"
        elif record.levelno >= logging.WARNING:
            tag = "warning"
        elif record.levelno >= logging.INFO:
            tag = "info"
        
        self.log_text.tag_add(tag, "end-{}c linestart".format(len(msg) + 1), "end-1c")
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("warning", foreground="orange")
        self.log_text.tag_config("info", foreground="blue")
    
    def _refresh_jlink_devices(self):
        """刷新JLink设备列表"""
        import pylink
        try:
            jlink = pylink.JLink()
            devices = jlink.connected_emulators()
            jlink.close()
            
            if devices:
                device_list = [
                    f"{dev.acProduct} (S/N: {dev.SerialNumber})"
                    for dev in devices
                ]
                self.jlink_device_combo['values'] = device_list
                self.jlink_device_combo.current(0)
                self.logger.info(f"找到 {len(devices)} 个JLink设备")
            else:
                self.jlink_device_combo['values'] = ["未找到JLink设备"]
                self.jlink_device_combo.current(0)
                self.logger.warning("未找到JLink设备，请连接JLink并刷新")
        except Exception as e:
            self.logger.error(f"刷新JLink设备列表失败: {str(e)}")
            self.jlink_device_combo['values'] = ["刷新失败"]
            self.jlink_device_combo.current(0)
    
    def _on_config_change(self, *args):
        """配置更改回调"""
        self._update_config()
        if self.config.auto_save:
            if hasattr(self.config, 'save_config'):
                self.config.save_config()
    
    def _on_rtt_mode_change(self):
        """RTT模式更改回调"""
        mode = self.rtt_mode_var.get()
        if mode == "manual":
            self.manual_frame.pack(fill=tk.X, pady=2)
            self.search_frame.pack_forget()
        else:
            self.manual_frame.pack_forget()
            self.search_frame.pack(fill=tk.X, pady=2)
        
        self._on_config_change()
    
    def _update_config(self):
        """从UI更新配置"""
        try:
            self.config.target_device = self.target_device_var.get()
            self.config.debug_interface = self.debug_interface_var.get()
            self.config.debug_speed = self.debug_speed_var.get()
            self.config.rtt_buffer_index = self.buffer_index_var.get()
            
            # 更新RTT控制块配置
            if self.rtt_mode_var.get() == "manual":
                try:
                    addr = self.rtt_addr_var.get()
                    if addr.startswith("0x"):
                        self.config.rtt_ctrl_block_addr = int(addr, 16)
                    else:
                        self.config.rtt_ctrl_block_addr = int(addr)
                except:
                    self.config.rtt_ctrl_block_addr = 0
            else:
                self.config.rtt_ctrl_block_addr = 0
            
            # 更新RTT搜索配置
            try:
                start = self.rtt_search_start_var.get()
                if start.startswith("0x"):
                    self.config.rtt_search_start = int(start, 16)
                else:
                    self.config.rtt_search_start = int(start)
            except:
                pass
            
            try:
                length = self.rtt_search_length_var.get()
                if length.startswith("0x"):
                    self.config.rtt_search_length = int(length, 16)
                else:
                    self.config.rtt_search_length = int(length)
            except:
                pass
            
            self.config.rtt_search_step = self.rtt_search_step_var.get()
            
            # 更新UDP配置
            self.config.udp_ip = self.udp_ip_var.get()
            self.config.udp_port = self.udp_port_var.get()
            self.config.local_port = self.local_port_var.get()
            
            # 更新其他配置
            self.config.polling_interval = self.polling_interval_var.get()
            self.config.debug = self.debug_var.get()
            self.config.auto_save = self.auto_save_var.get()
            
            # 保存配置
            if hasattr(self.config, 'save') and self.config.auto_save:
                self.config.save()
        except Exception as e:
            self.logger.error(f"更新配置失败: {str(e)}")
    
    def _on_start_click(self):
        """启动按钮点击回调"""
        self._update_config()
        if self.on_start():
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_var.set("运行中")
    
    def _on_stop_click(self):
        """停止按钮点击回调"""
        if self.on_stop():
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_var.set("已停止")
    
    def get_selected_jlink_serial(self):
        """获取选中的JLink序列号"""
        device = self.jlink_device_var.get()
        if "未找到" in device or "刷新失败" in device:
            return None
        return device.split("S/N: ")[1].split(")")[0]
    
    def show_error(self, message):
        """显示错误对话框"""
        messagebox.showerror("错误", message)
    
    def on_closing(self):
        """窗口关闭回调"""
        if self.stop_button['state'] == tk.NORMAL:
            if messagebox.askokcancel("退出", "转发服务正在运行，确定要退出吗？"):
                self._on_stop_click()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def _select_target_device(self):
        """选择目标设备"""
        from device_selector import DeviceSelector
        device = DeviceSelector.show_dialog(self.root, self.logger)
        if device:
            self.target_device_var.set(device)
            self.config.target_device = device
            self.logger.info(f"已选择目标设备: {device}")
