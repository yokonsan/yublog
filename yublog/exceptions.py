class NoCacheTypeException(Exception):
    """无此缓存类型异常"""


class DuplicateEntryException(Exception):
    """唯一性字段重复异常"""


class AppInitException(Exception):
    """应用初始化异常"""
