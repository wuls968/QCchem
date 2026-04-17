# QCchem Visual Workbench Design

## Goal

在不重写现有 QCchem 架构的前提下，把它从“研究工作流平台雏形”推进成一个更完整、更耐看、更适合长期使用的软件产品：

- 既有本地工作台式体验
- 又有高质量导出报告系统
- 两者共用同一套数据模型、可视化语言和可信度边界表达

本轮目标不是先做 MCP，也不是先做更多算法名，而是先把 **端到端使用体验、可视化表达和产品完成度** 打磨到软件级别。

## Visual Direction

最终视觉方向采用：

- **B 为主：Scientific Atelier**
- **A 为骨：Precision Atlas**

具体含义：

- 视觉气质以温润、柔和、带研究出版物感的 `Scientific Atelier` 为主
- 信息结构、可信度表达、benchmark/study/runtime 组织方式以 `Precision Atlas` 的秩序感为主

目标感受不是“很酷的量子界面”，而是：

- 研究人员长期看不会审美疲惫
- 会觉得它高级、克制、有自己的品位
- 同时又不会牺牲严肃性和可信度表达

## Scope

本轮只做产品层与可视化层的大补强，重点覆盖：

1. 本地工作台（result-centric）
2. 高质量报告系统（HTML/Markdown-first，保留后续 PDF）
3. 统一图形语言与可视化组件
4. 运行中心与现有 CLI/workflow 的无缝接入
5. 结构/轨道/活性空间/压缩/资源/运行监控等核心科研页面补齐
6. 3D 分子可视化与 QCSchema 风格数据对齐

明确不做：

- GUI 里的复杂 3D 编辑器
- 先做 MCP server
- 先做完整在线协作系统
- 为了视觉效果扩展不成熟算法
- 为了好看破坏现有 schema / artifact / validated boundary

## Frontend & Data Stack

### Frontend Shell

本轮主工作台优先采用 **Dash** 作为主前端壳层。

原因：

- Dash 原生适合 Python 驱动的多页面交互式数据应用
- 多页面、交互组件、表格与 callback 模式都适合 QCchem 当前 result-centric 工作流
- 它更适合把现有 QCchem Python schema / artifact / workflow 直接接成一个稳定工作台

### Panel 的定位

**Panel 不作为本轮主工作台壳层**，但保留为后续补强方向：

- 更偏 dashboard / monitoring / crossfilter / notebook-adjacent 工作流
- 适合以后做更探索性的科研监控页或轻量嵌入视图

这意味着本轮技术取舍是：

- **Dash = 主工作台**
- **Panel = 预留备选，不进入首轮主壳**

### 3D Molecular Layer

3D 分子层优先采用 **3Dmol.js**。

原因：

- 对小到中等分子结构、轨道表面和 cube 体渲染来说，接入成本和表现力平衡最好
- 很适合结构页、报告页和摘要卡的统一可视化

后续扩展点：

- 更大体系、轨迹、密度或更复杂浏览需求，再补 **NGL / MDsrv**

### Data Interchange Layer

QCchem 数据层继续以自有 result schema 为主，但更明确地向 **QCSchema 风格** 靠拢。

本轮要求：

- JSON 继续作为默认结构化交换格式
- HDF5 继续作为大对象/高保真导出格式
- provenance、runtime evidence、validation boundary 在两种导出里都保留
- workbench 和 report 直接消费这一层，不再发明第二套前端专用 schema

## Product Strategy

采用 **双层型产品形态**：

### Layer 1: Visual Workbench

一个本地 Web 工作台，面向：

- run / artifact 浏览
- study / benchmark / scan 对比
- runtime / calibration / hardware campaign 复盘
- 后续 run compose / launch

### Layer 2: Export-Grade Report Engine

一个与工作台共用视觉语言的报告系统，面向：

- 单 run 报告
- benchmark 报告
- study 报告
- scan 报告
- hardware campaign 报告

这两层必须共用：

- 同一套 QCchem result schema
- 同一套图表组件
- 同一套状态标签系统
- 同一套 validated / exploratory / unstable 边界表达

## Primary UX Route

本轮产品主线采用：

- **结果中心先打穿**
- 再把运行中心接入同一套界面

原因：

- QCchem 现有最强资产是 artifact、benchmark、study、runtime evidence
- 先把“看结果、讲结果、比较结果”做到惊艳，最容易把它变成完整软件
- 运行中心后接时，只需要复用同一套工作台骨架，不需要重做产品结构

## Information Architecture

产品一级工作面改为 **6 个必须完成的核心页面**，并在此基础上保留 studies / benchmarks / compose 作为支持性工作面。

### 1. 总览页 / Overview

研究主页，不是欢迎页。

展示：

- 一个实验从 molecule 到 result 的摘要卡片
- 最近 studies / benchmarks / scans
- 当前最佳 case
- hardware campaign 状态
- 最近 runtime collect / pending artifact
- validated / exploratory 分布

### 2. 结构 / 轨道页

这是“化学对象本身”的主页面。

必须包含：

- 3D 结构视图
- MO 能级图
- cube / orbital surface 入口

并要求：

- 结构视图和轨道信息不是孤立组件，而是与当前 result / active space / basis context 联动
- 视觉上更像研究插图工作台，而不是教学演示页

### 3. 活性空间 / 压缩页

这是 QCchem 的核心差异化页面之一，必须做成主打页面，不是附录。

必须包含：

- reduction audit
- active-space selection reason
- orbitals changed / frozen / removed
- constant energy correction
- compression method / rank / threshold
- pre/post term count
- reconstruction error

目标是让用户一眼看懂：

- active space 为什么这么选
- 压缩前后到底发生了什么
- 代价和误差是如何被引入和记录的

### 4. 映射 / 资源 / 电路页

这个页面直接回答：

- 需要多少 qubit
- 需要多少门
- 为什么是这个代价

必须包含：

- fermion-to-qubit mapping 摘要
- resource estimate
- qubit count
- transpiled depth / 2Q gate count
- circuit / execution cost explanation

### 5. 运行监控页

这是把 simulator 和 hardware 差别显出来的关键页。

必须包含：

- local ideal vs sampled vs runtime
- job evidence / job metadata
- layout / backend / provider usage
- calibration / measured vs estimated cost
- runtime queue / collect / retrieval state

### 6. 结果 / 可信度 / 报告页

单个 run / artifact 的深度分析页面。

固定结构：

- 顶部摘要：体系、方法、总能量、可信度状态、最佳对比
- 主图区：能量、误差、runtime / local 对比、scan 或 benchmark 主图
- 细节分区：
  - energy
  - exact baseline
  - reduction audit
  - compression
  - calibration
  - runtime
  - properties
  - excited-state
- 右侧解释栏：provenance、boundary、export

这一页的目标是让每次计算都能留下可复现证据，而不是只显示一个结果数值。

### 支持性工作面：Studies

研究活动页，负责组织多个 runs。

支持比较：

- solver
- backend
- mapping
- shots
- active space
- compression
- runtime strategy

### 支持性工作面：Benchmarks

可信度仪表板页。

重点表达：

- validated / exploratory / unstable
- exact / ideal / sampled / runtime
- chemical accuracy distance
- estimated vs measured cost
- hardware evidence tier

### 支持性工作面：Compose / Run

后接的运行中心，定位为“实验配方编辑器”，不是传统表单页。

结构：

- 左侧：molecule / problem / solver / backend / task / policy 结构化配置
- 中部：配置摘要与 preview
- 右侧：expected capability、risk/boundary、artifact preview

## Layout System

主工作台采用：

- **Analysis Desk** 作为默认骨架
- 吸收部分 **Gallery Home** 的展示气质

即：

- 左侧 `Research Navigator`
  - study / benchmark / scan / run registry
  - 收藏 case
  - 最近 artifact
- 中央 `Analysis Desk`
  - 当前主图
  - 当前主要结论
  - 结果细节面板
- 右侧 `Interpretation Rail`
  - provenance
  - validation boundary
  - runtime metadata
  - export actions
- 顶部 `Context Bar`
  - workspace
  - search
  - new run / benchmark / scan
  - runtime collect
  - report export

## Visual System

### Background and Material

- 不使用刺眼纯白
- 使用温润浅底：
  - 羊皮纸白
  - 淡矿物灰
  - 柔和暖灰
- 主内容卡片更干净，形成层次

### Color Language

- 结构色：深石墨蓝 / 深海蓝
- 强调色：铜棕 / 琥珀
- 科学辅助色：青灰 / 冰蓝
- 状态色保持克制，不做整屏交通灯

### Typography

- 标题：有研究出版物气质，略带编辑感
- 正文：高可读，适合长时间阅读
- 数值 / 路径 / 代码：单独等宽体系

### Motion

只做三类轻动效：

- 页面进入的轻微铺陈
- 列表切换与主图替换的柔和过渡
- 当前选中对象的焦点强化

不做抢戏动画。

## Visualization System

本轮必须补齐并统一的 7 类图形能力：

### 1. Molecule Identity Cards

- 每个 run / study / benchmark case 都有高质量分子预览
- 用于列表、摘要卡、报告封面
- 风格偏研究插图，而非粗糙教学示意
- 底层渲染优先使用 3Dmol.js 的结构快照与可导出视图能力

### 2. Energy & Error Hero Charts

- total / exact / solver / correction 关系图
- chemical accuracy distance
- runtime vs local 对比

### 3. Benchmark Dashboards

- validated / exploratory / unstable 分布
- exact / ideal / sampled / runtime 对照
- estimated vs measured cost
- precision target vs achieved error

### 4. Scan / PES Figures

- 曲线本身
- 几何参数
- baseline / error
- excited-state / property 占位入口

### 5. Runtime / Hardware Figures

- job evidence
- layout
- 2Q gate count
- usage seconds
- error trend

### 6. Reduction / Compression / Correction Figures

- active-space 前后规模变化
- Hamiltonian compression 前后对比
- perturbative correction 分量关系
- orbitals changed / frozen / removed 的图形化表达
- active-space selection rationale 的可解释化表达

### 7. Report Covers & Export Visuals

每个导出报告首页至少包含：

- 体系名称与分子图
- 方法摘要
- 关键结果
- 状态标签
- 一张主图

## Reporting Strategy

报告系统不再只是“把 JSON 渲染成 Markdown”，而是升级成统一的视觉表达层。

本轮要求：

- 工作台与报告共用视觉组件
- 报告页面仍忠实表达 schema
- 重要图表在 workbench 与 report 中复用同一视觉语法
- 保持可读、可截图、可汇报

首轮重点增强：

- run report
- study report
- benchmark report
- scan report
- hardware campaign report
- 结构 / 轨道导出视图
- 活性空间 / 压缩导出视图

## Integration with Existing QCchem

本轮不重写已有 workflow，只做上层集成：

- 继续复用 `result.json` / `report.md` / aggregate JSON
- 继续复用 `qcschema.json` / `result.h5`
- 继续复用 benchmark / study / scan / runtime collect
- 新工作台作为这些 artifact 的可视化消费层
- Compose / Run 只作为现有 CLI/workflow 的前端编排层

换句话说：

- QCchem 的“事实来源”仍是 schema + artifact
- 新界面是它们的高质量观察层与操作层

## Boundary Rules

本轮必须继续保留：

- validated / exploratory / unstable 明确边界
- hardware_verified 的窄语义
- chemical_accuracy 与 runtime_chemical_accuracy 的明确拆分

视觉层不能：

- 粉饰未达标结果
- 把 exploratory 模块伪装成 validated
- 把 schema 里没有的推断包装成事实

## Required Page Inventory

这轮必须正式交付并可演示的页面最少包括：

1. 总览页
   - 一个实验从 molecule 到 result 的摘要卡片
2. 结构 / 轨道页
   - 3D 结构 + MO 能级 + cube 表面
3. 活性空间 / 压缩页
   - QCchem 差异化核心页面
4. 映射 / 资源 / 电路页
   - 回答 qubit / gate / cost / why
5. 运行监控页
   - 清楚区分 simulator 与 hardware
6. 结果 / 可信度 / 报告页
   - 强化可复现证据与导出体验

## Deliverables

本轮设计对应的正式交付物应包括：

1. Visual workbench shell
2. Overview page
3. Structure / orbitals page
4. Active-space / compression page
5. Mapping / resources / circuits page
6. Runtime monitoring page
7. Result / confidence / reporting page
8. Study / Benchmark / Scan / Hardware campaign visual pages
9. Report visual overhaul
10. Shared visualization component system
11. Molecule preview system
12. Export-grade report cover system
13. Dash-based multipage shell
14. QCSchema-aligned JSON/HDF5-aware visualization consumption layer

## Success Criteria

- QCchem 看起来不再只是“很多 artifact 的集合”，而是完整软件
- 研究人员第一次打开时，能立即进入上下文
- 长时间阅读和比较结果不会审美疲惫
- benchmark / runtime / hardware evidence 的严肃信息仍然清楚可信
- workbench 与 report 看起来像同一产品，而不是两套风格
- 结构 / 轨道 / 活性空间 / 压缩 / 资源 / 运行监控 / 报告这几类科研信息都被提升到页面级，而不是附属字段
- 前端实现路线清楚：Dash 主壳、3Dmol.js 主结构层、QCSchema 风格数据对齐、JSON/HDF5 双保真导出
- 后续接入 Compose / Run 与 MCP 时不需要推翻本轮设计
