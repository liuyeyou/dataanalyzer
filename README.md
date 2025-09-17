# Data Analyzer with LLM Agents

这是一个基于 Streamlit 和 LangChain 的智能数据分析应用，它可以：
- 自动分析 CSV 数据
- 生成数据摘要
- 回答关于数据的问题
- 分析数据趋势
- 支持多种文件编码（UTF-8、GBK、GB2312等）

## 功能特点

- 智能文件编码检测
- 自动识别日期列
- 数据可视化
- 自然语言交互
- 趋势分析

## 技术栈

- **前端框架**: Streamlit
- **数据处理**: Pandas, NumPy
- **数据可视化**: Matplotlib, Plotly
- **AI/LLM**: LangChain
- **其他工具**: Python 3.8+

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/liuyeyou/dataanalyzer.git
cd dataanalyzer
```

2. 创建虚拟环境：
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 启动应用：
```bash
streamlit run app.py
```

2. 在浏览器中打开显示的URL（默认为 http://localhost:8501）

3. 上传CSV文件并开始分析

## 支持的文件格式

- CSV 文件
- 支持多种编码（UTF-8、GBK、GB2312、BIG5、UTF-16）
- 自动识别日期列

## 数据要求

- CSV 文件必须包含日期列（支持多种日期列名，如：日期、date、time、datetime等）
- 日期格式应该是标准格式（如：YYYY-MM-DD、YYYY/MM/DD等）
- 数值列应该是数字格式

## 功能示例

1. **数据摘要**
   - 自动生成数据统计信息
   - 识别关键指标和趋势
   - 生成数据质量报告

2. **智能问答**
   - 使用自然语言提问
   - 获取数据见解
   - 生成数据分析建议

3. **趋势分析**
   - 时间序列分析
   - 季节性分析
   - 异常检测

## 注意事项

- 建议使用虚拟环境运行应用
- 首次运行可能需要下载语言模型
- 处理大文件时需要足够的内存
- 确保网络连接（用于下载模型）
- `src/instruction/` 目录为本地说明文件，已加入 `.gitignore`，默认不提交仓库

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情


