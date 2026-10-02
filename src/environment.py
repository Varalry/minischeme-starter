"""环境：变量绑定表 + 指向外层环境的指针（词法作用域的关键）。

查找变量时沿父链一路向外，这就是闭包能"记住定义时环境"的原因。
"""

from errors import SchemeError


class Environment:
    __slots__ = ("bindings", "parent")

    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent

    def define(self, name, value):
        """在当前层绑定名字（define / 形参绑定都走这里）。"""
        self.bindings[name] = value

    def lookup(self, name):
        """沿环境链查找变量；找不到则报错。"""
        env = self
        while env is not None:
            if name in env.bindings:
                return env.bindings[name]
            env = env.parent
        raise SchemeError(f"未定义的符号：{name}")
