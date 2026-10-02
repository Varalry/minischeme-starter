"""语法分析：token 列表 → 表达式（嵌套数据结构）。

表达式直接就是运行时的数据表示：
- 原子：int / float / bool / str（字符串）/ Symbol（符号）/ nil（空表）
- 列表：Pair 链（与 quote/cons 的运行时表示一致，spec §6）

支持 'x 简写（展开为 (quote x)）与点号写法 (a . b)。
"""

from values import Symbol, Pair, nil, list_to_pairs, SYM_QUOTE
from lexer import StringToken
from errors import SchemeError


def _parse_expr(tokens, i):
    """解析一个表达式，返回 (表达式, 下一个 token 下标)。"""
    if i >= len(tokens):
        raise SchemeError("输入在表达式中途结束")

    tok = tokens[i]

    if tok == "(":
        return _parse_list(tokens, i + 1)
    if tok == ")":
        raise SchemeError("多余的右括号")
    if tok == "'":
        inner, j = _parse_expr(tokens, i + 1)
        return list_to_pairs([SYM_QUOTE, inner]), j

    # 原子：字符串 token 转成普通 str（与符号区分）；其余原样
    if isinstance(tok, StringToken):
        return str(tok), i + 1
    return tok, i + 1


def _parse_list(tokens, i):
    """解析 "(" 之后的列表内容直到 ")"，返回 (Pair 链, 下一个下标)。"""
    items = []
    tail = nil
    while True:
        if i >= len(tokens):
            raise SchemeError("缺少右括号")
        if tokens[i] == ")":
            return list_to_pairs(items, tail), i + 1
        # 点号写法：(a b . c)
        if tokens[i] == Symbol(".") or tokens[i] == ".":
            dotted, i = _parse_expr(tokens, i + 1)
            if i >= len(tokens) or tokens[i] != ")":
                raise SchemeError("点对写法后应紧跟右括号")
            tail = dotted
            return list_to_pairs(items, tail), i + 1
        expr, i = _parse_expr(tokens, i)
        items.append(expr)


def parse_program(text):
    """解析整段程序文本，返回顶层表达式列表。"""
    from lexer import tokenize
    tokens = tokenize(text)
    exprs = []
    i = 0
    while i < len(tokens):
        expr, i = _parse_expr(tokens, i)
        exprs.append(expr)
    return exprs
