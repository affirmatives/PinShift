# PinShift 开发约定 / Agent guidelines

本文件适用于整个项目，供编码助手和贡献者使用。公开文档为 [README.md](README.md) 和 [README.en.md](README.en.md)。

## 项目范围

- macOS 上基于 PySide6 / Qt WebEngine 的 iPhone USB 虚拟定位应用，当前支持单台设备。
- 设备协议通过 pymobiledevice3 实现；地图使用高德 JavaScript API 2.0；Mac 定位使用 PyObjC / CoreLocation。
- 当前界面为中文。修改功能、命令或限制时同步更新两份 README，不添加未经验证的跨平台或 iOS 兼容性承诺。

## 环境

- 建议使用 Python 3.13 和项目虚拟环境。依赖来源为 `requirements.txt`；Node.js 仅用于地图检查，无需 npm 依赖。
- 优先复用现有 `.venv`。它可能是软链接，先检查目标，不要为普通问题删除、替换或重建已有环境。
- 使用虚拟环境中的 `python` / `python -m pip`，或 uv 安装依赖，避免修改系统 Python。
- 纯文档改动无需安装依赖、重建应用或操作真实设备。

## 模块职责

| 路径                    | 职责                                       |
| ----------------------- | ------------------------------------------ |
| `main.py`               | GUI 和 `--location-helper` 子进程入口      |
| `models/`、`config/`    | 数据模型和 JSON 配置读写                   |
| `services/`             | USB 扫描、iPhone 定位、tunnel、Mac 定位    |
| `ui/`                   | Qt 界面、主题与用户动作编排                |
| `bridges/map_bridge.py` | Qt WebChannel 信号与槽                     |
| `web/`                  | 地图加载、搜索、选点、主题与标记           |
| `utils/`                | 路径、坐标转换、日志与脱敏                 |
| `tests/`                | 直接运行的回归检查脚本，不是 pytest 测试集 |
| `packaging/`            | `.app` 和 `.dmg` 构建脚本                  |

## 实现约束

- 保持 UI 编排与设备协议分离。耗时设备操作放到工作线程，经 Qt 信号将结果交回主线程，不从后台线程直接更新控件。
- pymobiledevice3 调用依赖异步 API；升级时核对 API 签名、await、连接关闭和异步上下文管理，不仅调整版本号。
- **坐标边界必须明确**：地图和保存的选点使用 GCJ-02；iPhone 接收 WGS-84，由 `LocationService.set_location` 转换。CoreLocation 返回 WGS-84，显示前转为 GCJ-02。
- Python 选点参数顺序为 `(longitude, latitude)`，底层定位 API 使用 `(latitude, longitude)`。辅助进程输入已是 WGS-84，不要重复转换。
- 修改桥接槽名、信号或 JavaScript 方法时，同步检查 `bridges/`、`ui/main_page.py` 和 `web/map.js`。
- 保留设置默认值、现有配置可加载性及主题切换不丢失选点的行为。
- 资源路径通过 `utils.paths` 获取，兼容源码和 PyInstaller frozen 模式。运行数据写入应用数据目录，不写入源码或 `.app` 资源目录。
- 管理员辅助进程涉及 shell 引用、进程身份、状态 / 命令文件和持续 tunnel。修改时保持参数安全引用，核对重复设置、清除、取消授权、超时及陈旧会话处理，不扩大提权范围。
- 日志使用现有脱敏机制，不输出地图凭据。公开设备数据、坐标或问题报告时使用脱敏或模拟数据。
- 保持现有类型标注、Python 模块和 JavaScript 风格，不为局部改动引入新框架或无关格式化。

## 检查与验证

在项目根目录、已激活依赖环境时执行相关检查：

```bash
PYTHONPATH=. python tests/check_core.py
node tests/check_map.cjs
PYTHONPATH=. python tests/check_ui.py
```

- 配置、坐标或服务改动运行核心检查；地图逻辑改动运行地图检查；Qt 界面、主题或桥接改动运行界面检查及地图检查。
- 界面检查需要 macOS 图形会话，会打开窗口并写入 `/private/tmp/pinshift-*.png`。视觉改动需查看截图。
- 新增检查应通过 `PINSHIFT_APP_SUPPORT_DIR` 使用临时配置目录，配合模拟设备及占位凭据。
- 设备定位、管理员授权及 tunnel 的验证另行安排；不要把模拟检查通过描述为真机验证通过，不仅为验证代码自动改变已连接 iPhone 的定位。
- 文档改动检查文件链接、命令与双语内容一致性即可；打包变更再视情况构建。
- 无法执行检查时说明环境条件和未验证范围，不隐藏失败。

## 构建与发布

```bash
bash packaging/build_macos.sh
bash packaging/create_dmg.sh
```

- 优先使用脚本：从 `PinShift.spec` 构建后执行 ad-hoc 签名和验证；单独构建 spec 不包含脚本的签名后处理。
- `config/app_info.py` 集中维护版本、作者、版权和链接；`PinShift.spec` 使用这些信息写入版本及版权，并包含定位权限说明与许可证文件。版本变更同步更新两份 README。
- 产物位于 `dist/`，不提交到源码仓库；构建会覆盖对应产物。
- 当前没有 Developer ID 签名、公证或 universal binary。发布说明只列实际验证的系统和架构。
- 不凭空添加仓库地址、下载链接、CI 徽章、已发布版本或兼容性承诺。
- 项目已由维护者指定为 GPL-3.0-or-later。保留 `LICENSE`、`COPYRIGHT` 和第三方声明，不擅自更换授权方式。

## 提交前

- 检查并保留用户已有改动，只修改任务所需文件。
- 遵循 `.gitignore`；不提交虚拟环境、缓存、构建产物、日志、真实凭据、个人配置或设备会话文件。
- 同步中英文文档，报告改动目的、已执行检查及仍需真机验证的部分。

## English summary

These guidelines apply throughout the project. Keep device logic in `services/`, GUI orchestration in `ui/`, and map behavior in `web/`; coordinate bridge changes across them. Reuse the existing virtual environment, preserve user changes, and update both READMEs together.

Map coordinates use GCJ-02 in `(longitude, latitude)` order. Device APIs receive WGS-84 in `(latitude, longitude)` order. Helper inputs are already converted. Preserve asynchronous APIs, cleanup, GUI thread boundaries, frozen resource paths, and helper lifecycle handling.

Run relevant checks with temporary settings and mocked devices. UI checks need a macOS graphical session. Report hardware validation separately. Do not commit secrets, device data, environments, or build outputs, and do not invent licensing, release, or compatibility claims.
