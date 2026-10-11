# Searge 游戏美术台

基于 [SeargeDP/SeargeSDXL](https://github.com/SeargeDP/SeargeSDXL) 的本地二次开发。将 Searge 的 SDXL 提示词组合与编码能力接入简化网页，通过 [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) 执行生成。

## 使用

首次安装请先阅读 [INSTALL.md](INSTALL.md)。这是 Windows 本地单用户源码原型；仓库不包含模型、虚拟环境、ComfyUI 引擎和个人生成数据。功能是简化现有工作流操作，不是新增模型能力。

在 PowerShell 中运行 `./Start-GameArt.ps1`。会启动本机引擎与网页，页面地址为 `http://127.0.0.1:5213`。首次启动需要等待引擎加载，然后点页面“刷新”。已运行时直接打开页面即可。

1. 选择角色、场景或道具，以及概念、动漫、手绘或写实风格。
2. 每行填写一个画面描述。SDXL 对英文理解较好，可先点击“提灯”“游侠”“城堡”示例。
3. 选择尺寸和步数，点击开始。每批最多20张，逐张执行，避免多图同时占显存。
4. 完成后点击图片下载；也可下载参数和 API 工作流。所有输出保存在 `data/outputs/<任务ID>/`。

**改绘**：展开“参考图与局部重绘”，上传原图，调整改动程度。数值越高变化越大。

**局部重绘**：再上传同一构图的黑白蒙版，白色区域重绘，黑色区域保留。原图和蒙版按相同方式居中裁切；使用边缘平滑的蒙版有助于过渡自然。当前使用 SDXL Base 的蒙版采样，不保证每次都严格实现文字要求。

**放大**：“更多参数”可选2倍插值放大。这是尺寸放大，不是额外的超分辨率模型。

固定种子可以复现相同配置，不等于不同场景中的角色身份一致。当前没有角色训练、LoRA管理和自动抠图功能。

## 运行环境

- Windows，RTX 5060 Laptop 8GB；Python 3.12。
- PyTorch 2.7.1+cu128，已实测 CUDA。采用兼容现有驱动的计算路径，未启用要求 CUDA 13 的新优化。
- ComfyUI v0.36.0，提交 `ee71d5c4993f29086b27fde1629a945ae48425bf`。
- SeargeSDXL 提交 `2eb5edbc712329d77d1a2f5f1e6c5e64397a4a83`，保留上游 MIT 授权。
- 模型：Stability AI SDXL Base 1.0，6,938,078,334字节。
- 模型 SHA256：`31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b`，已与发布方元数据核对。
- `.venv/`、`ComfyUI/`、`models/` 为此项目独立目录，原 Comfy Desktop 安装无需改动。

网页端口5213；ComfyUI引擎端口8189。均仅监听127.0.0.1。运行日志在 `data/`。关闭网页不会结束后台生成。

## 二次开发结构

- `gameart/workflow.py`：构建可导出的 ComfyUI API 工作流。
- `gameart/server.py`：本地任务保存、队列、图片上传、结果下载。提交中断不会自动重复提交。
- `gameart/web/`：中文操作界面。
- `ComfyUI/custom_nodes/SeargeSDXL/modules/game_art.py`：新增的 Searge 游戏美术条件编码节点，复用原项目的提示词组合和编码。
- `patches/searge-gameart.patch`：全部 Searge 修改的可重放补丁。
- `requirements-lock.txt`：本次验证的完整依赖版本。

补丁修复了 SDXL 编码器由 `encode` 改为 `execute` 的接口差异，并将原项目导入时对 UNet 的全局替换改为模型包装器内处理，避免加载插件就改变其他工作流。

本交付验证的是**新增简化工作流**。上游整套 Reborn 工作流中的 Refiner、ControlNet、FreeU 和所有旧节点组合没有逐一验证，不能据此宣称完整兼容。

运行单元测试：`.venv/Scripts/python.exe -m unittest discover -s tests -v`。

`tests/smoke_local.py` 是显式集成测试，会使用本机显卡执行任务，不属于普通单元测试。实际测试结果见 `data/smoke-report.json`。

## 下一步扩展

可围绕现有工作流添加指定游戏的风格模板、素材命名与分类导出、经过训练的角色 LoRA、真正的模型超分辨率，以及与 LibTV 视频节点连接。当前版本先完成本地美术素材生成与编辑。
