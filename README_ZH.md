# ⚡ N8N 工作流集合与文档

一个专业整理的 **2,053 个 n8n 工作流** 集合，配备极速文档系统，支持即时搜索、分析与浏览。

## 🚀 **全新：高性能文档系统**

**体验比传统文档快 100 倍的性能提升！**

### 快速开始 - 极速文档系统
```bash
# 安装依赖
pip install -r requirements.txt

# 启动 FastAPI 服务器
python run.py

# 浏览器访问
http://localhost:8000
```

**功能亮点：**
- ⚡ **亚 100 毫秒响应**，基于 SQLite FTS5 搜索
- 🔍 **即时全文检索**，支持高级过滤
- 📱 **响应式设计**，移动端完美适配
- 🌙 **深色/浅色主题**，自动适应系统
- 📊 **实时统计**，365 种独特集成，29,445 个节点
- 🎯 **按触发类型与复杂度智能分类**
- 🎯 **按服务名称映射用例分类**
- 📄 **按需查看/下载 JSON**
- 🔗 **Mermaid 流程图自动生成**，可视化工作流
- 🔄 **智能命名**，实时格式化

### 性能对比

| 指标 | 旧系统 | 新系统 | 提升 |
|------|--------|--------|------|
| **文件大小** | 71MB HTML | <100KB | **缩小 700 倍** |
| **加载时间** | 10+ 秒 | <1 秒 | **快 10 倍** |
| **搜索** | 仅客户端 | FTS5 全文 | **瞬时** |
| **内存占用** | ~2GB RAM | <50MB RAM | **降低 40 倍** |
| **移动端支持** | 差 | 优秀 | **完全响应式** |

---

## 📂 仓库结构

### 工作流集合
- **2,053 个工作流**，命名规范，便于检索
- **365 种独特集成**，覆盖主流平台
- **29,445 个节点**，专业分类
- **质量保障**，所有工作流均已分析与分类

### 智能命名系统 ✨
自动将技术文件名转为可读标题：
- **前**：`2051_Telegram_Webhook_Automation_Webhook.json`
- **后**：`Telegram Webhook Automation`
- **100% 语义化命名**，智能大写
- **自动集成识别**，基于节点分析

### 用例分类 ✨

搜索界面支持下拉筛选，按类别浏览 2,000+ 工作流。

系统自动按服务类别对工作流进行分类，便于发现和筛选。

### 分类原理
1. **运行分类脚本**
   ```
   python create_categories.py
   ```
2. **服务名识别**
   脚本分析每个工作流 JSON 文件名，识别服务名（如 Twilio、Slack、Gmail 等）
3. **类别映射**
   每个服务名通过 `context/def_categories.json` 映射到对应类别。例如：
   - Twilio → 通信与消息
   - Gmail → 通信与消息
   - Airtable → 数据处理与分析
   - Salesforce → CRM 与销售
4. **生成分类数据**
   脚本输出 `search_categories.json`，包含所有分类信息
5. **前端筛选**
   用户可在界面按类别筛选，快速定位用例

### 可用主类别
- AI智能体开发
- 业务流程自动化
- 云存储与文件管理
- 通信与消息
- 创意内容与视频自动化
- 创意设计自动化
- CRM与销售
- 数据处理与分析
- 电商与零售
- 财务与会计
- 市场营销与广告自动化
- 项目管理
- 社交媒体管理
- 技术基础设施与DevOps
- 网页抓取与数据提取

### 扩展分类
可在 context/defs_categories.json 中添加更多服务与类别映射。

---

## 🛠 使用说明

### 方式一：现代极速系统（推荐）
```bash
# 克隆仓库
git clone <repo-url>
cd n8n-workflows

# 安装依赖
pip install -r requirements.txt

# 启动文档服务器
python run.py

# 浏览 http://localhost:8000
# - 极速检索 2,053 个工作流
# - 专业响应式界面
# - 实时统计
```

### 方式二：开发模式
```bash
# 开发模式自动重载
python run.py --dev

# 自定义主机/端口
python run.py --host 0.0.0.0 --port 3000

# 强制重建索引
python run.py --reindex
```

### 导入工作流到 n8n
```bash
# 推荐使用 Python 脚本批量导入
python import_workflows.py

# 或手动导入单个工作流：
# 1. 打开 n8n 编辑器 UI
# 2. 菜单 (☰) → 导入工作流
# 3. 选择 workflows/ 文件夹下的 .json 文件
# 4. 运行前请更新凭证和 webhook 地址
```

---

## 📊 工作流统计

### 当前数据
- **总工作流数**：2,053
- **活跃工作流**：215（活跃率 10.5%）
- **节点总数**：29,445（平均每个 14.3 个节点）
- **独特集成**：365 种服务与API
- **数据库**：SQLite + FTS5 全文检索

### 触发类型分布
- **复杂**：831（40.5%）- 多触发系统
- **Webhook**：519（25.3%）- API 触发
- **手动**：477（23.2%）- 用户主动触发
- **定时**：226（11.0%）- 定时执行

### 复杂度分析
- **低（≤5节点）**：约35% - 简单自动化
- **中（6-15节点）**：约45% - 标准工作流
- **高（16+节点）**：约20% - 企业级复杂系统

### 热门集成
- **通信**：Telegram、Discord、Slack、WhatsApp
- **云存储**：Google Drive、Google Sheets、Dropbox
- **数据库**：PostgreSQL、MySQL、MongoDB、Airtable
- **AI/ML**：OpenAI、Anthropic、Hugging Face
- **开发**：HTTP 请求、Webhook、GraphQL

---

## 🔍 高级搜索功能

### 智能服务分类
系统自动将工作流归入 12 个服务类别：
- **messaging**：Telegram、Discord、Slack、WhatsApp、Teams
- **ai_ml**：OpenAI、Anthropic、Hugging Face
- **database**：PostgreSQL、MySQL、MongoDB、Redis、Airtable
- **email**：Gmail、Mailjet、Outlook、SMTP/IMAP
- **cloud_storage**：Google Drive、Google Docs、Dropbox、OneDrive
- **project_management**：Jira、GitHub、GitLab、Trello、Asana
- **social_media**：LinkedIn、Twitter/X、Facebook、Instagram
- **ecommerce**：Shopify、Stripe、PayPal
- **analytics**：Google Analytics、Mixpanel
- **calendar_tasks**：Google Calendar、Cal.com、Calendly
- **forms**：Typeform、Google Forms、Form Triggers
- **development**：Webhook、HTTP 请求、GraphQL、SSE

### API 使用示例
```bash
# 按文本搜索工作流
curl "http://localhost:8000/api/workflows?q=telegram+automation"

# 按触发类型和复杂度筛选
curl "http://localhost:8000/api/workflows?trigger=Webhook&complexity=high"

# 查找所有消息类工作流
curl "http://localhost:8000/api/workflows/category/messaging"

# 获取数据库统计
curl "http://localhost:8000/api/stats"

# 浏览所有分类
curl "http://localhost:8000/api/categories"
```

---

## 🏗 技术架构

### 现代技术栈
- **SQLite 数据库** - FTS5 全文检索，365 种集成
- **FastAPI 后端** - RESTful API，自动 OpenAPI 文档
- **响应式前端** - 现代 HTML5 + CSS/JS
- **智能分析** - 自动分类与命名

### 关键特性
- **变更检测** - MD5 哈希高效重索引
- **后台处理** - 非阻塞分析
- **压缩响应** - Gzip 中间件极速传输
- **错误处理** - 完善日志与降级
- **移动优化** - 触屏友好

### 数据库性能
```sql
-- 优化表结构，极速查询
CREATE TABLE workflows (
    id INTEGER PRIMARY KEY,
    filename TEXT UNIQUE,
    name TEXT,
    active BOOLEAN,
    trigger_type TEXT,
    complexity TEXT,
    node_count INTEGER,
    integrations TEXT,  -- 365 种服务的 JSON 数组
    description TEXT,
    file_hash TEXT,     -- MD5 变更检测
    analyzed_at TIMESTAMP
);

-- 全文检索与排序
CREATE VIRTUAL TABLE workflows_fts USING fts5(
    filename, name, description, integrations, tags,
    content='workflows', content_rowid='id'
);
```

---

## 🔧 安装与环境要求

### 系统要求
- **Python 3.7+** - 运行文档系统
- **现代浏览器** - Chrome、Firefox、Safari、Edge
- **50MB 存储空间** - SQLite 数据库及索引
- **n8n 实例** - 用于导入和运行工作流

### 安装步骤
```bash
# 克隆仓库
git clone <repo-url>
cd n8n-workflows

# 安装依赖
pip install -r requirements.txt

# 启动文档服务器
python run.py

# 访问 http://localhost:8000
```

### 开发环境
```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 开发模式自动重载
python api_server.py --reload

# 强制重建索引
python workflow_db.py --index --force
```

---

## 📋 命名规范

### 智能格式化系统
自动将技术文件名转为友好名称：
```bash
# 自动转换示例：
2051_Telegram_Webhook_Automation_Webhook.json → "Telegram Webhook Automation"
0250_HTTP_Discord_Import_Scheduled.json → "HTTP Discord Import Scheduled"
0966_OpenAI_Data_Processing_Manual.json → "OpenAI Data Processing Manual"
```

### 技术命名格式
```
[ID]_[服务1]_[服务2]_[用途]_[触发].json
```

### 智能大写规则
- **HTTP** → HTTP（不是 Http）
- **API** → API（不是 Api）
- **webhook** → Webhook
- **automation** → Automation
- **scheduled** → Scheduled

---

## 🚀 API 文档

### 核心接口
- `GET /` - 主工作流浏览界面
- `GET /api/stats` - 数据库统计与指标
- `GET /api/workflows` - 支持筛选与分页的搜索
- `GET /api/workflows/{filename}` - 工作流详情
- `GET /api/workflows/{filename}/download` - 下载 JSON
- `GET /api/workflows/{filename}/diagram` - 生成 Mermaid 流程图

### 高级搜索
- `GET /api/workflows/category/{category}` - 按服务类别搜索
- `GET /api/categories` - 所有可用类别
- `GET /api/integrations` - 集成统计
- `POST /api/reindex` - 触发后台重建索引

### 响应示例
```json
// GET /api/stats
{
  "total": 2053,
  "active": 215,
  "inactive": 1838,
  "triggers": {
    "Complex": 831,
    "Webhook": 519,
    "Manual": 477,
    "Scheduled": 226
  },
  "total_nodes": 29445,
  "unique_integrations": 365
}
```

---

## 🤝 贡献指南

### 新增工作流
1. **从 n8n 导出** JSON 文件
2. **规范命名**，遵循命名模式
3. **添加到 workflows/ 目录**
4. **移除敏感信息**（凭证、私有 URL）
5. **重建索引**，更新数据库

### 质量标准
- ✅ 工作流可用且已测试
- ✅ 移除所有凭证和敏感信息
- ✅ 命名规范统一
- ✅ 兼容最新 n8n 版本
- ✅ 包含有意义的描述或注释

---

## ⚠️ 注意事项

### 安全与隐私
- **使用前请检查** - 所有工作流仅供学习参考
- **更新凭证** - 替换 API 密钥、Token、Webhook
- **安全测试** - 请先在开发环境验证
- **权限检查** - 确保集成服务有正确权限

### 兼容性
- **n8n 版本** - 兼容 n8n 1.0+（大部分工作流）
- **社区节点** - 部分工作流需额外安装节点
- **API 变更** - 外部服务 API 可能已更新
- **依赖检查** - 导入前请确认所需集成已安装

---

## 📚 资源与参考

### 工作流来源
本合集包含以下来源的工作流：
- **官方 n8n.io** - 官方文档与社区示例
- **GitHub 仓库** - 开源社区贡献
- **博客与教程** - 实战自动化案例
- **用户投稿** - 已测试与验证的工作流
- **企业用例** - 业务流程自动化

### 深入了解
- [n8n 官方文档](https://docs.n8n.io/)
- [n8n 社区](https://community.n8n.io/)
- [工作流模板](https://n8n.io/workflows/)
- [集成文档](https://docs.n8n.io/integrations/)

---

## 🏆 项目成就

### 仓库升级
- **2,053 个工作流**，专业整理与命名
- **365 种独特集成**，自动检测与分类
- **100% 语义化命名**（不再是简单文件名）
- **智能重命名零数据丢失**
- **12 类服务高级检索**

### 性能革命
- **亚 100 毫秒检索**，SQLite FTS5 全文索引
- **29,445 节点极速筛选**
- **移动端优化**，全设备响应式
- **实时统计**，数据库动态查询
- **专业界面**，现代化用户体验

### 系统可靠性
- **健壮错误处理**，降级保护
- **变更检测**，高效数据库更新
- **后台处理**，非阻塞操作
- **全面日志**，便于调试与监控
- **生产级部署**，中间件与安全保障

---

*本仓库是目前最全面、最专业的 n8n 工作流集合，拥有先进的检索技术与专业文档，让工作流发现与使用变得高效愉快。*

**🎯 适合人群**：开发者、自动化工程师、业务分析师及任何希望用 n8n 自动化提升效率的人士。
