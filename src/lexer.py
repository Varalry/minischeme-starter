"""词法分析：程序文本 → token 列表。

token 用带类别的小元组或直接的字面值对象表示：
  "(" ")" "'" "."   —— 标点，用字符串本身表示
  True / False      —— 布尔 #t / #f
  int / float       —— 数字
  StringToken       —— 字符串（包装类，与符号区分）
  Symbol            —— 符号

注释（; 到行尾）与空白在这里被丢弃。
"""

from values import Symbol
from errors import SchemeError


class StringToken(str):
    """尚未求值的字符串字面量 token，仅词法/语法阶段使用。"""
    __slots__ = ()


# 字符串转义表
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _is_delimiter(ch):
    """token 的结束字符：空白、括号、引号、注释起始。"""
    return ch in " \t\r\n()';"


def _read_string(text, i):
    """从 text[i] == '"' 处读一个字符串字面量，返回 (StringToken, 下一个下标)。"""
    buf = []
    i += 1  # 跳过开引号
    while i < len(text):
        ch = text[i]
        if ch == '"':
            return StringToken("".join(buf)), i + 1
        if ch == "\\":
            i += 1
            if i >= len(text):
                raise SchemeError("字符串在转义符处意外结束")
            esc = text[i]
            if esc not in _ESCAPES:
                raise SchemeError(f"不支持的转义序列：\\{esc}")
            buf.append(_ESCAPES[esc])
        else:
            buf.append(ch)
        i += 1
    raise SchemeError("字符串缺少结束引号")


def _read_atom(text, i):
    """读一个原子 token（数字 / 布尔 / 符号），返回 (token, 下一个下标)。"""
    j = i
    while j < len(text) and not _is_delimiter(text[j]) and text[j] != '"':
        j += 1
    word = text[i:j]

    if word == "#t":
        return True, j
    if word == "#f":
        return False, j

    # 数字：可选负号 + 数字，可选小数部分。注意 "-" 单独出现是符号（减法）。
    try:
        if any(c == "." for c in word) and word not in (".", "-"):
            return float(word), j
        return int(word), j
    except ValueError:
        pass

    return Symbol(word), j


def tokenize(text):
    """把整段程序文本切成 token 列表。"""
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in " \t\r\n":
            i += 1
        elif ch == ";":  # 注释到行尾
            while i < n and text[i] != "\n":
                i += 1
        elif ch in "()'":
            tokens.append(ch)
            i += 1
        elif ch == '"':
            tok, i = _read_string(text, i)
            tokens.append(tok)
        else:
            tok, i = _read_atom(text, i)
            tokens.append(tok)
    return tokens
