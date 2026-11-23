# Rust 代码规范与坏味道

## 规范

- 命名：类型/枚举/trait `PascalCase`、函数与变量 `snake_case`、常量 `UPPER_SNAKE`
- 错误：库用 `thiserror` 定义错误枚举，应用层用 `anyhow` 或自定义；`unwrap`/`expect` 只在测试或不变量已证明处出现
- 所有权：借用优先于克隆；参数用 `&`/`&mut`，返回所有权仅在需要时
- 可见性：默认私有，`pub(crate)` 优先于 `pub`
- unsafe：每处 `unsafe` 必须配 SAFETY 注释说明依赖的不变量
- trait 设计：为能力定义小 trait，避免"上帝 trait"；`impl Trait`/`dyn Trait` 按是否需要动态分派选
- 格式化与 lint：`cargo fmt`、`cargo clippy` 零警告

## 坏味道

| 坏味道 | 识别信号 | 改法 |
|---|---|---|
| `clone()` 蔓延 | 到处都是 `.clone()` | 改借用，或缩小作用域 |
| `unwrap`/`expect` 进生产路径 | 有 `unwrap()` 在非测试代码 | 换成 `?` 或显式处理 |
| `Rc<RefCell<T>>` 滥用 | 到处都是共享可变 | 重构所有权，用消息传递或内部不可变 |
| 长生命周期的 `&str` 与 `String` 混用 | 频繁 `.to_string()` | 参数收 `&str` 或 `impl AsRef<str>` |
| `async` 里持锁跨 `await` | `MutexGuard` 存活到 await 之后 | 缩短锁作用域或换 `tokio::sync::Mutex` |
| 阻塞调用在 `async` 里 | `std::fs`/`thread::sleep` | 换 `tokio::fs`/`spawn_blocking` |
| `panic!` 当错误分支 | 可恢复错误用 panic | 返回 `Result` |
| 用 `Vec` 当队列 | `remove(0)` | `VecDeque` |
| 手写 `for i in 0..v.len()` | 索引遍历 | `iter()`/`enumerate()` |
| 过宽 `pub` | 内部实现全部公开 | 收紧到 `pub(crate)` |
| feature flag 交叉爆炸 | 组合数暴涨 | 收敛 feature，用 cfg 明确组合 |

## 特别注意

- 改了 `struct` 字段就要看是否影响 `PartialEq`/`Hash`/`serde` 的语义与序列化兼容。
- `unsafe` 代码附近不要顺手重构：先补测试与 SAFETY 说明。
