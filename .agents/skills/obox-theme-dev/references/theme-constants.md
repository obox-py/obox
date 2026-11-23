# theme.py 常量与 QSS

## 颜色

| 常量 | 用途 |
|---|---|
| BACKGROUND / SURFACE / SURFACE_MUTED | 背景、卡片面、弱背景 |
| TEXT / TEXT_MUTED | 正文、辅助文字 |
| LINE | 细分隔线（10% 左右） |
| ACCENT / ACCENT_TEXT / ACCENT_SOFT | 强调色、强调底上的文字、强调淡底 |
| CARD_SURFACE / CARD_BORDER | 卡片面与可见描边 |
| ICON_MUTED / ICON_ACTIVE | 侧栏图标未选中/选中 |
| TITLE_MUTED / TITLE_ACTIVE | 标题栏三按钮的线条色与悬停色（与侧栏图标解耦） |
| SLIDER_TRACK | 滑块轨道色，必须与页面底色可辨 |

## 尺寸

RADIUS_CONTROL=2、RADIUS_CARD=2、CONTROL_HEIGHT=32、SPACING={"margin":20,"gap":16,"control_height":32}

## QSS 约定

- 输入类默认全边框，其它组件默认无描边；卡片由组件自绘
- 字体栈：HarmonyOS Sans SC → Noto Sans SC → Microsoft YaHei UI → Segoe UI
- 标题栏、滚动条（8px、无箭头）、toast、modal、tab 都有专门规则
- 托盘菜单用自己的对象名 #obox-tray-menu：面板宽 240、行高 44、圆角 10、左右内边距 14；条目与分隔线各有一条规则，半透明底由 QMenu 的 WA_TranslucentBackground 支撑
- 标题栏三按钮的配色走 provider 的 title_muted / title_active，缺省回退 icon 两色
- QSS 写在主题目录的 styles.qss 里，用 {{TOKEN}} 引用 PALETTE 的键，provider 加载时替换成实际取值
- 构建会把 styles.qss 复制到 .theme/<kit>/，与 pyd 同级；改 QSS 后必须重编 pyd（或至少重新复制产物）