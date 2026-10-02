"""打印：值 → 文本。

- to_string：顶层求值结果的打印形式（字符串带引号、转义可见），对应 spec §8
- display_string：display 的输出形式（字符串不带引号、不转义）
"""

from values import Symbol, Pair, nil, is_procedure


def _escape(text):
    """把字符串转成带引号的字面量形式：换行/制表符等打印为转义序列。"""
    out = ['"']
    for ch in text:
        if ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def to_string(value):
    """值的规范打印形式（spec §8）。"""
    # 布尔必须先于数字判断：Python 里 True/False 是 int 的子类
    if value is True:
        return "#t"
    if value is False:
        return "#f"
    if value is nil:
        return "()"
    if isinstance(value, Pair):
        return _pair_to_string(value)
    if isinstance(value, Symbol):
        return str(value)  # Symbol 先于 str 判断（Symbol 是 str 子类）
    if isinstance(value, str):
        return _escape(value)
    if is_procedure(value):
        return "#<procedure>"
    if isinstance(value, float):
        return _float_to_string(value)
    if isinstance(value, int):
        return str(value)
    return str(value)


def _float_to_string(value):
    """浮点打印：0.5 → "0.5"；整数值的浮点也保持简单形式。"""
    text = repr(value)
    return text


def _pair_to_string(pair):
    """打印 Pair 链：真列表打成 (1 2 3)，非真列表打成 (1 . 2)。"""
    parts = []
    current = pair
    while isinstance(current, Pair):
        parts.append(to_string(current.car))
        current = current.cdr
    if current is nil:
        return "(" + " ".join(parts) + ")"
    # 非真列表：最后补 ". cdr"
    parts.append(".")
    parts.append(to_string(current))
    return "(" + " ".join(parts) + ")"


def display_string(value):
    """display 的输出形式：字符串不带引号，其余与 to_string 一致。"""
    if isinstance(value, str) and not isinstance(value, Symbol):
        return value
    return to_string(value)
