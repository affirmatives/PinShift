# Third-party license sources

`upstream/` contains license texts fetched from official dependency sources
for the 1.0.0 build. `upstream/SOURCES.json` records each source URL. Qt texts
are from Qt 6.11.1; Python's combined license and copyright notice is from
CPython 3.13.15. These files retain their upstream terms and copyrights.

The build script additionally collects license and notice files from installed
Python distributions and records their exact versions in the application's
`Contents/Resources/third-party-licenses/` directory. Recheck source materials
when upgrading dependencies. Preserve module-specific rights, including Qt
and Chromium notices, rather than treating PinShift's GPL as their replacement.

此目录保存 1.0.0 构建使用的上游许可材料，来源见 `upstream/SOURCES.json`。
构建时还会收集 Python 依赖附带的许可文本和版本记录。升级依赖时应重新核对
材料；这些文件不改变第三方组件的版权和许可。
