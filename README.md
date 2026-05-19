# Click Macro

一个轻量 Windows 辅助点击器原型：自定义多个目标点，然后把它们编排成按顺序执行的点击宏。

## 功能

- 添加、编辑、删除目标点。
- 3 秒倒计时捕获鼠标当前位置作为目标点。
- 添加宏步骤：选择目标点、设置步骤前延迟、点击次数、连点间隔。
- 调整步骤顺序，删除步骤。
- 设置循环次数，`0` 表示无限循环。
- 运行、暂停、停止宏。
- 保存和打开 `.json` 宏配置。
- Windows 上使用 `SendInput` 执行真实点击。

## 运行

推荐下载打包好的 Windows 程序：

1. 打开 GitHub 仓库的 `Actions` 页面。
2. 选择 `Build Windows App`。
3. 下载最新一次运行里的 `ClickMacro-windows` artifact。
4. 解压后双击 `ClickMacro.exe`。

如果下载的是 Release 版本，直接下载 `ClickMacro-windows.zip`，解压后双击 `ClickMacro.exe`。

也可以从源码运行，需要 Windows + Python 3.10 或更新版本。

双击运行：

```text
ClickMacro.bat
```

或者从命令行运行：

```powershell
python app.py
```

快捷键：

- `F5`：开始
- `F6`：暂停 / 继续
- `F7`：停止

注意：如果点击目标窗口需要管理员权限，建议用同等权限启动这个工具，否则 Windows 可能会拦截输入注入。

## 使用流程

1. 点击 `Capture in 3s`，把鼠标移动到要点击的位置，倒计时结束后会保存点位。
2. 对每个目标位置重复一次。
3. 在 `Macro Steps` 里选择点位，设置延迟、点击次数和间隔，然后添加步骤。
4. 设置循环次数，点击 `Start`。
5. 需要紧急停止时按 `F7`。

## 开发验证

核心逻辑使用标准库 `unittest` 验证，不需要第三方依赖。

```bash
python -m unittest discover -s tests
```

在 macOS/Linux 上运行时，程序会进入 dry-run 模式，不会发送真实点击；真实点击只在 Windows 上启用。

## 打包 Windows 程序

本地打包需要 Windows + Python 3.10 或更新版本：

```text
build_windows.bat
```

脚本会生成：

```text
ClickMacro-windows.zip
```

发布 Release 时，可以推送一个版本 tag：

```bash
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions 会自动构建 `ClickMacro.exe`，并把 `ClickMacro-windows.zip` 附到对应 Release 上。
