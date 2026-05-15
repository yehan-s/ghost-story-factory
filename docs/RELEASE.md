# Release — PyInstaller 单文件 binary

本文档讲怎么把项目打成「朋友双击就玩」的单文件 binary,
不需要朋友机器装 Python。

---

## Quick command

```bash
# 1. dev 环境装 pyinstaller(它不在 pyproject 主依赖,只是 build 工具)
.venv/bin/pip install pyinstaller

# 2. 打包(macOS / Linux / Windows 通用)
.venv/bin/pyinstaller \
  --onefile \
  --name ghost-story-tui \
  --add-data "stories:stories" \
  --collect-all textual \
  --hidden-import "ghost_story_factory.v7.menu_tui" \
  --hidden-import "ghost_story_factory.v7.tui_player" \
  --hidden-import "ghost_story_factory.v7.menu_registry" \
  play_tui.py

# 3. 产物
ls -lh dist/ghost-story-tui   # 约 24 MB (macOS arm64)
```

朋友拿到 `dist/ghost-story-tui` 后:

```bash
# macOS / Linux
./ghost-story-tui

# Windows
ghost-story-tui.exe
```

---

## 平台差异

| 平台 | binary 后缀 | 体积参考 | 备注 |
|---|---|---|---|
| macOS arm64 | (无) | ~24 MB | Apple Silicon。首次跑要在「系统设置 → 隐私与安全性 → 仍要打开」放行 |
| macOS x86_64 | (无) | ~25 MB | Intel Mac;打包时机器架构决定 binary 架构 |
| Linux x86_64 | (无) | ~22 MB | 跨发行版基本通用 |
| Windows x86_64 | `.exe` | ~30 MB | cmd / Windows Terminal / PowerShell 都行 |

> ⚠️ **跨平台打包**:PyInstaller 不能交叉编译。要出 Windows binary 必须在 Windows 机器上跑;
> Linux binary 在 Linux 上跑。**唯一通用方案是 GitHub Actions matrix**(见 § GitHub Actions)。

---

## 关键打包参数解释

| 参数 | 作用 |
|---|---|
| `--onefile` | 打成单文件 binary(否则是一个目录 + 一堆依赖文件) |
| `--name ghost-story-tui` | 产物名 |
| `--add-data "stories:stories"` | 把 `stories/` 目录原样打进 binary;运行时通过 `sys._MEIPASS` 访问 |
| `--collect-all textual` | textual 用 importlib.resources 加载 CSS 主题,必须显式 collect 全部资源 |
| `--hidden-import ...` | PyInstaller 静态扫描可能漏掉的动态 import,显式声明 |

---

## 运行时路径处理(关键技术细节)

`stories/` 目录的位置取决于运行模式:

```python
# src/ghost_story_factory/v7/menu_registry.py
def _stories_root() -> Path:
    # 1. 环境变量覆盖(debug 友好)
    override = os.environ.get("GHOST_STORY_STORIES_DIR")
    if override:
        return Path(override)
    # 2. PyInstaller frozen 模式 → sys._MEIPASS/stories
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "stories"
    # 3. 源码模式 → repo_root/stories
    here = Path(__file__).resolve()
    return here.parents[3] / "stories"
```

PyInstaller 把 `--add-data` 指定的资源解压到一个临时目录,
`sys._MEIPASS` 是该临时目录的绝对路径,只在 frozen 模式存在。

---

## macOS 签名 / Notarization

未签名 binary 第一次跑时 Gatekeeper 会拦截「无法打开,因为 Apple 无法检查恶意软件」。

**给朋友测试用(简单)**:
1. Finder 右键 `ghost-story-tui` → 「打开」→ 弹窗里再点「打开」
2. 或终端跑:`xattr -d com.apple.quarantine dist/ghost-story-tui`

**正式发布(需要 Apple Developer 账号)**:
```bash
codesign --force --deep --sign "Developer ID Application: <Your Name>" dist/ghost-story-tui
xcrun notarytool submit dist/ghost-story-tui --apple-id <email> --team-id <team> --wait
```

第一次发布前看 [Apple Notary Service 文档](https://developer.apple.com/documentation/security/customizing_the_notarization_workflow)。

---

## GitHub Actions 三平台矩阵(未实施)

下次出 release 时新增:

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags: ['v*']
jobs:
  build:
    strategy:
      matrix:
        os: [macos-latest, ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -e . pyinstaller
      - run: pyinstaller --onefile --add-data "stories:stories" --collect-all textual play_tui.py
      - uses: softprops/action-gh-release@v2
        with:
          files: dist/*
```

打 tag `v2.0.1` → 三平台 binary 自动出现在 GitHub Release。

---

## 本地体积优化(可选)

24 MB 的主要来源:

| 资源 | 估算 | 能不能压 |
|---|---|---|
| Python 解释器本体 | ~10 MB | 不能 |
| textual + rich + markdown_it 等 | ~6 MB | 不能(textual 需要全套) |
| stories/ JSON 数据 | ~600 KB | 已经 minified |
| PyInstaller bootloader | ~1 MB | 不能 |

20-25 MB 是合理下限。**别折腾压缩**——朋友下载 24 MB 完全无感。

---

## 已知限制

- **首次启动 1-2 秒延迟**:PyInstaller `--onefile` 模式每次启动要把资源解压到临时目录。
- **macOS Gatekeeper**:未签名 binary 首次要手动放行(见上)。
- **依赖 TTY**:在没有终端的环境(IDE 输出窗口、CI log)跑会立即退出。textual 必须 TTY。
