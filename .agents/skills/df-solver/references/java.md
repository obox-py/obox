# Java 代码规范与坏味道

## 规范

- 命名：类 `PascalCase`、方法与变量 `camelCase`、常量 `UPPER_SNAKE`、包名全小写
- 不可变优先：字段 `final`，优先 `record` 或不可变值对象
- 空值：公共 API 明确是否可为 `null`，或用 `Optional` 表达"可能没有"
- 异常：受检异常只用于调用方真能处理的场景；不抛 `Exception`/`RuntimeException` 这种过宽类型
- 资源：`try-with-resources`
- 集合：优先接口类型（`List`/`Map`），对外返回不可变视图
- 日志：参数化占位符，不拼字符串；异常带上下文

## 坏味道

| 坏味道 | 识别信号 | 改法 |
|---|---|---|
| `null` 传递成链 | 多层 `if (x != null)` | 入口校验 + 返回空集合/空对象，不返回 `null` |
| 上帝类 | 单个类上千行、几十个方法 | 按职责拆，抽出协作对象 |
| `equals`/`hashCode` 不同步 | 只重写了一个 | 一起重写，或用 `record` |
| 吞异常 | `catch (Exception e) {}` | 处理、转换或带上下文重抛 |
| 过宽捕获 | `catch (Throwable)` | 捕获具体类型 |
| 事务/资源泄漏 | `Connection` 未关闭 | `try-with-resources` |
| 静态可变状态 | `static` 集合被到处改 | 收敛为依赖注入的实例 |
| 字符串拼接 SQL/命令 | `"select * from " + name` | 参数化 |
| 双层循环里的 N+1 查询 | 循环内调 `repository.find` | 批量查询 + 内存 map |
| `Optional` 当字段/参数 | `private Optional<X> x` | 只在返回值用 |
| 过深继承 | 5 层以上父类 | 组合优先 |

## 特别注意

- 并发：共享可变状态必须明确同步策略；`HashMap` 换 `ConcurrentHashMap` 不等于线程安全，复合操作仍要加锁。
- 改了 `equals` 就要检查所有 `Set`/`Map` 用法。
