# Windows / NVIDIA 源码安装

当前是本地单用户工具。没有账号注册、API Key 或云端推理依赖；生成使用本机显卡。已验证 Python 3.12、RTX 5060 Laptop 8GB 和 PyTorch 2.7.1+cu128，其他硬件未逐一验证。仓库不包含模型、虚拟环境、生成记录或整个 ComfyUI。

先安装 Git、Python 3.12 及兼容的 NVIDIA 驱动。克隆本仓库并进入目录，在 PowerShell 中逐条执行；任一命令失败时先处理错误，再执行下一条。

```powershell
py -3.12 -m venv .venv
git clone https://github.com/Comfy-Org/ComfyUI.git ComfyUI
git -C ComfyUI checkout ee71d5c4993f29086b27fde1629a945ae48425bf
git clone https://github.com/SeargeDP/SeargeSDXL.git ComfyUI/custom_nodes/SeargeSDXL
git -C ComfyUI/custom_nodes/SeargeSDXL checkout 2eb5edbc712329d77d1a2f5f1e6c5e64397a4a83
$patchPath = (Resolve-Path ./patches/searge-gameart.patch).Path
git -C ComfyUI/custom_nodes/SeargeSDXL apply --check $patchPath
git -C ComfyUI/custom_nodes/SeargeSDXL apply $patchPath
./.venv/Scripts/python.exe -m pip install --upgrade pip
./.venv/Scripts/python.exe -m pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
./.venv/Scripts/python.exe -m pip install -r requirements-runtime.txt -c torch-constraints.txt
./.venv/Scripts/python.exe -m pip check
New-Item -ItemType Directory -Force models/checkpoints
```

补丁只需应用一次。升级依赖前备份环境，不能保证任意上游最新版都兼容。`requirements-lock.txt` 是开发机完整环境快照，安装步骤使用必要运行依赖和固定的 PyTorch 约束。

从 Stability AI 的发布渠道获取 `stabilityai/stable-diffusion-xl-base-1.0` 中的 `sd_xl_base_1.0.safetensors`，按模型发布方条款使用，放入 `models/checkpoints/`。模型约 6.94 GB，下载与运行需要额外磁盘空间。本仓库不重新分发模型。

```powershell
(Get-FileHash ./models/checkpoints/sd_xl_base_1.0.safetensors -Algorithm SHA256).Hash
```

预期 SHA256：`31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b`。

随后运行 `./Start-GameArt.ps1` 或双击 `Start-GameArt.cmd`。界面为 `http://127.0.0.1:5213`，引擎为 `http://127.0.0.1:8189`。首次加载需要等待，日志在 `data/`。模型配置使用仓库相对路径，移动目录后无需修改盘符。

## 检查

```powershell
./.venv/Scripts/python.exe -m unittest discover -s tests -p test_workflow.py -v
```

该命令不执行生成。`tests/smoke_local.py` 会使用显卡实际生成，并依赖工作台已经生成的一张图片，需显式运行。验证记录中的本地输出不随仓库分发。

## 边界

两项服务仅监听本机，没有多人账户及文件隔离。不要将服务直接对公网开放。当前是常用 SDXL 工作流的简化界面，不能替代完整 ComfyUI，也不包含角色训练、自动游戏引擎导出或 AI 超分功能。

上游 ComfyUI、SeargeSDXL 和模型分别保留其自己的许可；见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
