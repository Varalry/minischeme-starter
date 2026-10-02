; 边角特性自测（期望输出写在每行注释里）
(and)                              ; → #t
(or)                               ; → #f
(/ -7 2)                           ; → -3   负数商向零截断
(quotient -7 2)                    ; → -3
(quotient 7 -2)                    ; → -3
(/ 2)                              ; → 0.5  单参数取倒数（浮点）
(modulo -7 2)                      ; → 1
(- 5)                              ; → -5
(if #f 'bad)                       ; → 无值，不打印
(cond (#f 'a) (#f))                ; → 无值，不打印（全部不匹配）
(cond ((< 1 2)))                   ; → #t   子句无表达式时返回测试值
(equal? #t 1)                      ; → #f   先比类型再比值
(equal? 'a "a")                    ; → #f   符号与字符串不同
(eq? '(1) '(1))                    ; → #f   复合数据比同一性
(eq? '() '())                      ; → #t
(eq? 'a 'a)                        ; → #t
(equal? '(1 2 3) (list 1 2 3))     ; → #t
(equal? '(1 (2 3)) '(1 (2 3)))     ; → #t   嵌套结构相等
(let ((a 1)) (let ((a 2) (b a)) (list a b)))  ; → (2 1)  let 并行绑定
(let ((x 3) (y 4)) (+ x y))        ; → 7
(begin (define z 1) (+ z 41))      ; → 42
(append '(1 2) '(3 4) '(5))        ; → (1 2 3 4 5)
(append)                           ; → ()
(append '(1 2) 3)                  ; → (1 2 . 3)  最后参数作为链尾
(not 0)                            ; → #f
(not '())                          ; → #f
(if '() 't 'f)                     ; → t    空表是真
(list? (cons 1 2))                 ; → #f
(list? '())                        ; → #t
(pair? '())                        ; → #f
(procedure? car)                   ; → #t
(procedure? (lambda (x) x))        ; → #t
(zero? 0)                          ; → #t
(even? 8)                          ; → #t
(odd? 8)                           ; → #f
(number? 5)                        ; → #t
(number? #t)                       ; → #f   布尔不是数字
(boolean? #f)                      ; → #t
(string? "s")                      ; → #t
(symbol? '+)                       ; → #t
(car '(1 . 2))                     ; → 1
(cdr '(1 . 2))                     ; → 2
'(1 . 2)                           ; → (1 . 2)  读入点号写法
''a                                ; → (quote a)  嵌套 quote
'(1 2 . 3)                         ; → (1 2 . 3)
(define (filter pred xs)
  (if (null? xs) '()
      (if (pred (car xs))
          (cons (car xs) (filter pred (cdr xs)))
          (filter pred (cdr xs))))) ; → filter
(filter (lambda (x) (> x 2)) '(1 4 2 5))  ; → (4 5)
(define (sum-to n) (if (= n 0) 0 (+ n (sum-to (- n 1)))))  ; → sum-to
(sum-to 20000)                     ; → 200010000  深递归不爆栈
(define x 10)                      ; → x
(define (f) x)                     ; → f
(let ((x 99)) (f))                 ; → 10   词法作用域：闭包看定义处环境
(display "tab\there")              ; 打印 tab<制表符>here
(newline)
"a\tb"                             ; → "a\tb"  顶层字符串转义打印
"say \"hi\""                       ; → "say \"hi\""
(expt 2 0)                         ; → 1
(< 1 2 2)                          ; → #f   链式比较相邻不成立
(<= 1 2 2)                         ; → #t
