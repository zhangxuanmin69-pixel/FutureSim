"""
FutureSim 实验管理模块（成员 C / API Gateway）
独立于 MiroFish 核心逻辑；仅依赖 flask / flask-cors / python-dotenv。
"""
from .routes import futuresim_bp, register_error_handlers

__all__ = ['futuresim_bp', 'register_error_handlers']