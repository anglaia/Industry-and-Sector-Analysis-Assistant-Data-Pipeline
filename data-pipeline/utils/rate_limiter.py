"""
频率限制器
防止过于频繁的请求
"""
import time
from collections import deque
from threading import Lock
from typing import Optional


class RateLimiter:
    """
    令牌桶算法实现的频率限制器
    
    Usage:
        limiter = RateLimiter(max_calls=10, period=60)  # 每60秒最多10次
        
        with limiter:
            # 进行 API 调用或网络请求
            response = requests.get(url)
    """
    
    def __init__(self, max_calls: int, period: float, delay: Optional[float] = None):
        """
        初始化频率限制器
        
        Args:
            max_calls: 时间段内允许的最大调用次数
            period: 时间段（秒）
            delay: 每次调用后的固定延迟（秒），可选
        """
        self.max_calls = max_calls
        self.period = period
        self.delay = delay
        self.calls = deque()
        self.lock = Lock()
    
    def __enter__(self):
        """上下文管理器入口"""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if self.delay:
            time.sleep(self.delay)
        return False
    
    def acquire(self):
        """
        获取执行权限，如果超过频率限制则等待
        """
        with self.lock:
            now = time.time()
            
            # 移除过期的调用记录
            while self.calls and self.calls[0] <= now - self.period:
                self.calls.popleft()
            
            # 如果达到限制，等待
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    # 重新清理过期记录
                    now = time.time()
                    while self.calls and self.calls[0] <= now - self.period:
                        self.calls.popleft()
            
            # 记录本次调用
            self.calls.append(time.time())
    
    def get_wait_time(self) -> float:
        """
        获取需要等待的时间（秒）
        
        Returns:
            需要等待的秒数，0 表示可以立即执行
        """
        with self.lock:
            now = time.time()
            
            # 移除过期的调用记录
            while self.calls and self.calls[0] <= now - self.period:
                self.calls.popleft()
            
            if len(self.calls) < self.max_calls:
                return 0.0
            
            return self.period - (now - self.calls[0])


class SimpleRateLimiter:
    """
    简单的固定延迟限制器
    
    Usage:
        limiter = SimpleRateLimiter(delay=2.0)  # 每次请求后延迟2秒
        
        with limiter:
            response = requests.get(url)
    """
    
    def __init__(self, delay: float):
        """
        初始化简单频率限制器
        
        Args:
            delay: 每次调用后的延迟（秒）
        """
        self.delay = delay
        self.last_call = 0
        self.lock = Lock()
    
    def __enter__(self):
        """上下文管理器入口"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_call
            
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
            
            self.last_call = time.time()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        return False

