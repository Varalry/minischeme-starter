"""求值器：解释器的心脏，evaluate 与 apply 互相递归。

- evaluate(expr, env)：求值一个表达式
  原子（数字/布尔/字符串/空表）→ 原样返回
  符号 → 去环境查值
  Pair → 特殊形式按 spec §4 各自规则处理，其余按函数调用：
         先求值操作符和全部实参（应用序），再交给 apply
- apply(proc, args)：调用一个过程
  Builtin → 直接调 Python 函数
  Closure → 新建一层环境（外层指向闭包定义时的环境），绑定形参后求值函数体

真值判断：只有 #f 是假，0、()、"" 均为真（spec §9）。
"""

from values import (
    Symbol, Pair, nil, Closure, Builtin,
    pairs_to_list,
    SPECIAL_FORMS, SYM_QUOTE, SYM_IF, SYM_COND, SYM_AND, SYM_OR,
    SYM_DEFINE, SYM_LAMBDA, SYM_LET, SYM_BEGIN, SYM_ELSE,
)
from environment import Environment
from errors import SchemeError


def is_true(value):
    """mini-Scheme 的真值判断：只有 #f 为假。"""
    return value is not False


def evaluate(expr, env):
    """求值一个表达式，返回它的值。"""
    # 原子：自求值（bool 先于 int 判断无妨，bool 本身就是值）
    if isinstance(expr, (int, float, bool)) or expr is nil:
        return expr
    if isinstance(expr, Symbol):
        return env.lookup(expr)
    if isinstance(expr, str):
        return expr  # 字符串字面量（Symbol 已在上面先行返回）
    if not isinstance(expr, Pair):
        raise SchemeError(f"无法求值的表达式：{expr!r}")

    items = pairs_to_list(expr)
    head = items[0]

    # 特殊形式：每种有自己独立的求值顺序（spec §4）
    if isinstance(head, Symbol) and head in SPECIAL_FORMS:
        if head == SYM_QUOTE:
            return items[1]
        if head == SYM_IF:
            return _eval_if(items[1:], env)
        if head == SYM_COND:
            return _eval_cond(items[1:], env)
        if head == SYM_AND:
            return _eval_and(items[1:], env)
        if head == SYM_OR:
            return _eval_or(items[1:], env)
        if head == SYM_DEFINE:
            return _eval_define(items[1:], env)
        if head == SYM_LAMBDA:
            return _eval_lambda(items[1:], env)
        if head == SYM_LET:
            return _eval_let(items[1:], env)
        if head == SYM_BEGIN:
            return _eval_sequence(items[1:], env)

    # 函数调用：先求值操作符和全部实参（应用序），再 apply
    proc = evaluate(head, env)
    args = [evaluate(a, env) for a in items[1:]]
    return apply(proc, args)


def _eval_sequence(body, env):
    """按 begin 语义依次求值，返回最后一个的结果；空体返回 None。"""
    result = None
    for sub in body:
        result = evaluate(sub, env)
    return result


def _eval_if(items, env):
    """(if 测试 真分支 假分支?)：先求值测试，只求值被选中的分支。"""
    if len(items) not in (2, 3):
        raise SchemeError("if 需要 2 或 3 个参数")
    if is_true(evaluate(items[0], env)):
        return evaluate(items[1], env)
    if len(items) == 3:
        return evaluate(items[2], env)
    return None  # 无假分支且测试为 #f：结果无值（顶层不打印）


def _eval_cond(clauses, env):
    """(cond (测试 表达式...) ... (else 表达式...))：自上而下取首个为真的分支。"""
    for clause in clauses:
        parts = pairs_to_list(clause)
        test_expr, body = parts[0], parts[1:]
        if test_expr == SYM_ELSE:
            return _eval_sequence(body, env) if body else True
        test_value = evaluate(test_expr, env)
        if is_true(test_value):
            # 子句没有表达式时，返回测试值本身（spec §4.3）
            return _eval_sequence(body, env) if body else test_value
    return None  # 全部不匹配：结果无值


def _eval_and(args, env):
    """and 短路：遇第一个 #f 立即返回 #f；全真返回最后一个的值；(and) → #t。"""
    result = True
    for sub in args:
        result = evaluate(sub, env)
        if result is False:
            return False
    return result


def _eval_or(args, env):
    """or 短路：遇第一个非 #f 的值立即返回它；全假或 (or) → #f。"""
    for sub in args:
        result = evaluate(sub, env)
        if result is not False:
            return result
    return False


def _eval_define(items, env):
    """define 的两种形态：

    (define 名 表达式)          —— 先求值右侧，再在当前环境绑定；结果是符号名
    (define (名 参数...) 体...)  —— 函数简写，等价于 (define 名 (lambda ...))
    """
    target = items[0]
    if isinstance(target, Pair):
        sig = pairs_to_list(target)
        if not sig or not isinstance(sig[0], Symbol):
            raise SchemeError("define 的函数名必须是符号")
        name = sig[0]
        env.define(name, Closure(sig[1:], items[1:], env))
        return name
    if isinstance(target, Symbol):
        value = evaluate(items[1], env)
        env.define(target, value)
        return target
    raise SchemeError("define 的第一个参数必须是符号或 (函数名 参数...)")


def _eval_lambda(items, env):
    """(lambda (参数...) 体...)：制造闭包，记住定义时环境；函数体此时不求值。"""
    params = pairs_to_list(items[0])
    for p in params:
        if not isinstance(p, Symbol):
            raise SchemeError("lambda 的形参必须是符号")
    return Closure(params, items[1:], env)


def _eval_let(items, env):
    """(let ((名 表达式)...) 体...)：并行绑定——

    先把每个绑定表达式都在外层环境求值完（绑定之间互不可见），
    再在新环境里按 begin 语义求值函数体。
    """
    bindings = pairs_to_list(items[0])
    names, values = [], []
    for binding in bindings:
        pair = pairs_to_list(binding)
        if len(pair) != 2 or not isinstance(pair[0], Symbol):
            raise SchemeError("let 的绑定必须是 (名 表达式)")
        names.append(pair[0])
        values.append(evaluate(pair[1], env))  # 关键：都在外层 env 求值
    local = Environment(parent=env)
    for name, value in zip(names, values):
        local.define(name, value)
    return _eval_sequence(items[1:], local)


def apply(proc, args):
    """调用一个过程。args 是已求值实参的 Python 列表。"""
    if isinstance(proc, Builtin):
        return proc.fn(args)
    if isinstance(proc, Closure):
        if len(args) != len(proc.params):
            raise SchemeError(
                f"参数个数不对：期望 {len(proc.params)}，得到 {len(args)}")
        # 新环境的外层指向闭包定义时的环境（词法作用域）
        local = Environment(parent=proc.env)
        for name, value in zip(proc.params, args):
            local.define(name, value)
        return _eval_sequence(proc.body, local)
    raise SchemeError(f"尝试调用一个不是过程的值：{proc!r}")
