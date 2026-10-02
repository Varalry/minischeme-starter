"""入口：读文件/标准输入，逐个求值顶层表达式，逐行打印结果。

用法：
    python3 src/main.py file1.scm [file2.scm ...]   # 多个文件共享全局环境
    python3 src/main.py                              # 从标准输入读取

约定（spec §2）：每个求值结果独占一行；结果为 None（无值）时不打印。
"""

import sys
import os
import threading

# 让直接以 "python3 src/main.py" 运行时也能找到同级模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser import parse_program
from environment import Environment
from evaluator import evaluate
from primitives import install_builtins
from printer import to_string
from errors import SchemeError


def run_sources(sources):
    """按顺序求值每段源码的顶层表达式；多个文件共享同一个全局环境。"""
    global_env = install_builtins(Environment())
    for text in sources:
        for expr in parse_program(text):
            result = evaluate(expr, global_env)
            if result is not None:  # 无值结果（display/newline 等）不打印
                print(to_string(result))


def main():
    if len(sys.argv) > 1:
        sources = []
        for path in sys.argv[1:]:
            with open(path, "r", encoding="utf-8") as f:
                sources.append(f.read())
    else:
        sources = [sys.stdin.read()]
    try:
        run_sources(sources)
    except SchemeError as err:
        # spec 未定义出错行为；给出清晰的错误信息便于调试
        sys.stderr.write(f"错误：{err}\n")
        sys.exit(1)


def _guarded_main():
    """在线程中运行 main 并透传异常（配合下方的大栈设置）。"""
    try:
        main()
    except SystemExit:
        raise
    except BaseException as err:  # noqa: BLE001 —— 线程内错误透传到主线程
        _thread_error.append(err)


_thread_error = []

if __name__ == "__main__":
    # 深递归程序（如 fib、长列表上的递归 map）需要更深的栈：
    # 放大 Python 递归上限，并在大栈线程中运行，避免 C 栈溢出。
    # 不同平台允许的栈上限不同，逐级回退到可用值。
    sys.setrecursionlimit(200_000)
    for size in (256, 128, 64, 32, 16):
        try:
            threading.stack_size(size * 1024 * 1024)
            break
        except (ValueError, OverflowError):
            continue
    worker = threading.Thread(target=_guarded_main)
    worker.start()
    worker.join()
    if _thread_error:
        raise _thread_error[0]
