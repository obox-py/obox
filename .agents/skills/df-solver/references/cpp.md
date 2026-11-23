# C++ 代码规范与坏味道

## 规范

- 命名：类型 `PascalCase`、函数与变量 `snake_case` 或 `camelCase`（跟项目）、成员变量加 `m_` 或尾下划线（跟项目）
- 资源管理：RAII 为默认；`new`/`delete` 只在实现所有权语义时出现
- 所有权：`std::unique_ptr` 表达独占、`std::shared_ptr` 只在确需共享时用、裸指针与引用只表达借用
- 特殊成员函数：遵循 Rule of 0；必须自定义时成套写（析构/拷贝/移动）
- const：能 `const` 就 `const`，成员函数默认标 `const`
- 异常安全：提供基本保证；析构函数不抛
- 头文件：include guard 或 `#pragma once`；头里只 include 必要项，能前置声明就前置声明

## 坏味道

| 坏味道 | 识别信号 | 改法 |
|---|---|---|
| 裸 `new`/`delete` | 出现 `new Foo(` | 换 `std::make_unique` / 容器 |
| Rule of 3/5 只写一半 | 自定义析构但没有拷贝/移动 | 补齐或删除自定义实现 |
| 按值传递大对象 | `void f(std::string s)` | `const&` 或 `std::string_view` |
| 悬挂引用 | 返回局部变量的引用/`string_view` | 按值返回或明确生命周期 |
| 悬垂 lambda 捕获 | 捕获 `this` 或局部引用后异步使用 | 捕获值，或延长对象生命周期 |
| 隐式转换链 | 构造函数未 `explicit` | 单参构造加 `explicit` |
| 虚函数在构造/析构中调用 | ctor 里调 `virtual` | 拆成 `init()` 或工厂 |
| 复制蔓延 | 到处都是 `shared_ptr` | 收紧所有权，用 `unique_ptr` 或引用 |
| 头文件污染 | 头里 `#include <iostream>` 等重头 | 前置声明，实现文件里 include |
| 手写循环可比 STL | `for` 里找/排序/累加 | `<algorithm>` + lambda |

## 特别注意

- 移动后的对象状态：被移动对象只保证可析构可赋值，别假设内容。
- 改模板代码前先确认编译期报错是否来自模板本身，不要用 `const_cast` 掩盖。
