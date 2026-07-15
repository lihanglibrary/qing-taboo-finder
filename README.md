# QingTabooFinder 清代避讳定位器

QingTabooFinder 清代避讳定位器是一个面向古籍研究的本地 Python 工具。

它用于在已经整理或 OCR 完成的古籍文本（TXT / DOCX / EPUB）中，快速定位清代避讳相关字词的出现位置，辅助研究者回到古籍图像或古籍实物进行实证校勘与版本判断。

## Contents 目录

- [项目意义](#project-significance-项目意义)
- [作者](#author-作者)
- [许可证](#license-许可证)
- [项目目录结构](#repository-layout)
- [规则数据文件](#data-file)
- [可选避讳项目](#selectable-categories-可选避讳项目)
- [逐步使用指南](#step-by-step-guide-逐步使用指南)
  - [开始前准备](#before-you-start-开始前准备)
  - [迁移项目或上传 GitHub](#move-or-publish-迁移项目或上传-github)
  - [Windows 使用指南](#windows-guide-windows-使用指南)
  - [macOS 使用指南](#macos-guide-macos-使用指南)
  - [第一次查验](#run-your-first-check-第一次查验)
  - [选择查验项目](#choose-check-categories-选择查验项目)
  - [查验自己的文本](#check-your-own-text-查验自己的文本)
  - [阅读报告](#read-the-report-阅读报告)
  - [修改规则表](#edit-the-rule-table-修改规则表)
  - [一次性命令](#optional-command-line-use-可选一次性命令)
  - [常见问题](#common-problems-常见问题)
- [输出文件](#output)
- [学术背景与研究提示](#academic-background-学术背景与研究提示)

## Project Significance 项目意义

在古籍与古典文献研究中，避讳往往是判断版本年代和流传层次的重要线索。

实际工作中常见困难是：

- 研究者很难在长篇文本里手工筛到合适的避讳字证据。
- 找到疑似字形后还需要人工比对原刻本、抄本或影印本，成本很高。

本项目的价值在于：

- 先在已经整理好的电子文本里批量定位避讳线索。
- 输出章节、位置、上下文、所属皇帝等定位信息。
- 使用者可以利用定位结果回溯到古籍图像或者古籍实物，提升版本考据效率。

## Author 作者

- Creator: Hang Li

## License 许可证

- MIT License
- See [LICENSE](LICENSE)

## Repository Layout

```text
.
├── data/
│   └── qing_taboo.csv
├── examples/
│   └── tao_hua_shan_excerpt.txt
├── qing_taboo_finder/
│   ├── cli.py
│   ├── constants.py
│   ├── csv_loader.py
│   ├── detector.py
│   ├── exporter.py
│   ├── models.py
│   ├── segmenter.py
│   ├── taboo_rules.py
│   └── readers/
├── run.py
├── requirements.txt
├── pyproject.toml
└── LICENSE
```

## Data File

统一规则文件为：

- [data/qing_taboo.csv](data/qing_taboo.csv)

该文件包含以下列：

- `序号`、`皇帝`、`皇帝简体名`、`皇帝繁体名`
- `避讳1 繁体名单字拆分`、`避讳2 簡体名单字拆分`
- `避讳3 可能需要避讳的同偏旁字`、`避讳4 替代字`
- `避讳5 避讳后的专有词汇 简体`、`避讳6 避諱後的專有詞彙 繁体`
- `避讳7 避讳前的专有词汇 简体`、`避讳8 避諱前的專有詞彙 繁体`

## Selectable Categories 可选避讳项目

交互界面支持以下项目：

- `避讳1 繁体名单字拆分`
- `避讳2 簡体名单字拆分`
- `避讳3 可能需要避讳的同偏旁字`
- `避讳4 替代字`
- `避讳5 避讳后的专有词汇 简体`
- `避讳6 避諱後的專有詞彙 繁体`
- `避讳7 避讳前的专有词汇 简体`
- `避讳8 避諱前的專有詞彙 繁体`

每一项都与 [data/qing_taboo.csv](data/qing_taboo.csv) 的同序列表头对应。程序报告中的“命中类别”仍使用简短名称，例如“繁体”“偏旁”或“原 專有詞彙 繁体”，便于阅读。

## Step-by-Step Guide 逐步使用指南

本节面向第一次使用命令行的研究者。项目使用跨平台的 Python 和文件路径处理方式，Windows 与 macOS 都可以直接运行，不需要修改程序代码。每一行命令输入后按一次回车键执行。

### Before You Start 开始前准备

请准备以下内容：

- 一台已安装 Python 3.10 或更高版本的电脑。
- 待查验的电子文本，格式可以是 TXT、DOCX 或 EPUB。建议使用古籍的整理本电子书。
- 本项目文件夹。请不要移动或改名其中的 `qing_taboo_finder` 文件夹、`data/qing_taboo.csv` 和 `run.py`。

### Move or Publish 迁移项目或上传 GitHub

程序使用相对路径读取 `data/qing_taboo.csv`、示例文件和默认 `outputs` 目录，移动整个项目文件夹后不需要修改代码或创建 `.env` 文件。

但 Python 虚拟环境 `.venv` 记录了创建时的绝对路径。项目移动后，请删除旧 `.venv`，再按当前系统对应的“第一次安装所需组件”步骤重新创建并安装依赖。`.venv`、报告文件、编辑器配置和 `.env` 已被 `.gitignore` 排除，不应上传到 GitHub。

上传前请确认示例 TXT 的原始作品及规则 CSV 具有公开分发授权；节选内容也可能受版权限制。个人待查验文本应存放在项目外部，或加入 `.gitignore` 后再提交。

### Windows Guide Windows 使用指南

#### 1. 安装 Python

访问 [Python 官网下载页](https://www.python.org/downloads/windows/) 并安装 Python 3.10 或更高版本。安装界面出现时，务必勾选 **Add Python to PATH**，然后选择“Install Now”。安装完成后关闭并重新打开终端。

#### 2. 打开 PowerShell 并进入项目文件夹

按 Windows 键，搜索并打开 **PowerShell** 或 **Windows Terminal**。在资源管理器中打开项目文件夹，单击地址栏后复制路径；回到 PowerShell 输入 `cd `（`cd` 后有一个空格），粘贴路径并按回车。例如：

```powershell
cd "C:\Users\你的用户名\Developer\QingTabooFinder"
```

输入以下命令。若输出中有 `run.py` 与 `data`，说明位置正确：

```powershell
dir
```

#### 3. 第一次安装所需组件

在 PowerShell 中依次输入以下三条命令。这些操作只需首次使用时执行一次：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

若第二条命令提示“禁止运行脚本”，先执行下面这条命令，再重复激活命令。它只对当前 PowerShell 窗口生效，不会永久修改电脑设置：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

成功激活后，命令行开头通常会显示 `(.venv)`。以后每次重新打开 PowerShell 时，先进入项目文件夹，再执行：

```powershell
.\.venv\Scripts\Activate.ps1
```

#### 4. 启动程序

在已激活的环境中运行：

```powershell
py run.py
```

然后按照下方“Run Your First Check 第一次查验”的四个问题依次输入即可。

### macOS Guide macOS 使用指南

#### 1. 打开终端并进入项目文件夹

在 macOS 中打开“终端”应用。将项目文件夹拖进终端窗口，会自动输入其路径；然后在路径前输入 `cd `（`cd` 后有一个空格），例如：

```bash
cd ~/Developer/QingTabooFinder
```

输入下面的命令确认终端已经进入项目文件夹。若输出中能看到 `run.py` 和 `data`，说明位置正确：

```bash
ls
```

#### 2. 第一次安装所需组件

下面三条命令只需在首次使用时执行一次。它们会在项目文件夹中建立独立的 Python 环境，并安装读取 Word、EPUB 和 Excel 所需的组件。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

完成后，终端行首通常会出现 `(.venv)`。以后每次重新打开终端并进入项目文件夹时，先执行：

```bash
source .venv/bin/activate
```

若系统提示找不到 `python3`，请先安装 Python 3，再从本节第 2 步重新执行。若你使用 Anaconda，也可以改为启用自己已经安装依赖的 Python 环境。

#### 3. 启动程序

在已激活的环境中运行：

```bash
python3 run.py
```

然后按照下方“Run Your First Check 第一次查验”的四个问题依次输入即可。

### Run Your First Check 第一次查验

项目的 `examples` 文件夹中有 `tao_hua_shan_excerpt.txt`，可用于确认 TXT 读取与避讳查验功能是否正常。该文件是原始作品正文的节选；请仅在原始作品可公开分发时上传到 GitHub。若其来源或授权不明确，请只保留在本地，不要随项目公开发布。

Windows 用户输入：

```powershell
py run.py
```

macOS 用户输入：

```bash
python3 run.py
```

程序会依次提问。可按以下方式回答：

1. **规则文件路径**：提示 `请输入合并后 CSV 文件路径` 时，直接按回车，使用默认的 `data/qing_taboo.csv`。
2. **待查验文档路径**：先输入 `examples/tao_hua_shan_excerpt.txt` 测试。正式查验时，输入自己的文本路径。最简单的方式是把文件拖进终端窗口，终端会自动填入完整路径，再按回车。
3. **目标皇帝**：程序会列出皇帝并显示序号。输入序号，例如输入 `6` 选择道光。程序会同时纳入康熙至该皇帝之间的累计避讳规则。
4. **查验项目**：输入需要检查的编号、编号范围或组合，具体规则见下一节。

程序结束时会显示两条“已导出”信息。报告默认位于 `outputs` 文件夹中。

### Choose Check Categories 选择查验项目

无需逐项输入。建议按研究问题选择以下快捷输入：

| 输入内容 | 检查范围 | 适用情况 |
| --- | --- | --- |
| `1-4` | 避讳 1 至 4 | 查找避讳字、简体写法、同偏旁字与替代字；这是最常用的基础查验。 |
| `5-6` | 避讳后专有词汇 | 查找已经因避讳而改变的地名、人名、年号或其他专名。 |
| `7-8` | 避讳前专有词汇 | 有些古籍整理本会将古籍中的避讳改为原字。 |
| `1-8` 或 `全部` | 全部八类 | 需要完整排查时使用；结果可能较多。 |
| `1-4,6` | 自定义组合 | 同时查基础单字与“避讳后专有词汇繁体”。 |

中文逗号也可以使用，例如 `1-4，6`。输入的编号与上方“Selectable Categories”中的顺序一致。

### Check Your Own Text 查验自己的文本

完成示例测试后，重新运行。Windows 用户输入：

```powershell
py run.py
```

macOS 用户输入：

```bash
python3 run.py
```

在第二步输入自己的文件路径。例如，文本放在桌面时可能是：

```text
/Users/你的用户名/Desktop/某部古籍.txt
```

文件名或路径中含空格、中文、圆括号时无需手动改名，直接拖入终端即可。程序会自动读取 TXT、DOCX 或 EPUB 文件，并按标题或固定长度将文本分段。

### Read the Report 阅读报告

每次查验会生成两种内容相同的报告：

- `*_避讳查验报告.csv`：可用 Excel、Numbers 或 WPS 打开，适合筛选和再整理。
- `*_避讳查验报告.xlsx`：Excel 工作簿格式，适合直接查看。

报告先按“皇帝序号”从大到小排列。每一行是一次文本命中，重点字段如下：

| 字段 | 含义 |
| --- | --- |
| 命中字 | 在电子文本中找到的字或词。 |
| 命中类别 | 该命中来自哪一类规则，例如“繁体”“偏旁”或“专有词汇 简体”。 |
| 所属皇帝 / 皇帝序号 | 该规则对应的皇帝及其规则序号。 |
| 是否前朝累计避讳 | “是”表示该规则来自目标皇帝之前的朝代；“否”表示来自本朝。 |
| 全文位置 / 分段位置 | 该命中在全文和所在分段中的字符位置，便于回到电子文本。 |
| 命中上下文 | 命中位置附近的一小段文字，是人工核对的直接线索。 |

报告中的命中只表示“符合规则表的候选位置”，并不单独构成版本断定。请结合原书影、刻印字形、上下文语义与版本信息进行复核。

### Edit the Rule Table 修改规则表

规则表位于 [data/qing_taboo.csv](data/qing_taboo.csv)，可用 Excel、Numbers 或 WPS 打开。修改前请复制一份备份。

1. 不要改变 12 个列的顺序，也不要增删表头。
2. 在同一单元格中填写多个字词时，用英文分号 `;` 分隔，例如 `玄;燁`。
3. 单字类规则填写单个字；专有词汇类规则可以填写多个字的词语。
4. 修改后另存时选择 UTF-8 编码的 CSV 格式；若软件询问是否保留当前格式，请选择保留 CSV 格式。
5. 重新运行程序，新的规则会自动生效，无需修改程序代码。

若 Excel 打开 CSV 时出现乱码，请在 Excel 中通过“数据”中的“从文本/CSV”导入，并选择 UTF-8 编码，而不是直接双击打开。

### Optional Command-Line Use 可选：一次性命令

熟悉命令行后，可以把常用参数写成一条命令，避免逐项回答问题。下面示例检查道光朝、基础单字避讳，并将结果写入 `outputs`。Windows 用户输入：

```powershell
py run.py --csv "data/qing_taboo.csv" --document "examples/tao_hua_shan_excerpt.txt" --emperor "道光" --mode combo_traditional_simplified_radical_substitute --output-dir outputs
```

macOS 用户输入：

```bash
python3 run.py \
  --csv "data/qing_taboo.csv" \
  --document "examples/tao_hua_shan_excerpt.txt" \
  --emperor "道光" \
  --mode combo_traditional_simplified_radical_substitute \
  --output-dir outputs
```

一般使用时建议采用前面的交互方式；这条命令适合反复处理同类文件时使用。

### Common Problems 常见问题

**运行后提示“未找到合并后 CSV 文件”**：先确认终端是否位于项目文件夹；Windows 运行 `dir`、macOS 运行 `ls` 后应能看到 `data`。规则文件路径直接按回车即可使用默认值。

**提示“未找到文档”**：请将文件拖进终端，而不是只输入文件名；这样可以避免路径写错。

**输出结果过多**：先使用 `1-4` 进行基础单字查验，或只选择与研究问题有关的范围。避讳 3 的同偏旁字规则通常会产生较多候选项。

**没有输出结果**：确认选择的目标皇帝、规则项目和文本版本；也可先用 `examples/tao_hua_shan_excerpt.txt` 测试程序是否正常运行。

**无法打开 EPUB 或 DOCX**：先激活 Python 环境，再执行 `pip install -r requirements.txt` 以补齐依赖。Windows 的激活命令是 `.\.venv\Scripts\Activate.ps1`；macOS 的激活命令是 `source .venv/bin/activate`。

## Output

程序导出两种报告：

- `*_避讳查验报告.csv`
- `*_避讳查验报告.xlsx`

报告字段包括：

- 文档名
- 分段序号
- 分段标题
- 命中字
- 命中类别
- 所属皇帝
- 皇帝序号
- 是否前朝累计避讳
- 全文位置
- 全文位置百分比
- 分段位置
- 分段位置百分比
- 命中上下文

## Academic Background 学术背景与研究提示

本项目受黄一農教授《清代避諱研究：e考據的學術實踐》启发。该研究提示我们：清代避讳并非一套在各地、各类文献中均匀而严格落实的静态制度，而是在官方规定、地方执行、社会实践与历史惯性共同作用下形成的复杂历史现象。

因此，本工具提供的是可供核查的文本线索，而非自动的断代或版本结论。使用报告时，建议将以下因素一并纳入研究判断：

- **制度与实践的差异**：诏令和讳例不必然会及时、完整地落实于地方志、私人著述或刻本；漏避、迟避和不同避讳形式都可能具有解释意义。
- **官方与社会行为的区别**：部分避讳可能来自个人、家族或特定群体的自主实践，其程度会随身份、地域与文献类型而变化。
- **多重证据的互证**：单一讳字的出现或缺失不足以直接判定文献年代，应结合文本性质、刊刻背景、避讳形态及其他时代特征复核。
- **制度发展的阶段性**：清代避讳经历了逐步形成与完善的过程；康熙时期已有实践，雍正时期后官方讳例的全国性与统一性才更为明确。

本工具旨在降低发现候选证据的成本，最终的考据结论仍应建立在原书影像、版本信息与具体历史语境的综合判断之上。