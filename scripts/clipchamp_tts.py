#!/usr/bin/env python3
"""Generate Clipchamp voiceovers by driving the signed-in Chrome UI via OpenCLI."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

SESSION = 'clipchamp-tts-' + uuid.uuid4().hex[:10]

def call(*args, timeout=60):
    cmd = ['opencli', 'browser', '--session', SESSION, *args]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f'Browser command timed out: {args[0]}')
    try:
        result = json.loads(p.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f'OpenCLI returned invalid output: {(p.stderr or p.stdout)[:500]}')
    if not result.get('ok'):
        e = result.get('error', {})
        raise RuntimeError(f'{e.get("code", "browser_error")}: {e.get("message", "Unknown browser error")}')
    return result.get('data')

def read(js):
    result = call('eval', 'JSON.stringify(' + js + ')')
    return json.loads(result) if isinstance(result, str) else result

def wait_for(expression, description, seconds=60):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if read(expression):
            return
        time.sleep(1)
    raise RuntimeError(f'Timed out waiting for {description}; check the Clipchamp page, login, or service status.')

def click(css):
    call('click', css)

def options():
    return read('Array.from(document.querySelectorAll("[role=option]"), e => ({id:e.id, label:e.innerText.trim().split("\\n")[0]}))')

def choose(selector, wanted, kind):
    current = read('document.querySelector(' + json.dumps(selector) + ')?.value')
    if kind == 'language' and current == wanted:
        return {'id': None, 'label': current}
    click(selector)
    wait_for('document.querySelectorAll("[role=option]").length > 0', kind + ' options', 30)
    entries = options()
    exact = [x for x in entries if wanted.casefold() in (x['id'].casefold(), x['label'].casefold())]
    if kind == 'language' and len(exact) > 1 and len({x['label'] for x in exact}) == 1:
        exact = exact[:1]
    if len(exact) != 1:
        matches = [x for x in entries if wanted.casefold() in (x['id'] + ' ' + x['label']).casefold()]
        raise RuntimeError(f'{kind} must match one exact displayed name or option ID; candidates: {json.dumps(matches[:20], ensure_ascii=False)}')
    entry = exact[0]
    if not entry['id']:
        raise RuntimeError(f'{kind} option has no stable ID.')
    click('[role="option"][id=' + json.dumps(entry['id'], ensure_ascii=False) + ']')
    actual = read('document.querySelector(' + json.dumps(selector) + ')?.value')
    if actual != entry['label']:
        raise RuntimeError(f'{kind} selection did not stick: expected {entry["label"]!r}, got {actual!r}')
    return entry

def editor():
    call('open', 'https://app.clipchamp.com/consumer/home')
    wait_for('!!document.querySelector("[data-testid=create-project-button]")', 'signed-in Clipchamp home', 90)
    click('[data-testid="create-project-button"]')
    wait_for('!!document.querySelector("[data-testid=editor-page]")', 'new editor', 90)
    wait_for('!!document.querySelector("[data-testid=property-panel-button-recordCreate]")', 'record and create panel')
    click('[data-testid="property-panel-button-recordCreate"]')
    wait_for('!!document.querySelector("#voiceover")', 'text-to-speech entry')
    click('#voiceover')
    wait_for('!!document.querySelector("[data-testid=voice-dropdown]")', 'text-to-speech controls', 90)

def main():
    parser = argparse.ArgumentParser(description='Generate speech through the Clipchamp website using your signed-in OpenCLI Chrome session.')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('voices', 'generate'):
        p = sub.add_parser(name)
        p.add_argument('--language', default='中文（普通话，简体）', help='Exact language label as displayed in Clipchamp')
    gen = sub.choices['generate']
    gen.add_argument('--voice', required=True, help='Exact Clipchamp voice display name or option ID')
    group = gen.add_mutually_exclusive_group(required=True)
    group.add_argument('--text')
    group.add_argument('--text-file', type=Path)
    gen.add_argument('--output', type=Path, required=True, help='New .m4a output file')
    args = parser.parse_args()
    if not shutil.which('opencli') or not shutil.which('ffprobe'):
        parser.error('opencli and ffprobe must both be installed and on PATH')
    if args.command == 'generate':
        text = args.text if args.text is not None else args.text_file.read_text(encoding='utf-8')
        if not text.strip():
            parser.error('Text must not be empty')
        output = args.output.expanduser().resolve()
        if output.suffix.lower() != '.m4a' or output.exists():
            parser.error('Output must be a new .m4a file; existing files are not overwritten')
        output.parent.mkdir(parents=True, exist_ok=True)
    editor()
    language = choose('[data-testid="language-dropdown"]', args.language, 'language')
    if args.command == 'voices':
        click('[data-testid="voice-dropdown"]')
        wait_for('document.querySelectorAll("[role=option]").length > 0', 'voice options', 30)
        voices = options()
        try:
            call('close')
        except RuntimeError:
            pass
        print(json.dumps({'language': language, 'voices': voices}, ensure_ascii=False, indent=2))
        return
    voice = choose('[data-testid="voice-dropdown"]', args.voice, 'voice')
    field = '[role="textbox"][contenteditable="true"]'
    result = call('fill', field, text)
    if not result.get('verified'):
        raise RuntimeError('Clipchamp did not retain the full input text; no audio was exported.')
    click('[data-testid="voice-save-button"]')
    wait_for('document.querySelector("[data-testid=voice-save-button]")?.getAttribute("aria-disabled") === "true"', 'speech generation', 180)
    click('[data-testid="button-export"]')
    wait_for('!!document.querySelector("[data-testid=filename-ext-input]")', 'export dialog')
    ext = read('document.querySelector("[data-testid=filename-ext-input]")?.parentElement?.innerText')
    if not ext or '.m4a' not in ext:
        raise RuntimeError('Export dialog is not set to audio-only .m4a; inspect the page before retrying.')
    token = 'clipchamp-tts-' + uuid.uuid4().hex
    call('fill', '[data-testid="filename-ext-input"]', token)
    click('[data-testid="export-button"]')
    download = call('wait', 'download', token, '--timeout', '180000', timeout=195)
    source = Path(download['filename'])
    if download.get('state') != 'complete' or not source.is_file() or source.stat().st_size == 0:
        raise RuntimeError('Download did not complete or is empty.')
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type', '-of', 'json', str(source)], capture_output=True, text=True)
    if probe.returncode:
        raise RuntimeError('Downloaded file could not be decoded by ffprobe: ' + probe.stderr[:300])
    media = json.loads(probe.stdout)
    if not any(s.get('codec_type') == 'audio' for s in media.get('streams', [])) or float(media.get('format', {}).get('duration', 0)) <= 0:
        raise RuntimeError('Downloaded file has no audio stream or positive duration.')
    # Exclusive creation prevents races from overwriting a user file.
    with output.open('xb') as dst, source.open('rb') as src:
        shutil.copyfileobj(src, dst)
    source.unlink()
    try:
        call('close')
    except RuntimeError:
        pass
    print(json.dumps({'ok': True, 'output': str(output), 'duration_seconds': float(media['format']['duration']), 'language': language, 'voice': voice}, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc), 'session': SESSION}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
