# GitHub 发布准备

目标仓库：`https://github.com/affirmatives/PinShift`。本文件是发布流程，不代表仓库或 Release 已创建。

## 发布前必须完成

- 初始化 Git，检查 `.gitignore` 生效，只提交源码、文档、截图、图标和构建配置，不提交 `.venv*`、`build/`、`dist/`、个人配置或凭据。
- 对实际分发包补齐需要保留的第三方许可证全文和版权声明。构建脚本已收集随包许可文本及上游材料；`THIRD_PARTY_NOTICES.md` 是主要组件说明，不能替代许可全文，也不是完整依赖清单。特别核对 Qt 各模块、Python 运行时、pymobiledevice3 及其传递依赖。
- 保存与二进制对应的源码。版本标签须指向构建该二进制所使用的代码；源码改变后重新构建。GPL 要求提供对应源码。
- 确认下载限制在 README 和 Release 说明中明确：Apple 芯片、未公证、需配置高德凭据、设备信任及开发者模式。

## 建议完成

- 在另一台没有 Python 开发环境的 Mac 上，从下载的 DMG 安装并验证启动、地图、设置 / 清除定位及管理员授权。
- 为实际发布构建保存完整的依赖版本和构建环境，避免当前最低版本约束造成不可复现构建。
- 配置 Developer ID 签名与公证，以改善下载后首次启动体验。当前 ad-hoc 签名不能替代公证。
- 添加 Issue 模板或贡献指南，便于收集复现信息；这些不阻止首次发布。

## 通过 GitHub 网页发布

1. 在账号下新建公开仓库 `PinShift`，上传源码与文档；安装包放到 Release Assets，不放在源码仓库里。
2. 在确认源码与二进制对应后创建 `v1.0.0` 标签。
3. 打开仓库的 Releases，选择 Draft a new release，选择 `v1.0.0`，标题为 `PinShift 1.0.0`。
4. 将 [v1.0.0.md](releases/v1.0.0.md) 的内容作为发布说明，更新其中的验证范围以反映实际结果。
5. 上传 `dist/release-1.0.0/PinShift-1.0.0-macos-arm64.dmg`、`PinShift-1.0.0-third-party-notices.zip` 和 `SHA256SUMS.txt`；按许可要求提供对应源码和第三方许可材料。
6. 先保存草稿，核对附件、版本和说明，再发布。

278 MB 左右的 DMG 适合放在 GitHub Release Assets。源码仓库中已通过 `.gitignore` 排除 DMG，不要强行加入 Git。

## 更新发布材料

二进制改变后必须重新生成版本化附件和 SHA-256，避免校验文件与下载内容不符。README 截图的文档更新本身不要求重建应用；运行代码、构建配置或包内声明变更则需要重新构建。
