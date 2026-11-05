# 工具使用与输入约定

这些工具处理已有图像，不替代创作动作帧，也不会修复画面内部的角色漂移。参数中的尺寸与字节预算应与本次后台要求对应。

## 环境

Python 3.9+，安装 `requirements.txt` 中的Pillow。脚本均可通过 `--help` 查看参数。

## 编码GIF

动作帧放在同一目录，使用自然排序文件名，例如 `01.png`、`02.png`。所有PNG必须共享原始画布尺寸和角色锚点；不同尺寸会拒绝处理，不做逐帧裁切和重新居中。

```bash
python3 scripts/build_gif.py --frames ./frames/01 --output ./stickers/01.gif --size 240 --duration 120
```

指定每帧时长时，按自然排序后的文件顺序填写，单位毫秒，个数必须与输入PNG相同；GIF以10毫秒为单位：

```bash
python3 scripts/build_gif.py --frames ./frames/01 --output ./stickers/01.gif --durations 180,120,120,180
```

固定配字可单独提供一张与输出画布相同大小的透明PNG：

```bash
python3 scripts/build_gif.py --frames ./frames/01 --caption ./captions/01.png --output ./stickers/01.gif
```

动作区与字幕区应在制作时留开。工具锁定字幕包围矩形，避免字幕闪烁；不要把字幕放在角色必须经过的区域，否则会遮挡动作。单帧或完全相同的重复帧输入会拒绝；编码使用全局调色板、透明索引和清除上一帧的处置方式。

## 导出上传图

主页横幅示例（字节上限使用80000，比80KiB更保守）：

```bash
python3 scripts/export_image.py --input ./sources/artist-banner.png --output ./artist/banner-750x400.jpg --width 750 --height 400 --max-bytes 80000
```

封面保持透明并完整包含主体：

```bash
python3 scripts/export_image.py --input ./sources/cover.png --output ./album/cover-240x240.png --width 240 --height 240 --max-bytes 500000 --fit contain
```

`cover` 填满目标画布并居中裁切，生成时先留安全边距；`contain` 保留整张原画并透明留边。PNG保持PNG；如果无法达到指定预算，工具明确报错，不暗中改成JPEG。可在平台允许时另选JPEG，或简化图稿后重试。

## 技术检查

```bash
python3 scripts/inspect_images.py ./stickers --width 240 --height 240 --expect-count 16 --require-animation --require-loop --require-transparency --max-bytes 500000 --output ./reports/gifs.json
```

16张和500000字节是示例参数，数量和体积要求以当前后台为准。报告包含格式、尺寸、字节数、帧数、不同画面数量、时长、循环、透明像素和帧包围框。失败返回非零退出码。技术检查不能代替角色与动作质量的视觉验收。
