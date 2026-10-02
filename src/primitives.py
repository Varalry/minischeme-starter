"""内置过程库：spec §5 的全部内置函数，安装进初始全局环境。

每个内置过程是一个 Builtin(name, fn)，fn 接收"已求值实参的 Python 列表"。
实参先全部求值再调用（应用序），这一步在 evaluator.apply 完成。
"""

import sys

from values import (
    Symbol, Pair, nil, Builtin, is_procedure,
    list_to_pairs, pairs_to_list,
)
from errors import SchemeError


def _fail(msg):
    raise SchemeError(msg)


def _require_number(x, who):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        _fail(f"{who} 的参数必须是数字，得到：{x!r}")
    return x


def _require_pair(x, who):
    if not isinstance(x, Pair):
        _fail(f"{who} 的参数必须是点对，得到：{x!r}")
    return x


def _check_arity(args, lo, hi, who):
    """检查实参个数在 [lo, hi] 区间；hi 为 None 表示不设上限。"""
    if len(args) < lo or (hi is not None and len(args) > hi):
        _fail(f"{who} 的参数个数不对：期望 {lo}" + ("" if hi is None and lo == hi else "+") + f"，得到 {len(args)}")


# ---------- 算术 ----------

def _trunc_div(a, b):
    """整数相除，商向零截断（spec：(/ -7 2) → -3，而不是 Python 的 -4）。"""
    if b == 0:
        _fail("除数为 0")
    q = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        q = -q
    return q


def _add(args):
    total = 0
    for x in args:
        total += _require_number(x, "+")
    return total


def _sub(args):
    _check_arity(args, 1, None, "-")
    nums = [_require_number(x, "-") for x in args]
    if len(nums) == 1:
        return -nums[0]  # 单参数取反
    result = nums[0]
    for x in nums[1:]:
        result -= x
    return result


def _mul(args):
    result = 1
    for x in args:
        result *= _require_number(x, "*")
    return result


def _div(args):
    _check_arity(args, 1, None, "/")
    nums = [_require_number(x, "/") for x in args]
    if len(nums) == 1:
        return 1.0 / nums[0]  # 单参数求倒数，结果是浮点（spec §5）
    result = nums[0]
    for x in nums[1:]:
        if isinstance(result, int) and isinstance(x, int):
            result = _trunc_div(result, x)  # 整数相除得整数商，向零截断
        else:
            if x == 0:
                _fail("除数为 0")
            result = result / x
    return result


def _modulo(args):
    _check_arity(args, 2, 2, "modulo")
    a, b = (_require_number(x, "modulo") for x in args)
    if b == 0:
        _fail("除数为 0")
    return a % b


def _quotient(args):
    _check_arity(args, 2, 2, "quotient")
    a, b = (_require_number(x, "quotient") for x in args)
    return _trunc_div(a, b)


def _expt(args):
    _check_arity(args, 2, 2, "expt")
    base, exp = (_require_number(x, "expt") for x in args)
    return base ** exp


def _abs(args):
    _check_arity(args, 1, 1, "abs")
    return abs(_require_number(args[0], "abs"))


# ---------- 比较（链式：相邻两两都成立才为真；支持数字与符号） ----------

def _make_comparison(op, name):
    def compare(args):
        for a, b in zip(args, args[1:]):
            if not op(a, b):
                return False
        return True
    compare.__name__ = name
    return compare


# ---------- 列表 ----------

def _cons(args):
    _check_arity(args, 2, 2, "cons")
    return Pair(args[0], args[1])


def _car(args):
    _check_arity(args, 1, 1, "car")
    return _require_pair(args[0], "car").car


def _cdr(args):
    _check_arity(args, 1, 1, "cdr")
    return _require_pair(args[0], "cdr").cdr


def _list(args):
    return list_to_pairs(args)


def _length(args):
    _check_arity(args, 1, 1, "length")
    return len(pairs_to_list(args[0]))


def _append(args):
    # 拼接若干列表：前面的列表必须是真列表，最后一个可以是任意值
    result = args[-1] if args else nil
    for lst in reversed(args[:-1]):
        result = list_to_pairs(pairs_to_list(lst), result)
    return result


def _nullp(args):
    _check_arity(args, 1, 1, "null?")
    return args[0] is nil


def _pairp(args):
    _check_arity(args, 1, 1, "pair?")
    return isinstance(args[0], Pair)


def _listp(args):
    _check_arity(args, 1, 1, "list?")
    current = args[0]
    while isinstance(current, Pair):
        current = current.cdr
    return current is nil


# ---------- 谓词 ----------

def _not(args):
    _check_arity(args, 1, 1, "not")
    return args[0] is False  # 只有 #f 是假


def _numberp(args):
    _check_arity(args, 1, 1, "number?")
    # 布尔不是数字（Python 里 bool 是 int 子类，需排除）
    return isinstance(args[0], (int, float)) and not isinstance(args[0], bool)


def _booleanp(args):
    _check_arity(args, 1, 1, "boolean?")
    return isinstance(args[0], bool)


def _symbolp(args):
    _check_arity(args, 1, 1, "symbol?")
    return isinstance(args[0], Symbol)


def _stringp(args):
    _check_arity(args, 1, 1, "string?")
    return isinstance(args[0], str) and not isinstance(args[0], Symbol)


def _procedurep(args):
    _check_arity(args, 1, 1, "procedure?")
    return is_procedure(args[0])


def _zerop(args):
    _check_arity(args, 1, 1, "zero?")
    return _require_number(args[0], "zero?") == 0


def _evenp(args):
    _check_arity(args, 1, 1, "even?")
    return _require_number(args[0], "even?") % 2 == 0


def _oddp(args):
    _check_arity(args, 1, 1, "odd?")
    return _require_number(args[0], "odd?") % 2 != 0


def _eqp(args):
    """eq?：符号/数字/布尔/字符串按值比较；复合数据（点对）按同一性。"""
    _check_arity(args, 2, 2, "eq?")
    a, b = args
    if a is nil or b is nil:
        return a is b  # 空表全局唯一，(eq? '() '()) → #t
    if isinstance(a, Pair) or isinstance(b, Pair):
        return a is b  # 复合数据比同一性：(eq? '(1) '(1)) → #f
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b  # #t 不等于 1
    if isinstance(a, Symbol) != isinstance(b, Symbol):
        return False  # 符号与字符串是不同的类型
    return a == b


def _equalp(args):
    """equal?：结构相等，逐层比较（先比类型再比值）。"""
    _check_arity(args, 2, 2, "equal?")
    return _deep_equal(args[0], args[1])


def _deep_equal(a, b):
    if a is nil or b is nil:
        return a is b
    if isinstance(a, Pair) and isinstance(b, Pair):
        return _deep_equal(a.car, b.car) and _deep_equal(a.cdr, b.cdr)
    if isinstance(a, Pair) or isinstance(b, Pair):
        return False
    # 类型必须一致：bool≠int（True != 1），Symbol≠str（'a != "a"）
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if isinstance(a, Symbol) != isinstance(b, Symbol):
        return False
    if isinstance(a, float) != isinstance(b, float) and isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b  # 1 与 1.0 视为相等（数值相等）
    return a == b


# ---------- 输出 ----------

def _display(args):
    _check_arity(args, 1, 1, "display")
    from printer import display_string  # 延迟导入避免循环依赖
    sys.stdout.write(display_string(args[0]))
    sys.stdout.flush()
    return None  # 无值：顶层不打印


def _newline(args):
    _check_arity(args, 0, 0, "newline")
    sys.stdout.write("\n")
    sys.stdout.flush()
    return None


def install_builtins(env):
    """把全部内置过程装进给定的（全局）环境。"""
    import operator
    table = {
        # 算术
        "+": _add, "-": _sub, "*": _mul, "/": _div,
        "modulo": _modulo, "quotient": _quotient, "expt": _expt, "abs": _abs,
        # 比较（链式）
        "=": _make_comparison(operator.eq, "="),
        "<": _make_comparison(operator.lt, "<"),
        ">": _make_comparison(operator.gt, ">"),
        "<=": _make_comparison(operator.le, "<="),
        ">=": _make_comparison(operator.ge, ">="),
        # 布尔
        "not": _not,
        # 列表
        "cons": _cons, "car": _car, "cdr": _cdr, "list": _list,
        "length": _length, "append": _append,
        "null?": _nullp, "pair?": _pairp, "list?": _listp,
        # 谓词
        "number?": _numberp, "boolean?": _booleanp, "symbol?": _symbolp,
        "string?": _stringp, "procedure?": _procedurep,
        "zero?": _zerop, "even?": _evenp, "odd?": _oddp,
        "eq?": _eqp, "equal?": _equalp,
        # 输出
        "display": _display, "newline": _newline,
    }
    for name, fn in table.items():
        env.define(Symbol(name), Builtin(name, fn))
    return env
