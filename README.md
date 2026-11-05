# 微信表情包上架 Skill

**先确认静态稿，再制作动态。** 为微信表情开放平台准备完整图片、文案和上传清单。

让Codex把微信表情开放平台投稿需要的图片与文案整理成可逐项上传的素材包。核心流程：角色方向 → 整套静态稿 → 用户确认 → 代表动作验证 → 动态表情 → 配套图与文案 → 检查打包。

- 专辑：独立表情文件、详情横幅、封面、聊天面板图标。
- 个人主页：头像、个人主页横幅，可复用已有资料。
- 赞赏：引导语、引导图、致谢图，按需启用。
- 文案：名称、介绍、版权署名、每张含义词及分类参考。
- 验收：尺寸、格式、大小、动画循环，以及漂移、角色一致性和文字稳定性。

![嘴硬小鹅GIF示例](examples/goose/preview.gif)

> 作者授权公开的16张大鹅示例；部分动作存在用户反馈的漂移问题，保留为视觉验收案例，不代表已通过全部质量检查或微信审核。[示例说明](examples/goose/README.md)

## 安装

将整个仓库作为一个Codex skill安装：

```bash
git clone https://github.com/WangQvQ/wechat-sticker-publisher.git "${CODEX_HOME:-$HOME/.codex}/skills/wechat-sticker-publisher"
```

同名目录已存在时先检查现有内容，避免覆盖本地修改。图片创作需要Codex环境提供图像生成工具；本地Python工具只处理已有图像，不调用AI服务或读取API密钥。

## 素材与工作流

查看 [完整素材与文案清单](references/materials-checklist.md) 和 [SKILL.md](SKILL.md)。完整适用范围为16张主图加7张配套图，共23张上传图片；数量和可选模块可按需求调整。主页横幅与专辑详情横幅是两个字段，尺寸相同也不要混用不同体积的文件。

制作参考来自一次真实上传准备流程。不同年代教程的张数、体积和缩略图要求可能不一致；本skill区分后台截图要求、本次实用规格和制作建议，使用时以当前后台为准。

## 调用示例

```text
用 $wechat-sticker-publisher 做一套原创动物表情。
先给我角色方向和16张静态确认稿，确认后再做动态。
准备专辑、个人主页、赞赏三个模块的适用素材与文案。
```

```text
用 $wechat-sticker-publisher 补齐已有表情包的上架材料。
保留我已确认的角色，先列缺项，再制作缺少的图片和文案。
```

## 可移植性

Python工具支持Python 3.9+，依赖Pillow。包含已确认动作帧的GIF编码、精确尺寸和体积的图片导出、只读图片检查。详细命令和输入约定见 [工具使用说明](references/tools.md)。

检查已制作的动态表情，例如：

```bash
python3 -m pip install -r requirements.txt
python3 scripts/inspect_images.py ./stickers --width 240 --height 240 --require-animation --require-loop --require-transparency --output ./image-checks.json
python3 -m unittest discover -s tests -v
```

尺寸、数量、体积限制可按当前后台要求配置；动画必须经过另行视觉验收，检查脚本不能判断画风一致或没有漂移。

## 许可证与公开范围

- 仓库名：`wechat-sticker-publisher`
- 许可证：[MIT](LICENSE)，适用于代码、文档和已授权示例。
- 当前公开示例为 `examples/goose` 中的大鹅GIF；其余角色作品、账户资料、聊天记录和后台截图不自动纳入公开内容。
