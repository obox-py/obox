# JavaScript 代码规范与坏味道

## 规范

- 命名：变量与函数 `camelCase`、类 `PascalCase`、常量 `UPPER_SNAKE`
- 比较一律 `===`/`!==`
- 作用域：`const` 优先，其次 `let`，禁用 `var`
- 模块：ESM（`import`/`export`）优先；不用 `export default` 混搭命名导出
- 异步：`async/await` 优先于裸 `.then()`；所有 `await` 都要有错误路径
- 空值与默认：用可选链 `?.` 与 `??`，不要用 `||` 兜 `0`/`""`
- 副作用：模块顶层不做 I/O；函数尽量无副作用

## 坏味道

| 坏味道 | 识别信号 | 改法 |
|---|---|---|
| `==` 隐式转换 | `x == 0` | `===` |
| 未 await 的 Promise | 调用 async 函数不 `await` 也不 `catch` | `await` 或显式 `.catch()`，或标 `void` |
| 隐式全局 | 赋值未声明的变量 | 严格模式 + `const/let` |
| 回调地狱 | 三层以上嵌套回调 | 改 Promise/async |
| `forEach` 里 await | `arr.forEach(async ...)` | `for...of` 或 `Promise.all` |
| 循环里串行 await | `for { await fetch() }` | `Promise.all(items.map(...))` |
| 吞错误 | `try {} catch (e) {}` | 处理或带上文重抛 |
| `this` 丢失 | 传方法引用后 `this` 为 undefined | 箭头函数或 `bind` |
| 深层解构 | 五层嵌套解构 | 分步取值 |
| 大而全的工具文件 | `utils.js` 数百个导出 | 按领域拆模块 |
| 直接改传入对象 | 函数内改参数属性 | 返回新对象 |

## 特别注意

- 数字精度：金额不要用浮点直接运算。
- 时区与 `Date` 解析差异是最常见的线上事故来源之一。
