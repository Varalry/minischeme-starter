"""值表示：mini-Scheme 运行时使用的数据类型。

- 整数/浮点直接用 Python 的 int / float
- 布尔用 Python 的 True / False（打印时转成 #t / #f）
- 字符串用 Python 的 str
- 符号用 Symbol（str 的子类），从而能与字符串区分：
  spec 要求 (equal? 'a "a") 为 #f，若符号直接是 str 就会误判相等
- 列表/点对用 Pair 链；空表是全局唯一的 nil
- 过程分为 Builtin（Python 实现的内置过程）与 Closure（lambda 闭包）
"""


class Symbol(str):
    """Scheme 符号。是 str 的子类，便于打印与比较，但类型上与字符串区分。"""
    __slots__ = ()

    def __repr__(self):
        return f"Symbol({str.__repr__(self)})"


# 一些常用符号常量，避免到处重复构造
SYM_QUOTE = Symbol("quote")
SYM_IF = Symbol("if")
SYM_COND = Symbol("cond")
SYM_AND = Symbol("and")
SYM_OR = Symbol("or")
SYM_DEFINE = Symbol("define")
SYM_LAMBDA = Symbol("lambda")
SYM_LET = Symbol("let")
SYM_BEGIN = Symbol("begin")
SYM_ELSE = Symbol("else")

SPECIAL_FORMS = frozenset({
    SYM_QUOTE, SYM_IF, SYM_COND, SYM_AND, SYM_OR,
    SYM_DEFINE, SYM_LAMBDA, SYM_LET, SYM_BEGIN,
})


class Nil:
    """空表 ()，全局唯一实例（见下方 nil）。"""
    __slots__ = ()
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "nil"


nil = Nil()


class Pair:
    """点对：(car . cdr)。列表就是 cdr 逐层指向下一节点的 Pair 链。"""
    __slots__ = ("car", "cdr")

    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr

    def __repr__(self):
        return f"Pair({self.car!r}, {self.cdr!r})"


def list_to_pairs(items, tail=nil):
    """把 Python 序列转成 Pair 链；tail 是链的末端（默认空表）。"""
    result = tail
    for item in reversed(items):
        result = Pair(item, result)
    return result


def pairs_to_list(pair):
    """把真列表（cdr 终点为 nil 的 Pair 链）转成 Python 列表。

    若链的终点不是空表（即非真列表），抛出 SchemeError 由上层转为报错。
    """
    from errors import SchemeError  # 延迟导入避免循环依赖
    result = []
    while isinstance(pair, Pair):
        result.append(pair.car)
        pair = pair.cdr
    if pair is not nil:
        raise SchemeError("参数不是真列表（无法展开为元素序列）")
    return result


class Builtin:
    """内置过程：包装一个 Python 函数。fn 接收实参的 Python 列表。"""
    __slots__ = ("name", "fn")

    def __init__(self, name, fn):
        self.name = name
        self.fn = fn

    def __repr__(self):
        return f"<builtin {self.name}>"


class Closure:
    """用户函数：lambda 求值得到的闭包，记住定义时的环境（词法作用域）。"""
    __slots__ = ("params", "body", "env")

    def __init__(self, params, body, env):
        self.params = params    # 形参 Symbol 列表
        self.body = body        # 函数体表达式列表（begin 语义）
        self.env = env          # 定义时环境

    def __repr__(self):
        return f"<closure {self.params}>"


def is_procedure(value):
    """谓词 procedure? 的判断逻辑：内置过程或闭包。"""
    return isinstance(value, (Builtin, Closure))
