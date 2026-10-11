# Third-party notices / 第三方声明

PinShift's original code and documentation are licensed under
**GPL-3.0-or-later**. This does not replace the licenses or copyrights of
third-party components. See [LICENSE](LICENSE) and [COPYRIGHT](COPYRIGHT).

PinShift 原创代码和文档采用 **GPL-3.0-or-later**，不替代第三方组件的许可证或版权。以下是主要直接依赖及服务，包含开发 / 构建工具，并非整个分发包的完整软件清单。

| Component / 组件 | License or terms / 许可证或条款 | Upstream / 上游 |
| --- | --- | --- |
| PySide6 / Qt for Python | LGPL-3.0 / GPL options; Qt modules have their own licenses / 各 Qt 模块另有对应许可 | [Licensing](https://doc.qt.io/qtforpython-6/licenses.html) |
| pymobiledevice3 | GPL-3.0-or-later | [Project and license](https://github.com/doronz88/pymobiledevice3) |
| PyObjC / CoreLocation bridge | MIT | [Project and license](https://github.com/ronaldoussoren/pyobjc) |
| PyInstaller | GPL-2.0-or-later with its distribution exception / 附带分发例外 | [License and exception](https://pyinstaller.org/en/stable/license.html) |
| Python runtime | PSF license and included third-party notices / PSF 许可及其第三方声明 | [License](https://docs.python.org/3/license.html) |
| AMap JavaScript API and map content / 高德 API 与地图内容 | AMap service terms; not covered by PinShift's GPL / 遵循高德条款，不属于本项目 GPL 授权范围 | [AMap Open Platform](https://lbs.amap.com/) |

## Distribution / 分发

When distributing a binary, provide the corresponding source for that build
under the GPL, preserve applicable third-party license texts and copyright
notices, and review the licenses of all bundled dependencies and Qt modules.
The links above are references, not replacements for required license texts.
PyInstaller's build environment can contain dependencies beyond this table.

分发二进制包时，应按 GPL 提供与该构建对应的源码，保留所需的第三方许可文本和版权声明，并核对实际打包的所有依赖及 Qt 模块。上面的链接不能替代分发时要求附带的许可全文。PyInstaller 构建环境可能包含表格以外的依赖。

Map content shown in documentation screenshots remains subject to its
provider's rights and terms. Preserve AMap's attribution on the map.

文档截图中的地图内容仍遵循提供方的权利和条款，应保留地图上的高德署名。
