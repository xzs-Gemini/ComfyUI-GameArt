# ComfyUI-GameArt｜Searge 游戏美术台

**在中文网页中填写描述、上传参考图或蒙版，用自己电脑的显卡生成和修改角色、场景、道具概念图。**

这是基于 [ComfyUI](https://github.com/Comfy-Org/ComfyUI) 与 [SeargeSDXL](https://github.com/SeargeDP/SeargeSDXL) 的本地单用户工作台。它把一组常用 SDXL 工作流整理成表单，方便不熟悉节点的人操作，也能保存结果和 API 工作流供开发者继续调整。

**它是现有生成能力的简化界面，不是新模型，也不会仅因换了界面就提高画质。** 当前产出是二维图片，不是可以直接导入游戏的完整 3D 模型、骨骼动画或角色资产包。

> 当前版本：Windows / NVIDIA 源码原型。需要自己安装环境并下载 SDXL Base 1.0 模型。实际生成不需要 LibTV、OpenAI 或其他平台账号和 API Key，计算发生在本机。本仓库不是 ComfyUI 或 SeargeSDXL 官方产品。

## 目录

- [能用来做什么](#能用来做什么)
- [与原版有什么区别](#与原版有什么区别)
- [它如何运作](#它如何运作)
- [安装与首次启动](#安装与首次启动)
- [使用方法](#使用方法)
- [参数说明](#参数说明)
- [任务结果与数据](#任务结果与数据)
- [常见问题](#常见问题)
- [开发与验证](#开发与验证)

## 能用来做什么

| 功能 | 使用场景 | 输出 |
| --- | --- | --- |
| 文字生成图片 | 探索角色服装、游戏场景、道具外观 | PNG 概念图 |
| 参考图改绘 | 在草图或已有图片基础上调整细节和风格 | 改绘后的 PNG |
| 蒙版局部重绘 | 修改披风、武器、背景的一部分 | 合成回原图的 PNG |
| 批量候选方案 | 一次提交多条描述，逐张生成 | 按任务整理的结果 |
| 保存参数与工作流 | 追溯配置、再次生成或继续开发 | 参数 JSON、ComfyUI API 工作流 JSON |
| 2 倍尺寸放大 | 将输出宽高各扩大一倍 | 插值放大的图片 |

例如，先生成一个“绿色披风的森林游侠”，选择满意的图上传为参考图，再用白色蒙版标出披风，尝试修改颜色和材质。局部重绘仍受模型能力影响，不保证每次准确完成文字要求。

暂未实现：角色 LoRA 训练、跨场景身份一致性、自动抠图、精灵动画、3D 建模、游戏引擎资源打包和真正的 AI 超分。白色背景不等于透明背景，固定种子也不等于角色一致性。

## 与原版有什么区别

ComfyUI 是通用的 AI 工作流工具，原本就能生成和修改图片；SeargeSDXL 提供 SDXL 节点及工作流。本项目主要降低常见操作的上手成本。

| 原版操作 | 本项目提供 |
| --- | --- |
| 导入工作流、找到节点并调整参数 | 中文表单：类型、风格、描述、尺寸、步数 |
| 自己组合常用提示词 | 角色／场景／道具，以及四种画风预设 |
| 在节点中配置参考图与蒙版 | 文件上传与改动程度控件 |
| 自己整理参数和输出 | 任务记录、图片、参数和 API 工作流按目录保存 |
| 处理本次遇到的插件接口变化 | 可重放的 Searge 兼容补丁及固定上游版本 |

熟悉 ComfyUI 的用户仍可直接使用完整节点界面；本工具只开放一组常用配置。当前界面限定使用 SDXL Base 1.0，不能直接切换到 Flux、SD 1.5 等模型。上游完整 Reborn 工作流、Refiner、ControlNet、FreeU 等组合没有全部验证。

## 它如何运作

这里有两个本机服务：

| 服务 | 默认地址 | 职责 |
| --- | --- | --- |
| 游戏美术台 | `http://127.0.0.1:5213` | 表单、上传、任务队列、结果下载 |
| ComfyUI 引擎 | `http://127.0.0.1:8189` | 加载模型、执行节点、使用显卡生成 |

工作过程：

1. 网页把描述和配置发送给本地 Python 工作台。
2. 工作台保存任务，组合素材类型、画风及用户提示词，构建 ComfyUI API 工作流。
3. Searge 自定义节点负责提示词组合与 SDXL 编码；标准 ComfyUI 节点负责采样、解码和保存。
4. 有参考图时，先缩放裁切并编码；有蒙版时，在指定区域加噪重绘，再合成回原图。
5. 工作台从本机引擎读取结果，整理图片、参数及工作流，供网页下载。

生成使用本机算力，不提交到 LibTV 云端。安装代码、依赖和模型需要网络；装齐后，这套生成流程不要求云端推理账号。运行时仍会消耗本机显存、内存、磁盘空间和电力。

## 安装与首次启动

以下步骤针对 Windows x64、NVIDIA 显卡及 PowerShell。每段命令在同一项目目录执行，某步失败时先处理错误，再执行下一步。

### 1. 准备环境

| 项目 | 已验证配置／要求 |
| --- | --- |
| 系统 | Windows；其他系统未验证 |
| Python | 3.12 |
| 显卡 | RTX 5060 Laptop 8GB 已实测；这不是所有硬件的最低配置承诺 |
| PyTorch | 2.7.1 + CUDA 12.8 构建，需兼容的 NVIDIA 驱动 |
| 磁盘 | 模型约 6.94 GB，另需容纳 Python、PyTorch、引擎和生成图片 |
| 工具 | Git、PowerShell、浏览器 |

本项目采用独立环境，不需要修改已有 ComfyUI Desktop。已有虚拟环境不要直接从别人的电脑复制，按下方命令在自己的电脑创建。

```powershell
git --version
py -3.12 --version
nvidia-smi
```

若没有 `py`，但 `python --version` 是 3.12，可用 `python` 替换下面创建环境时的 `py -3.12`。

### 2. 下载源码及固定版本的引擎

在准备存放项目的目录打开 PowerShell：

```powershell
git clone https://github.com/xzs-Gemini/ComfyUI-GameArt.git
cd ComfyUI-GameArt
py -3.12 -m venv .venv

git clone https://github.com/Comfy-Org/ComfyUI.git ComfyUI
git -C ComfyUI checkout ee71d5c4993f29086b27fde1629a945ae48425bf

git clone https://github.com/SeargeDP/SeargeSDXL.git ComfyUI/custom_nodes/SeargeSDXL
git -C ComfyUI/custom_nodes/SeargeSDXL checkout 2eb5edbc712329d77d1a2f5f1e6c5e64397a4a83
```

固定提交是为了匹配已验证的接口。Git 提示处于 `detached HEAD` 是检出指定提交的正常结果，不要因此直接切换回最新版分支。

### 3. 应用 Searge 补丁

```powershell
$patchPath = (Resolve-Path ./patches/searge-gameart.patch).Path
git -C ComfyUI/custom_nodes/SeargeSDXL apply --check $patchPath
git -C ComfyUI/custom_nodes/SeargeSDXL apply $patchPath
```

补丁新增 `SeargeGameArtConditioning` 节点、修复 SDXL 编码接口，并将影响全部工作流的 UNet 全局替换改为模型包装器中的局部处理。**首次安装只应用一次。** 若检查失败，先确认版本和是否已经应用，不要忽略报错继续安装。

### 4. 安装依赖并检查显卡

```powershell
./.venv/Scripts/python.exe -m pip install --upgrade pip
./.venv/Scripts/python.exe -m pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
./.venv/Scripts/python.exe -m pip install -r requirements-runtime.txt -c torch-constraints.txt
./.venv/Scripts/python.exe -m pip check
./.venv/Scripts/python.exe -c "import torch; print('PyTorch:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"
```

预期 `pip check` 不报告依赖冲突，`CUDA available` 为 `True`。这只是安装检查，不能替代实际生成验证。命令使用虚拟环境里的 Python，不要求先激活环境。

`requirements-lock.txt` 是开发环境完整版本快照；上面使用的是运行依赖清单及 PyTorch 约束，不保证未来所有依赖更新都兼容。不要直接把 PyTorch 升级到最新版来覆盖已验证组合。

### 5. 下载 SDXL Base 1.0 模型

需要文件：`sd_xl_base_1.0.safetensors`。模型由 Stability AI 发布，来源说明也可从 [Stability AI 官方 GitHub](https://github.com/Stability-AI/generative-models) 中的 SDXL 条目查看。

以下命令从发布方的 Hugging Face 仓库下载；地址在 2026-10-11 检查可访问。下载约 6.94 GB，可能耗时较长。已有完整模型时可直接复制到相同目录，不必重复下载。

```powershell
New-Item -ItemType Directory -Force models/checkpoints | Out-Null
curl.exe -L --fail --retry 3 -o models/checkpoints/sd_xl_base_1.0.safetensors 'https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors'
(Get-FileHash ./models/checkpoints/sd_xl_base_1.0.safetensors -Algorithm SHA256).Hash
```

预期 SHA256：

```text
31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b
```

大小写不影响哈希比较。若不一致，不要使用该文件启动生成，检查下载是否完整或是否下载了不同模型。使用模型需遵守发布方提供的模型许可，仓库代码许可不替代模型许可。

最终路径应为：

```text
ComfyUI-GameArt/
  .venv/
  ComfyUI/
    custom_nodes/SeargeSDXL/
  models/
    checkpoints/sd_xl_base_1.0.safetensors
  gameart/
  extra_model_paths.yaml
  Start-GameArt.ps1
```

`extra_model_paths.yaml` 将本仓库的 `models/` 加入引擎搜索路径。只下载源码 ZIP 不会自动取得模型、ComfyUI 或运行环境。

### 6. 启动与首次检查

```powershell
./Start-GameArt.ps1
```

或双击 `Start-GameArt.cmd`。脚本会启动本机引擎和工作台，并打开 `http://127.0.0.1:5213`。等待引擎完成启动后点击页面“刷新”。

成功标志：页面顶部显示本地设备信息，“更多参数”里出现 `sd_xl_base_1.0.safetensors`，提交按钮可用。首张图通常还要等待模型加载，不要连续重复提交。

若系统禁止执行 PowerShell 脚本，或者需要直接查看运行日志，可用两个终端以前台方式启动，不需要修改系统执行策略。先确认没有已有实例占用端口。

终端 A，在仓库根目录执行：

```powershell
cd ComfyUI
../.venv/Scripts/python.exe main.py --listen 127.0.0.1 --port 8189 --extra-model-paths-config ../extra_model_paths.yaml --disable-api-nodes --preview-method none
```

终端 B，在仓库根目录执行：

```powershell
./.venv/Scripts/python.exe -m gameart.server
```

然后手动打开网页。两个终端都要保持运行，按 `Ctrl+C` 停止对应服务。

## 使用方法

### A. 用一句描述生成第一张图

1. 素材类型选择“道具”，视觉风格选择“游戏概念设计”。
2. 点击“提灯”示例，或填入下面的描述。
3. 第一次可选 `768 × 768`、12 步测试链路；成功后再尝试 `1024 × 1024`、20 步。
4. 点击“加入队列，开始出图”，等待右侧任务变为“已完成”。
5. 点击图片下载 PNG，也可以下载参数和工作流。

```text
a brass lantern with warm amber light, white background
```

### B. 批量生成多个候选方案

每个非空行生成一张图，每批最多 20 条，按顺序执行。同一批使用相同类型、风格和参数；留空种子时随机产生起始种子，后续任务依次加一。希望同一描述得到多个候选图，可以重复填写该描述。

```text
a brass lantern with warm amber light, white background
a silver sword with a blue gemstone, white background
a leather travel backpack with brass buckles, white background
```

界面是中文，但没有内置提示词翻译器。可先用页面英文示例测试，再逐步改写主体、颜色、材质和场景。

### C. 参考图改绘

1. 展开“参考图与局部重绘”，上传 PNG、JPEG 或 WebP 图片。
2. 不上传蒙版，填写目标画面的描述。
3. 选择输出尺寸，设置“改动程度”，再提交。

改动程度越高，结果通常越偏离原图；较低时更容易保留原有结构。默认值为 0.65。参考图会按所选尺寸缩放并居中裁切，不保证保留原图全部边缘。

### D. 局部重绘

1. 上传参考图，并准备与它构图、比例一致的黑白蒙版。
2. 将希望修改的区域涂白，其余区域涂黑；建议使用相同像素尺寸的蒙版。
3. 上传蒙版，填写修改目标，例如把披风改为蓝色。
4. 设置改动程度并提交。需要自然边界时，可在外部绘图工具里给蒙版边缘适当过渡。

白色区域参与重绘，黑色区域在最终合成时保留经过缩放裁切后的参考图；灰色边缘会混合。这里读取的是蒙版图像亮度颜色区域，不要只依赖透明通道。当前没有网页内的蒙版画笔，需要自己准备蒙版文件。

参考图和蒙版每个文件最多 20 MB，后端限制图像最多 3200 万像素。一次批量任务共用本次上传的参考图和蒙版。上传选择会保留在表单中，想恢复纯文字生成时先清空文件选择。

## 参数说明

| 参数 | 含义与使用方式 |
| --- | --- |
| 素材类型 | 添加角色、场景或道具的构图提示；不是切换专用训练模型 |
| 视觉风格 | 添加概念、动漫、手绘或写实风格提示；不是加载 LoRA |
| 尺寸 | 1024 方图、832×1216 角色竖图、1216×832 场景横图、768 方形草稿 |
| 细化步数 | 界面提供 12、20、30 步；更多步数增加计算量，不保证必然更好 |
| 提示词强度 CFG | 默认 7，调整模型对提示词的响应；数值过高可能影响画面质量 |
| 随机种子 | 留空随机；相同环境、模型、提示词和参数下有助于复现，跨环境不保证逐像素一致 |
| 不希望出现的内容 | 负面提示词，例如 `text, watermark, blurry`，不是绝对禁止条件 |
| 改动程度 | 仅在使用参考图时生效；纯文字生成使用完整采样 |
| 2 倍插值放大 | 宽高各乘 2，采用 Lanczos 插值，不会额外调用超分模型 |

固定种子不是“锁定角色”。同一批任务种子依次递增，想复现某一张图，应使用该任务保存的实际种子和全部参数。

## 任务结果与数据

| 位置 | 内容 |
| --- | --- |
| `data/jobs.json` | 工作台任务和状态 |
| `data/outputs/<任务ID>/result-1.png` | 输出图片 |
| 同目录 `parameters.json` | 提示词、参数、种子等 |
| 同目录 `workflow-api.json` | 供 ComfyUI API 使用的节点图 |
| `ComfyUI/input/gameart-*.png` | 上传后转换保存的参考图和蒙版 |
| `ComfyUI/output/GameArt/` | 引擎自己的原始输出 |
| `data/comfy.log`、`data/comfy-error.log` | 引擎日志 |
| `data/app.log`、`data/app-error.log` | 工作台日志 |

API 工作流不包含模型或原始参考图，也不包含完整编辑器画布布局；移到其他机器使用时仍需相应模型、自定义节点和输入图片，不能视为自包含素材包。

“等待中”任务可取消；已提交的生成没有在此界面提供取消按钮。提交中断后出现“需要核对”时，点击“核对任务”，工作台会检查本机引擎队列及历史，不会自动重复提交。引擎重启导致历史丢失时可能无法恢复核对，先查看输出文件，再决定是否重建任务。

关闭网页不会停止后台或释放显存。采用前台启动时用两个终端的 `Ctrl+C` 分别结束；采用脚本后台启动时，目前需在任务管理器确认本项目的进程后结束，勿批量结束所有 Python 进程。备份应在停止服务后进行，保留 `data/` 以及需要继续使用的输入图。

本项目没有网站账号、用户权限与任务隔离。同机同一实例共用显卡和历史记录。两个服务只监听 `127.0.0.1`，把地址发给别人不会让别人访问你的机器。仓库不包含个人上传图、生成图、模型及虚拟环境。

## 常见问题

| 问题 | 检查与处理 |
| --- | --- |
| 页面显示“引擎尚未就绪” | 等待启动后点“刷新”；查看 `data/comfy-error.log`，确认 8189 引擎运行 |
| 找不到模型／提交按钮不可用 | 核对文件名、目录和 SHA256；模型需在 `models/checkpoints/`，下载完整后重新启动引擎并刷新 |
| 提示缺少 `SeargeGameArtConditioning` | 检查固定版本与补丁是否应用，查看插件加载日志，然后重启引擎 |
| CUDA available 为 False | 核对 NVIDIA 驱动及虚拟环境内的 PyTorch 构建，不能只检查系统 Python |
| 显存不足 | 关闭其他占用显存的软件，先用 768 方图测试；不能保证所有显卡均能运行 |
| 局部重绘改错位置 | 核对蒙版白黑方向、原图与蒙版比例以及居中裁切造成的位置变化 |
| 换图片后结果仍像上一张 | 检查表单中的参考图与蒙版是否仍被选中，清空后再做文生图 |
| 生成失败／任务需要核对 | 先读任务错误和引擎日志、查看队列历史，不要连续重复提交 |
| 补丁报 already exists／不适用 | 确认 Searge 提交及是否已应用；不要反复套用或覆盖未知的本地修改 |
| 其他模型不出现在列表 | 当前工作流只开放 SDXL Base 1.0；不是任意模型加载器 |

## 开发与验证

| 文件 | 职责 |
| --- | --- |
| `gameart/workflow.py` | 提示词预设、ComfyUI API 节点图构建 |
| `gameart/server.py` | 本地任务、上传、引擎调用、结果与恢复 |
| `gameart/web/` | 中文前端 |
| `patches/searge-gameart.patch` | 新节点及 Searge 兼容修复 |
| `SOURCE_VERSIONS.json` | 上游提交及模型校验信息 |
| `requirements-runtime.txt`、`torch-constraints.txt` | 安装依赖及 PyTorch 固定版本 |
| `requirements-lock.txt` | 开发环境完整依赖快照 |

可从提示词模板、文件命名、分类导出继续开发。角色一致性、LoRA 训练、图集导出及多人权限需要额外实现，不是更换页面选项即可获得的功能。

离线工作流测试，不调用显卡生成：

```powershell
./.venv/Scripts/python.exe -m unittest discover -s tests -p test_workflow.py -v
```

`tests/smoke_local.py` 是显式集成测试，会执行真实生成，并依赖工作台中已有一张已完成的图片；不是首次安装的必跑步骤。

2026-10-11 已验证：5 项工作流测试通过，真实生成 1024×1024 文生图、768×768 参考图改绘，以及修正后的蒙版重绘与 2 倍插值输出；CUDA 运算及模型 SHA256 检查通过。详细过程和局部重绘修复记录见 [VALIDATION.md](VALIDATION.md)。测试输出属于开发机本地文件，未包含在公开仓库。

尚未完成的验证：另一台全新电脑从零安装、全部硬件、上游完整 Reborn 工作流和所有旧节点组合。发布安装步骤不等于已经验证所有环境。

安装补充见 [INSTALL.md](INSTALL.md)。新增代码使用 [MIT 许可证](LICENSE)，Searge 修改保留原许可，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)；引擎和模型分别遵循其发布方许可。
