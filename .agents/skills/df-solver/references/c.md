# C 代码规范与坏味道

## 规范

- 命名：类型 `PascalCase` 或 `snake_case`（跟项目）、函数 `snake_case`、宏全大写、内部符号加模块前缀
- 头文件：每个头文件有 include guard 或 `#pragma once`；头文件只放声明，不放定义（`static inline` 除外）
- 所有权：谁分配谁释放，成对出现在同一函数或同一模块；返回所有权时在函数名或注释里写明
- 错误：用返回值表达失败，`errno`/`out-param` 二选一并全项目统一；不吞错误
- 内存：分配后立即检查 `NULL`；`free` 后指针置 `NULL`
- 边界：所有外部输入的长度与指针先校验，再做 `memcpy`/`strcpy` 类操作
- 类型：定长类型（`uint32_t`）优先于 `int`；避免隐含有符号/无符号混用

## 坏味道

| 坏味道 | 识别信号 | 改法 |
|---|---|---|
| 返回栈上地址 | `return local_array;` | 调用方传入缓冲区，或 `malloc` 并明确所有权 |
| 隐式截断 | `size_t` 赋给 `int` | 用 `size_t` 贯穿，转换处显式检查范围 |
| 未初始化内存 | `char buf[64]; strcpy(buf, s);` | `memset` 或用 `snprintf` 带上限 |
| 检查了分配却没检查重分配 | `p = realloc(p, n);` | 临时变量接 `realloc` 结果，成功后再赋值 |
| 宏里有副作用 | `#define MAX(a,b) ((a)>(b)?(a):(b))` | 改 `static inline` 函数 |
| 忽略返回值 | `write(fd, ...);` 无检查 | 检查并按语义处理 `EINTR`/`EAGAIN` |
| 双重释放 / 悬垂指针 | 同一指针两次 `free` | 统一所有权，`free` 后置空 |
| 过深嵌套的 goto 清理 | 多层 `goto err` 交错 | 单出口 + 分级 cleanup 标签 |
| 头文件引入实现细节 | 头里出现 `#include "internal.h"` | 前置声明或 `opaque pointer` |

## 特别注意

- 未定义行为不因"当前编译器表现正常"而安全：越界、别名违规、溢出都按 bug 处理。
- 改 C 代码时先看构建选项（`-Wall -Wextra`、sanitizer）；没有就建议加，不要顺手改构建系统。
