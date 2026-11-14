# clipchamp-tts

给 Codex、Claude 等 Agent 使用的 Clipchamp 文字转语音 Skill。通过 OpenCLI 控制已登录的 Chrome，选择语言和声音、输入文本，并将纯音频导出为 `.m4a`。

它使用 Clipchamp 在线服务，不提供离线模型或 Azure Speech API。每次查询声音或生成音频都会在 Clipchamp 创建一个新项目，不会自动删除。

## 环境要求

- Python 3、[FFmpeg](https://ffmpeg.org/)（需要 `ffprobe`）
- [OpenCLI](https://github.com/jackwener/opencli) 和已连接的 Browser Bridge Chrome 扩展
- Chrome 中已登录的 Clipchamp 账号

按照 OpenCLI 的说明安装并连接浏览器，然后运行 `opencli doctor` 检查连接。首次登录、验证码或二次验证由用户本人完成。网页界面与可用声音可能变化。

## 安装 Skill

将仓库克隆到 Agent 的 Skill 目录。例如：

```bash
# Codex
mkdir -p ~/.codex/skills
git clone https://github.com/kowloonzh/clipchamp-tts.git ~/.codex/skills/clipchamp-tts
```

Claude Code 用户可以克隆到 `~/.claude/skills/clipchamp-tts`；其他 Agent 请使用其对应的 Skill 目录。已有目录时请先检查，避免覆盖。安装后如未发现该 Skill，重启 Agent 会话。

## 让 Agent 使用

在对话中提供声音和原文，例如：

> 使用 clipchamp-tts，选择 Yunxi Dragon HD Flash Latest，朗读：飞得最远的，一分没有。

Agent 会按 [SKILL.md](SKILL.md) 的说明调用 CLI。默认语言是 **中文（普通话，简体）**，声音需要指定 Clipchamp 中的完整名称或选项 ID。

## 直接使用 CLI

以下命令在仓库目录下运行。查询默认语言的可用声音：

```bash
python3 scripts/clipchamp_tts.py voices
```

生成配音：

```bash
python3 scripts/clipchamp_tts.py generate \
  --voice 'Yunxi Dragon HD Flash Latest' \
  --text '你好，欢迎收听。' \
  --output ./voiceover.m4a
```

从 UTF-8 文件读取较长的稿件，并显式选择语言：

```bash
python3 scripts/clipchamp_tts.py generate \
  --language '中文（普通话，简体）' \
  --voice 'zh-CN-Yunxi-DragonHDFlashLatestNeural' \
  --text-file ./narration.txt \
  --output ./voiceover.m4a
```

`--language` 接受 Clipchamp 界面显示的完整语言名称；`voices --language '语言名称'` 可以查询该语言下的声音。声音必须与网页返回的名称或选项 ID 精确匹配，不会自动替换。CLI 当前使用 Clipchamp 默认音调和语速，不支持调整这两项。

成功时输出 JSON，包含输出路径、时长和实际选择的声线；不会覆盖已有文件。脚本会检查下载结果是否有音轨和正时长，但不等于检查朗读内容或人耳听审。文字超过网页限制时需按语义分段，并核对最终音频覆盖完整稿件。

如果运行失败，检查 stderr 中的错误及 session 名称；可执行 `opencli browser --session <session> state` 查看浏览器现场。登录失效或 Browser Bridge 未连接时，先恢复登录或运行 `opencli doctor`。不要提交账号凭据或下载的私人音频。
