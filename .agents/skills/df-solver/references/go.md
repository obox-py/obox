# Go 代码规范与坏味道

## 规范

- 命名：包名短小全小写、导出标识符 `CamelCase`、非导出 `camelCase`、缩写全大写（`ID`、`HTTP`）
- 错误：`error` 作为最后一个返回值；用 `%w` 包装保留链；不因"应该不会出错"而忽略
- 上下文：跨函数调用与 I/O 一律传 `ctx context.Context` 作为首参
- 并发：谁启动 goroutine 谁负责它的退出；共享状态用 channel 或 `sync` 明确表达
- 资源：`defer` 关闭，且紧跟资源获取之后
- 接口：由使用方定义，越小越好；不要为测试造大接口
- 格式：`gofmt`/`goimports` 结果即标准，不手工对抗

## 坏味道

| 坏味道 | 识别信号 | 改法 |
|---|---|---|
| 忽略错误 | `_ = doSomething()` / 直接丢弃返回 | 检查并返回或记录 |
| goroutine 泄漏 | 启动后无退出条件 | 接 `ctx` 或 `done` channel |
| `defer` 在循环里 | `for { f, _ := os.Open(); defer f.Close() }` | 抽成函数，让 `defer` 随函数返回释放 |
| 空 `select {}` 死锁 | `select {}` 占位 | 用 `<-ctx.Done()` |
| 复制含锁结构 | 传 `sync.Mutex` 值 | 传指针 |
| `context.Background()` 遍地 | 函数内部自造 ctx | 由调用方传入 |
| 错误只用 `errors.New` 拼串 | 丢失原始错误 | `fmt.Errorf("...: %w", err)` |
| 过早抽象接口 | 只有一个实现却先定接口 | 先具体类型，第二个实现出现再抽 |
| 包内全局状态 | `var db *sql.DB` 到处用 | 显式依赖注入 |
| panic 当错误处理 | 库内 `panic` | 返回 error，panic 只用于不可恢复 |

## 特别注意

- `nil` map 可读不可写；`nil` channel 上的收发永久阻塞。
- 循环变量捕获在旧版本有坑：升级 go.mod 前确认 `for` 里启动的 goroutine 语义。
