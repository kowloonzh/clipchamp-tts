---
name: clipchamp-tts
description: 使用已登录的 Clipchamp 网页，通过 OpenCLI 浏览器自动化查询声音并生成、下载文字转语音音频。适用于用户要求 Clipchamp 配音、指定 Clipchamp 声线试听或生成旁白；不是 Azure Speech API 或离线语音合成。
---

# Clipchamp TTS

用本 Skill 的 CLI 驱动 Clipchamp 网页；根据用户的文字和声音选择生成 `.m4a`，不需要用户逐步手动操作。每次运行会在账号中新建一个 Clipchamp 项目并通过微软在线服务处理所给文本。复用已登录的 Chrome，不读取或导出账户凭据。默认设置为 Clipchamp 默认音调与语速；当前 CLI 不支持调整这些参数，不要声称支持。

## 准备

需要 Python 3、`opencli`、已连接的 OpenCLI Browser Bridge / Chrome、用户已登录的 Clipchamp、`ffprobe`。执行 `opencli doctor` 排查连接。登录、验证码和二次验证由用户本人完成，不绕过。脚本路径相对于此 Skill 文件夹。

## 命令

声音以 Clipchamp **显示的完整名称**或 `voices` 返回的 **option ID** 精确指定，不静默替换；Azure 的声音 ID 不能直接假定等同于 Clipchamp 的 option ID。语言默认 `中文（普通话，简体）`，其他语言传网页显示的完整名称；列表会随账号和服务变化。

```bash
python3 scripts/clipchamp_tts.py voices --language '中文（普通话，简体）'
python3 scripts/clipchamp_tts.py generate \
  --voice 'Yunxi Dragon HD Flash Latest' \
  --text '这里是要朗读的文字。' --output ./voiceover.m4a
python3 scripts/clipchamp_tts.py generate \
  --language '中文（普通话，简体）' \
  --voice 'zh-CN-Yunxi-DragonHDFlashLatestNeural' \
  --text-file ./narration.txt --output ./voiceover.m4a
```

长文本优先用 UTF-8 文件。脚本输出 JSON，其中 `output` 是最终文件路径，`voice` 包含网页实际选中的名称与 ID。不能覆盖已存在的输出文件。脚本检查下载完成、ffprobe 可识别音轨与正时长，但不等于逐字转写或人耳听审。交付时说明文件路径和实际声线，不虚报听审。

调用前确定用户指定的文字和声音；缺少声线时使用明确的已有项目选择，仍不清楚则先查询并询问，不自行换声。不要修改原稿。文字超出网页限制、生成失败或页面结构变化时报告实际错误和保留的项目；不要截断文字冒充完成。确需分段时按语义拆分、逐段生成并核对连接，最终音频需覆盖完整原稿。

`voices` 和 `generate` 都会新建网页项目；任务完成后不自动删除用户云端项目。输出为错误时检查 stderr 的 JSON 和 `session`，可用 `opencli browser --session <session> state` 查看现场；会话是当前操作的临时浏览器标签。网页和免费范围可能变化，不承诺无限使用或 API 可用。
