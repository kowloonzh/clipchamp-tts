---
name: clipchamp-tts
description: 使用已登录的 Clipchamp 网页，通过 OpenCLI 浏览器自动化查询声音并生成、下载文字转语音音频。适用于用户要求 Clipchamp 配音、指定 Clipchamp 声线试听或生成旁白；不是 Azure Speech API 或离线语音合成。
---

# Clipchamp TTS

用本 Skill 的 CLI 驱动 Clipchamp 网页；根据用户的文字和声音选择生成 `.m4a`，不需要用户逐步手动操作。首次查询没有缓存的语言、刷新列表或生成音频时会新建 Clipchamp 项目；生成音频通过微软在线服务处理所给文本。复用已登录的 Chrome，不读取或导出账户凭据。未指定高级参数时沿用 Clipchamp 默认设置。

## 准备

需要 Python 3、`opencli`、已连接的 OpenCLI Browser Bridge / Chrome、用户已登录的 Clipchamp、`ffprobe`。执行 `opencli doctor` 排查连接。登录、验证码和二次验证由用户本人完成，不绕过。脚本路径相对于此 Skill 文件夹。

## 命令

声音以 Clipchamp **显示的完整名称**或 `voices` 返回的 **option ID** 精确指定，不静默替换；Azure 的声音 ID 不能直接假定等同于 Clipchamp 的 option ID。语言默认 `中文（普通话，简体）`，其他语言传网页显示的完整名称；列表会随账号和服务变化。

```bash
python3 scripts/clipchamp_tts.py voices --language '中文（普通话，简体）'
python3 scripts/clipchamp_tts.py voices --language '中文（普通话，简体）' --refresh
python3 scripts/clipchamp_tts.py settings --voice 'Yunxi Dragon HD Flash Latest'
python3 scripts/clipchamp_tts.py generate \
  --emotion '高兴' --pitch '高' --speed 1.1 \
  --voice 'Yunxi Dragon HD Flash Latest' \
  --text '这里是要朗读的文字。' --output ./voiceover.m4a
python3 scripts/clipchamp_tts.py generate \
  --language '中文（普通话，简体）' \
  --voice 'zh-CN-Yunxi-DragonHDFlashLatestNeural' \
  --text-file ./narration.txt --output ./voiceover.m4a
```

声音查询优先使用按语言保存的本地缓存，中文普通话无本地缓存时使用随 Skill 附带的快照；结果的 `source` 和 `captured_at` 标明来源和时间，可能过时或不完整。`--refresh` 在线更新；切换账号时应刷新。生成时仍按网页实际选项核对，不把缓存视为可用性保证。缓存查询无需浏览器。

`settings` 在线查询指定声音的情感、声调选项和速度范围，会新建项目。`--emotion`、`--pitch` 使用该账号当前界面的完整选项名称；各声音支持的选项不同，不支持时报告并列出候选，不要静默替换。`--speed` 是网页滑块支持的倍速，通常 0.5–2；不可表示的值会报错。按用户要求传入，未指定则保留默认。

长文本优先用 UTF-8 文件。脚本输出 JSON，其中 `output` 是最终文件路径，`voice` 包含网页实际选中的名称与 ID。不能覆盖已存在的输出文件。脚本检查下载完成、ffprobe 可识别音轨与正时长，但不等于逐字转写或人耳听审。交付时说明文件路径和实际声线，不虚报听审。

调用前确定用户指定的文字和声音；缺少声线时使用明确的已有项目选择，仍不清楚则先查询并询问，不自行换声。不要修改原稿。文字超出网页限制、生成失败或页面结构变化时报告实际错误和保留的项目；不要截断文字冒充完成。确需分段时按语义拆分、逐段生成并核对连接，最终音频需覆盖完整原稿。

`voices --refresh`、无缓存的语言查询、`settings` 和 `generate` 会新建网页项目；任务完成后不自动删除用户云端项目。输出为错误时检查 stderr 的 JSON 和 `session`，可用 `opencli browser --session <session> state` 查看现场；会话是当前操作的临时浏览器标签。网页和免费范围可能变化，不承诺无限使用或 API 可用。
