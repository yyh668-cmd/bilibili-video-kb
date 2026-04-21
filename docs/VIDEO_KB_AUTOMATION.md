# B站视频知识库自动化

## 目标

把 B 站知识视频处理成两类长期可用产物：

- Obsidian 里的完整知识笔记
- 桌面文件夹里的 `.xmind` 专业导图

Obsidian 只保留两层结构：

- `01 知识笔记`
- `02 索引导航`

不再生成主题页、概念卡、转写索引、Markdown 导图这些中间层。

## 默认路径

Obsidian：

- `D:\Document\Win_Obsidian知识库\YYH个人知识库\08 视频知识库`

桌面 XMind：

- `C:\Users\yy198\Desktop\B站视频XMind`

缓存：

- `.cache/video_kb/{run_id}/`

## 初始化

```powershell
.\scripts\setup_video_kb.ps1
```

如需启用 OpenAI 抽取：

```powershell
$env:OPENAI_API_KEY = "your_key"
```

## 日常使用

处理 B 站链接：

```powershell
.\scripts\run_video_kb.ps1 "https://www.bilibili.com/video/BV1xxxxxx/"
```

处理本地媒体：

```powershell
.\scripts\run_video_kb.ps1 "D:\Downloads\lecture.mp4"
```

覆盖桌面 XMind 输出目录：

```powershell
.\scripts\run_video_kb.ps1 "https://www.bilibili.com/video/BV1xxxxxx/" -XMindRoot "D:\MyXMind"
```

强制不用 OpenAI：

```powershell
.\scripts\run_video_kb.ps1 "https://www.bilibili.com/video/BV1xxxxxx/" -SkipOpenAI
```

只输出 JSON manifest：

```powershell
.\scripts\run_video_kb.ps1 "https://www.bilibili.com/video/BV1xxxxxx/" -Json
```

## Python CLI

```powershell
.venv-video-kb\Scripts\python.exe -m video_kb.cli ingest "https://www.bilibili.com/video/BV1xxxxxx/" --open-obsidian
```

健康检查：

```powershell
.venv-video-kb\Scripts\python.exe -m video_kb.cli doctor --json
```

## 产物结构

Obsidian：

- `08 视频知识库/01 知识笔记/{年份}/{BV号 标题}.md`
- `08 视频知识库/02 索引导航/总索引.md`

桌面：

- `B站视频XMind/{BV号 标题}.xmind`

缓存目录包含：

- `raw_info.json`
- `transcript.json`
- `transcript.txt`
- `analysis.json`
- `run_manifest.json`

## 当前策略

- 优先使用字幕
- 没有可用字幕时自动回退到 `faster-whisper` ASR
- 有 `OPENAI_API_KEY` 时优先用 OpenAI 抽取
- 没有密钥或调用失败时自动降级为 extractive
- 知识页自动加入 `关联视频` 区块
- 总索引页按最近更新和主题导航汇总所有知识页
- XMind 导出后会自动补齐 `meta.xml` 和 `META-INF/manifest.xml`，保证能被当前 XMind 客户端正常打开
