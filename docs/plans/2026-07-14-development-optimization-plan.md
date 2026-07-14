# English Work Abroad Coach 开发优化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不破坏现有 30/60 分钟学习、签到、统计和提醒行为的前提下，将项目逐步优化为可跨设备安装、数据可靠、三平台一致、可持续发布的 Agent Skill。

**Architecture:** 保留 `claudecode-codex-opencode/`、`openclaw/`、`hermes/` 三个可独立安装的分发目录，将 Claude Code/Codex/opencode 版本作为共享脚本和参考资料的唯一源码，通过同步工具生成另外两个平台的共享文件。运行数据从 skill 安装目录迁移到操作系统用户状态目录，并使用 Python 标准库 SQLite 提供原子写入、并发保护和迁移能力。

**Tech Stack:** Python 3.9+、Python 标准库（`argparse`、`json`、`sqlite3`、`unittest`）、uv、Agent Skills Markdown/YAML、systemd user timer、GitHub Actions。

---

## 目录

1. 文档状态
2. 当前基线
3. 范围
4. 方案比较与选择
5. 关键架构决策
6. 目标目录
7. 分阶段实施
8. 里程碑与发布顺序
9. 测试策略
10. 风险与回滚
11. 完成定义
12. 执行纪律

## 1. 文档状态

| 项目 | 内容 |
| --- | --- |
| 状态 | Proposed，等待维护者评审后执行 |
| 创建日期 | 2026-07-14 |
| 基线提交 | `bc0b74e Document agent-based skill installation` |
| 当前版本 | OpenClaw/Hermes 元数据版本 `0.1.0` |
| 优化策略 | 先工程稳定，再增强学习智能 |
| 主要使用场景 | 同一用户多设备、多 Agent 平台使用，同时保留公开分发能力 |

## 2. 当前基线

执行计划前必须保留以下已验证行为：

- 工作日默认 30 分钟，周末默认 60 分钟。
- `today`、`checkin`、`summary`、`reminder`、`plan` 命令继续可用。
- 50 天周期和 500 天目标继续保留。
- Claude Code/Codex/opencode、OpenClaw、Hermes 三个目录都能独立安装。
- Linux systemd 提醒与 Agent 会话外调度继续分离。
- 当前测试基线为核心 8 项、OpenClaw 4 项、Hermes 5 项全部通过。

基线验证命令：

```bash
cd /home/jhadmin/codes/mystu/english-work-abroad-coach
PYTHONDONTWRITEBYTECODE=1 claudecode-codex-opencode/.venv/bin/python -m unittest discover -s claudecode-codex-opencode/tests -v
PYTHONDONTWRITEBYTECODE=1 openclaw/.venv/bin/python -m unittest discover -s openclaw/tests -v
PYTHONDONTWRITEBYTECODE=1 hermes/.venv/bin/python -m unittest discover -s hermes/tests -v
```

预期：分别显示 `Ran 8 tests`、`Ran 4 tests`、`Ran 5 tests`，全部为 `OK`。

## 3. 范围

### 3.1 本计划包含

- 三个平台共享文件的单一来源和漂移检查。
- Python 版本约束、uv 优先安装和无全局依赖运行。
- 用户状态目录、SQLite 存储、旧 JSON/JSONL 数据迁移。
- 日期、时长、损坏数据和 systemd 路径边界修复。
- 诊断、导入、导出和备份能力。
- CI、元数据版本、发布包和文档一致性。
- 自适应复习功能的独立设计入口。

### 3.2 本计划不包含

- 云端账号、自动云同步或中心化服务。
- 移动端应用、Web 管理后台或桌面 GUI。
- 语音识别、音频上传或第三方付费 API。
- 自动抓取受版权保护的课程内容。
- 在当前计划内实现完整自适应学习引擎；该能力必须先单独评审设计。

## 4. 方案比较与选择

| 方案 | 内容 | 优点 | 代价与风险 | 结论 |
| --- | --- | --- | --- | --- |
| A. 最小修补 | 只修安装命令和已知边界 Bug | 变更少、短期快 | 三份代码继续漂移，数据仍写在安装目录，下一轮修改继续重复 | 不采用 |
| B. 分阶段稳定化 | 先建立共享来源，再改安装、状态、正确性和发布 | 每个里程碑可独立验收，兼顾现有结构与长期维护 | 比最小修补多一次状态迁移 | 采用 |
| C. 完整 Python 包重构 | 改成标准 wheel/package，再由插件层引用 | Python 工程结构最统一 | 破坏自包含 skill 形状，安装依赖更重，当前规模不值得 | 暂不采用 |

状态存储同时比较三种选择：继续整文件重写 JSONL、改用 SQLite、接入云同步。选择 SQLite 是因为它属于 Python 标准库，能解决原子写入和并发覆盖，又不引入账号、服务端或第三方运行依赖。保留 JSON 导入导出作为人工跨设备迁移格式。

## 5. 关键架构决策

### 5.1 三平台分发

采用“一个共享来源，三个自包含分发”的方案：

```text
claudecode-codex-opencode/      共享脚本和 references 的唯一来源
            |
            | tools/sync_distributions.py
            +--------------------> openclaw/
            +--------------------> hermes/

平台专属文件不参与覆盖：
- SKILL.md
- agents/openai.yaml
- 平台测试
- 平台元数据
```

不把三个平台改成运行时共享同一个父目录，因为安装后的 skill 必须保持自包含。同步工具只在开发和发布阶段运行。

### 5.2 代码与数据分离

skill 目录只保存只读资源：

```text
data/default-plan.json
scripts/
references/
SKILL.md
```

用户运行数据保存到以下优先级最高的目录：

1. 命令行 `--state-dir`。
2. 环境变量 `ENGLISH_COACH_HOME`。
3. Windows：`%LOCALAPPDATA%/EnglishWorkAbroadCoach`。
4. macOS：`~/Library/Application Support/EnglishWorkAbroadCoach`。
5. Linux：`$XDG_STATE_HOME/english-work-abroad-coach`，未设置时使用 `~/.local/state/english-work-abroad-coach`。

状态目录结构：

```text
<state-dir>/
  coach.db
  reminder.log
  backups/
```

SQLite 初始表：

```sql
CREATE TABLE schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE checkins (
    checkin_date TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);
```

`progress.json` 不再作为事实来源；进度在查询时从签到记录计算。导入旧数据时只读取 `progress.json` 进行一致性提示，不把它写入数据库。

### 5.3 兼容策略

- 现有 `--root` 继续表示 skill 资源目录。
- 新增 `--state-dir`，不改变现有命令名称。
- 首次运行发现旧 `data/checkins.jsonl` 或个性化 `data/plan.json` 时，只复制到新状态库，不自动删除旧文件。
- 迁移完成后在数据库写入 `legacy_migration_completed`，避免重复导入。
- 30/60 分钟继续作为 v0.x 唯一合法模式。
- Python 最低版本统一为 3.9；推荐版本为 3.12。

## 6. 目标目录

```text
english-work-abroad-coach/
  .github/workflows/ci.yml
  docs/plans/2026-07-14-development-optimization-plan.md
  tools/
    sync_distributions.py
    verify_project.py
  tests/
    test_distribution_sync.py
  claudecode-codex-opencode/
    SKILL.md
    agents/openai.yaml
    requirements-dev.txt
    data/default-plan.json
    scripts/
      bootstrap.py
      coach_storage.py
      english_coach.py
      install_reminder.py
      reminder_runner.py
    references/
    tests/
  openclaw/
  hermes/
```

## 7. 分阶段实施

每个任务必须独立通过测试后再进入下一个任务。除文档任务外，行为修改一律先写失败测试。

### Task 1：建立项目级验证入口

**目标：** 用一个命令验证核心测试、平台测试和 skill 元数据；Task 2 再把共享文件一致性接入同一入口。

**Files:**
- Create: `tools/verify_project.py`
- Create: `tools/validate_skill.py`
- Create: `tests/test_verify_project.py`
- Modify: `README.md`

- [ ] **Step 1：先写验证工具的单元测试**

测试至少断言验证计划包含三个测试目录和三个 skill 校验目标：

```python
def test_verification_plan_covers_all_distributions():
    plan = verify_project.build_verification_plan(ROOT)
    assert [item["name"] for item in plan["tests"]] == [
        "claudecode-codex-opencode",
        "openclaw",
        "hermes",
    ]
    assert len(plan["skill_validation"]) == 3
```

- [ ] **Step 2：运行测试并确认失败**

```bash
python3.12 -m unittest discover -s tests -p 'test_verify_project.py' -v
```

预期：因为 `tools/verify_project.py` 尚不存在而失败。

- [ ] **Step 3：实现验证计划和命令执行器**

`tools/verify_project.py` 必须提供：

```python
def build_verification_plan(root: Path) -> dict:
    """Return deterministic project checks configured for the current milestone."""

def run_verification(root: Path, python: str, validator: Optional[Path]) -> int:
    """Run every check and return non-zero after the first failed command."""
```

文件顶部从 `typing` 导入 `Optional`，以保持 Python 3.9 兼容。

`tools/validate_skill.py` 使用开发依赖 PyYAML，检查 frontmatter 边界、`name`、`description`、目录命名和平台 metadata 基本形状。外部官方验证器路径允许通过 `--validator` 显式传入；未传入时仍执行本地验证器，并打印 `SKIP: external skill validator not configured`，不能静默假装执行过官方校验。

`tests/test_verify_project.py` 同时覆盖一个合法 frontmatter 和缺少 `description` 的非法 frontmatter，断言本地验证器分别返回 0 和 1。

- [ ] **Step 4：运行项目级验证**

```bash
python3.12 tools/verify_project.py --python claudecode-codex-opencode/.venv/bin/python
```

预期：三个测试套件和本地元数据验证全部通过；未提供外部 validator 时显示 `SKIP: external skill validator not configured`。

- [ ] **Step 5：更新 README 的开发验证章节**

README 只保留项目级入口和常见失败定位，不复制完整测试矩阵；同时在开发章节链接本计划，保证路线图可发现。

- [ ] **Step 6：提交本任务**

```bash
git add tools/verify_project.py tools/validate_skill.py tests/test_verify_project.py README.md
git commit -m "build: add project verification entrypoint"
```

### Task 2：消除三份共享代码漂移

**目标：** 保持三个目录可独立安装，同时只维护一份共享脚本、依赖清单和 references。

**Files:**
- Create: `tools/sync_distributions.py`
- Create: `tests/test_distribution_sync.py`
- Modify: `tools/verify_project.py`
- Modify: `README.md`
- Synchronize: `openclaw/scripts/`, `openclaw/references/`, `hermes/scripts/`, `hermes/references/`

- [ ] **Step 1：写共享文件清单测试**

```python
def test_shared_files_match_canonical_distribution():
    mismatches = sync_distributions.find_mismatches(ROOT)
    assert mismatches == []
```

清单必须包含：

```python
SHARED_PATHS = (
    "requirements.txt",
    "scripts/bootstrap.py",
    "scripts/english_coach.py",
    "scripts/reminder_runner.py",
    "references/learning-science.md",
    "references/material-sources.md",
    "references/plan-system.md",
)
```

Task 3 把 `requirements.txt` 替换为 `requirements-dev.txt` 时同步更新清单；Task 4 创建 `coach_storage.py` 时再把它加入清单和测试。不能预先创建空文件。

- [ ] **Step 2：制造临时差异并确认 `--check` 能失败**

测试使用 `TemporaryDirectory` 复制最小目录，不得修改真实分发文件。

预期：`find_mismatches()` 返回目标平台和相对路径。

- [ ] **Step 3：实现同步工具**

```python
def find_mismatches(root: Path) -> list[str]:
    """Return shared files whose bytes differ from the canonical version."""

def synchronize(root: Path) -> list[Path]:
    """Copy canonical shared files to platform distributions."""
```

命令行为：

```bash
python3.12 tools/sync_distributions.py --check  # 只检查，漂移时退出 1
python3.12 tools/sync_distributions.py --write  # 覆盖清单内共享文件
```

同步工具禁止覆盖 `SKILL.md`、`agents/`、平台 README、平台测试和 `data/default-plan.json` 中的 `distribution` 字段。

同步检查实现后，把 `sync_distributions.py --check` 加入 `verify_project.py` 的默认验证计划；从此项目级验证会阻止共享文件漂移。

- [ ] **Step 4：同步并验证三个分发目录**

```bash
python3.12 tools/sync_distributions.py --write
python3.12 tools/sync_distributions.py --check
python3.12 tools/verify_project.py --python claudecode-codex-opencode/.venv/bin/python
```

预期：`--check` 退出 0，全部现有测试通过。

- [ ] **Step 5：提交本任务**

```bash
git add tools/sync_distributions.py tools/verify_project.py tests/test_distribution_sync.py README.md openclaw hermes
git commit -m "build: synchronize shared skill files"
```

### Task 3：建立可预测的 Python 与安装契约

**目标：** 默认安装不再误用 Python 3.7，运行核心功能不依赖 PyYAML 或网络。

**Files:**
- Modify: `claudecode-codex-opencode/scripts/bootstrap.py`
- Rename: `claudecode-codex-opencode/requirements.txt` to `claudecode-codex-opencode/requirements-dev.txt`
- Delete: `openclaw/requirements.txt`
- Delete: `hermes/requirements.txt`
- Create by synchronization: `openclaw/requirements-dev.txt`
- Create by synchronization: `hermes/requirements-dev.txt`
- Modify: `claudecode-codex-opencode/tests/test_bootstrap.py`
- Create: `claudecode-codex-opencode/tests/test_runtime_smoke.py`
- Modify: `claudecode-codex-opencode/references/installing.md`
- Modify: `README.md`
- Synchronize shared files to `openclaw/` and `hermes/`

- [ ] **Step 1：写 Python 版本失败测试**

```python
def test_require_supported_python_rejects_python_37():
    with self.assertRaisesRegex(RuntimeError, "Python 3.9 or newer"):
        bootstrap.require_supported_python((3, 7, 3))

def test_require_supported_python_accepts_python_312():
    bootstrap.require_supported_python((3, 12, 0))
```

- [ ] **Step 2：写运行依赖分离测试**

断言核心 `english_coach.py` 只导入标准库，并断言 `requirements-dev.txt` 包含 `PyYAML>=6.0.2`。分发目录不再声明核心运行时必须安装 PyYAML。

- [ ] **Step 3：运行测试并确认失败**

```bash
claudecode-codex-opencode/.venv/bin/python -m unittest discover \
  -s claudecode-codex-opencode/tests -p 'test_bootstrap.py' -v
```

预期：版本检查函数和 `requirements-dev.txt` 尚不存在。

- [ ] **Step 4：实现版本保护**

```python
MIN_PYTHON = (3, 9)

def require_supported_python(version_info=None):
    version = tuple(version_info or sys.version_info[:3])
    if version < MIN_PYTHON:
        raise RuntimeError(
            "Python 3.9 or newer is required; use uv python install 3.12 "
            "and rerun bootstrap with that interpreter."
        )
```

在创建 `.venv` 之前执行检查。错误消息必须包含当前解释器路径、当前版本和 uv 修复命令。

- [ ] **Step 5：调整 bootstrap 行为**

- 正常运行只创建 `.venv`，执行共享的 `test_runtime_smoke.py` 和 `today --json` quick check。
- `--dev` 才安装 `requirements-dev.txt` 并执行 YAML 元数据校验测试。
- 不再无条件升级 pip；只有确实需要安装开发依赖时才调用 pip。
- 保留 `uv venv --clear --seed` 作为标准 `venv` 失败后的回退。
- 把同步工具中的 `requirements.txt` 清单项替换为 `requirements-dev.txt`，并删除三个分发目录中的旧文件。
- 新建只依赖标准库的 `tests/test_runtime_smoke.py` 并加入共享文件清单；平台 metadata 测试只在 `--dev` 或 CI 中运行。

- [ ] **Step 6：写清楚两条安装路径**

已有 Python 3.9+：

```bash
python3 scripts/bootstrap.py
```

只有 uv：

```bash
uv python install 3.12
uv run --python 3.12 python scripts/bootstrap.py --python "$(uv python find 3.12)"
```

Windows PowerShell 等价命令：

```powershell
uv python install 3.12
$python = uv python find 3.12
uv run --python 3.12 python scripts/bootstrap.py --python $python
.venv\Scripts\python.exe scripts\english_coach.py today --json
```

Python 和 uv 都不存在时，安装文档给出 uv 官方安装入口，并要求安装后先验证：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version
```

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv --version
```

项目开发者使用 `python3 scripts/bootstrap.py --dev` 创建包含 PyYAML 的验证环境；普通使用者不需要开发依赖。

- [ ] **Step 7：同步并验证**

```bash
python3.12 tools/sync_distributions.py --write
python3.12 tools/verify_project.py --python claudecode-codex-opencode/.venv/bin/python
```

- [ ] **Step 8：提交本任务**

```bash
git add README.md tools/sync_distributions.py claudecode-codex-opencode openclaw hermes
git commit -m "fix: enforce portable Python bootstrap"
```

### Task 4：引入外部状态目录和 SQLite 存储

**目标：** 让三个平台共享同一份用户进度，避免更新 skill 时覆盖数据，并保证写入原子性。

**Files:**
- Create: `claudecode-codex-opencode/scripts/coach_storage.py`
- Modify: `claudecode-codex-opencode/scripts/english_coach.py`
- Modify: `claudecode-codex-opencode/scripts/reminder_runner.py`
- Modify: `claudecode-codex-opencode/tests/test_english_coach.py`
- Create: `claudecode-codex-opencode/tests/test_coach_storage.py`
- Modify: `tools/sync_distributions.py`
- Create from current template: `claudecode-codex-opencode/data/default-plan.json`
- Create from current template: `openclaw/data/default-plan.json`
- Create from current template: `hermes/data/default-plan.json`
- Modify: `.gitignore`
- Synchronize shared files to `openclaw/` and `hermes/`

- [ ] **Step 1：写状态目录优先级测试**

```python
def test_explicit_state_dir_wins_over_environment(self):
    resolved = coach_storage.resolve_state_dir(
        explicit="/tmp/explicit",
        environ={"ENGLISH_COACH_HOME": "/tmp/environment"},
        platform="linux",
        home=Path("/home/tester"),
    )
    self.assertEqual(resolved, Path("/tmp/explicit"))
```

补充 Linux、macOS、Windows 默认目录测试，所有测试必须注入环境和 home，不能依赖执行测试的真实用户目录。

- [ ] **Step 2：写 SQLite 替换与并发测试**

```python
def test_upsert_replaces_one_date_without_duplicate_rows(self):
    store.upsert_checkin({"date": "2026-07-14", "minutes": 30})
    store.upsert_checkin({"date": "2026-07-14", "minutes": 60})
    self.assertEqual(store.list_checkins(), [{"date": "2026-07-14", "minutes": 60}])
```

再使用两个独立 SQLite 连接连续写入不同日期，断言两条记录都存在。连接必须设置合理的 `timeout`，事务使用 `with connection:`。

- [ ] **Step 3：运行存储测试并确认失败**

```bash
claudecode-codex-opencode/.venv/bin/python -m unittest discover \
  -s claudecode-codex-opencode/tests -p 'test_coach_storage.py' -v
```

预期：`coach_storage.py` 尚不存在。

- [ ] **Step 4：实现状态目录解析和数据库初始化**

`coach_storage.py` 对外接口固定为以下签名：

- `resolve_state_dir(explicit=None, environ=None, platform=None, home=None) -> Path`
- `CoachStore.__init__(state_dir: Path)`
- `CoachStore.initialize() -> None`
- `CoachStore.load_plan(default_plan: dict) -> dict`
- `CoachStore.save_plan(plan: dict) -> None`
- `CoachStore.list_checkins() -> list[dict]`
- `CoachStore.upsert_checkin(entry: dict) -> None`
- `CoachStore.get_meta(key: str) -> Optional[str]`
- `CoachStore.set_meta(key: str, value: str) -> None`

`resolve_state_dir` 只解析路径，不接触文件系统。文件从 `typing` 导入 `Optional`。SQLite 设置：启用外键、设置 busy timeout，并把 `schema_version=1` 写入 `schema_meta`。

把 `scripts/coach_storage.py` 加入 `SHARED_PATHS`，确保 OpenClaw 和 Hermes 使用同一存储实现。

- [ ] **Step 5：让 CLI 同时接收资源目录和状态目录**

```text
--root      只读 skill 资源目录
--state-dir 可写用户状态目录
```

`english_coach.py` 的 `load_plan`、`load_checkins`、`record_checkin`、`build_summary` 改为通过 `CoachStore` 读写。命令输出 JSON 结构保持兼容。

- [ ] **Step 6：删除运行时 progress 文件依赖**

`summary` 只输出计算结果，不再写 skill 目录内的 `data/progress.json`。需要快照时由 `export` 命令生成。

Task 4 暂时保留旧 `data/plan.json` 和 `data/progress.json`，供 Task 5 的真实迁移回归使用；运行时代码只读取 `default-plan.json` 和外部状态库。

- [ ] **Step 7：验证只读 skill 目录**

测试创建只读资源目录和可写临时状态目录，执行 `checkin` 后断言：

- 资源目录没有新增或修改文件。
- 状态目录创建 `coach.db`。
- `summary` 能读取刚写入的签到。

- [ ] **Step 8：同步并提交**

```bash
python3.12 tools/sync_distributions.py --write
python3.12 tools/verify_project.py --python claudecode-codex-opencode/.venv/bin/python
git add .gitignore claudecode-codex-opencode openclaw hermes tools tests
git commit -m "feat: move coach state to SQLite user storage"
```

### Task 5：迁移旧数据并提供导入导出

**目标：** 现有用户升级后不丢签到、计划和提醒日志，并能在设备之间手动迁移。

**Files:**
- Modify: `claudecode-codex-opencode/scripts/coach_storage.py`
- Modify: `claudecode-codex-opencode/scripts/english_coach.py`
- Modify: `claudecode-codex-opencode/tests/test_coach_storage.py`
- Modify: `claudecode-codex-opencode/references/installing.md`
- Delete after migration tests pass: `claudecode-codex-opencode/data/plan.json`
- Delete after migration tests pass: `claudecode-codex-opencode/data/progress.json`
- Delete after migration tests pass: `openclaw/data/plan.json`
- Delete after migration tests pass: `openclaw/data/progress.json`
- Delete after migration tests pass: `hermes/data/plan.json`
- Delete after migration tests pass: `hermes/data/progress.json`

- [ ] **Step 1：写旧数据迁移测试**

测试夹具包含：

```text
legacy/data/plan.json
legacy/data/progress.json
legacy/data/checkins.jsonl
legacy/data/reminder.log
```

断言首次迁移导入计划和签到、复制提醒日志、保留旧文件；第二次运行迁移不增加重复记录。

- [ ] **Step 2：写损坏 JSONL 处理测试**

一行合法、一行损坏时，迁移必须：

- 导入合法行。
- 把损坏行号写入结构化错误列表。
- 返回非零迁移状态。
- 不删除或重写原文件。

- [ ] **Step 3：实现迁移接口**

```python
def migrate_legacy_data(store: CoachStore, legacy_root: Path) -> dict:
    """Copy legacy state once and report imported, skipped, and invalid records."""
```

迁移结果固定包含 `imported_checkins`、`skipped_checkins`、`invalid_lines`、`plan_imported`、`log_copied`。

- [ ] **Step 4：增加 CLI 命令**

```bash
python scripts/english_coach.py migrate --legacy-root ./legacy-skill-backup
python scripts/english_coach.py export --output english-coach-backup.json
python scripts/english_coach.py import --input english-coach-backup.json --merge
```

导出文件必须包含 `format_version`、`exported_at`、`plan`、`checkins`。`--merge` 以日期为主键覆盖同日记录；不提供 `--merge` 时若数据库非空则拒绝导入。

- [ ] **Step 5：增加首次初始化和计划更新命令**

```bash
python scripts/english_coach.py init --start-date 2026-07-14
python scripts/english_coach.py plan --json
python scripts/english_coach.py plan export --output my-plan.json
python scripts/english_coach.py plan update --input my-plan.json
```

`init` 在未传日期时使用本机当天日期；状态库已有计划时拒绝覆盖，只有显式 `--force` 才允许重置计划，并且重置前自动导出备份。`plan update` 校验 `start_date`、30/60 分钟配置、七个 weekday theme 和材料来源结构后才写入事务。skill 后续修改计划必须调用该命令，不再编辑分发目录中的默认模板。

为保持兼容，原有 `plan --json` 继续等价于显示计划；`plan export` 和 `plan update` 是可选的二级动作。

- [ ] **Step 6：验证真实兼容形状**

使用当前仓库 `data/plan.json` 和一个临时 `checkins.jsonl` 副本执行迁移测试，禁止操作真实个人记录。

- [ ] **Step 7：移除分发目录中的旧运行数据模板**

迁移测试通过后，删除三个分发目录中的 `data/plan.json` 和 `data/progress.json`，保留 `data/default-plan.json`。更新平台文件完整性测试，断言发布包不再携带旧运行状态文件。

- [ ] **Step 8：同步、验证并提交**

```bash
python3.12 tools/sync_distributions.py --write
python3.12 tools/verify_project.py --python claudecode-codex-opencode/.venv/bin/python
git add claudecode-codex-opencode openclaw hermes
git commit -m "feat: migrate and export coach data"
```

### Task 6：修复日期、时长和统计边界

**目标：** 对非法输入给出明确错误，并消除已复现的汇总崩溃和时长不一致。

**Files:**
- Modify: `claudecode-codex-opencode/scripts/english_coach.py`
- Modify: `claudecode-codex-opencode/tests/test_english_coach.py`

- [ ] **Step 1：写计划开始前汇总测试**

```python
def test_summary_before_plan_start_returns_not_started(self):
    summary = english_coach.build_summary(store, date(2026, 7, 13), days=30)
    self.assertEqual(summary["status"], "not_started")
    self.assertEqual(summary["expected_days"], 0)
    self.assertEqual(summary["completion_rate"], 0.0)
```

- [ ] **Step 2：写时长约束测试**

`today --minutes 45` 和 `checkin --minutes 45` 都必须由 argparse 返回退出码 2，错误消息包含 `invalid choice: 45`。库函数收到 45 时抛出 `ValueError("minutes must be 30 or 60")`。

- [ ] **Step 3：写日期约束测试**

- 计划开始前签到：拒绝。
- 默认拒绝未来签到。
- `summary --days 0`：拒绝。
- 第 501 天任务：返回 `goal_status="completed"`，不显示 `501/500`。

- [ ] **Step 4：运行测试并确认至少四项失败**

```bash
claudecode-codex-opencode/.venv/bin/python -m unittest discover \
  -s claudecode-codex-opencode/tests -p 'test_english_coach.py' -v
```

- [ ] **Step 5：实现集中校验函数**

```python
def validate_minutes(value: int) -> int:
    if int(value) not in (30, 60):
        raise ValueError("minutes must be 30 or 60")
    return int(value)

def validate_summary_days(value: int) -> int:
    if int(value) < 1:
        raise ValueError("days must be at least 1")
    return int(value)
```

CLI 和库函数都调用同一校验函数，不能只依赖 argparse。

- [ ] **Step 6：实现未开始和目标完成状态**

汇总返回兼容字段并新增 `status`；任务返回 `goal_status`。现有字段不删除，`goal_500_progress` 最大值保持 `500/500`。

- [ ] **Step 7：同步、验证并提交**

```bash
python3.12 tools/sync_distributions.py --write
python3.12 tools/verify_project.py --python claudecode-codex-opencode/.venv/bin/python
git add claudecode-codex-opencode openclaw hermes
git commit -m "fix: validate coach dates and durations"
```

### Task 7：加固提醒安装与诊断能力

**目标：** 路径包含空格时 systemd 单元仍可运行，用户可以快速定位 Python、状态目录和通知问题。

**Files:**
- Modify: `claudecode-codex-opencode/scripts/install_reminder.py`
- Modify: `claudecode-codex-opencode/scripts/reminder_runner.py`
- Modify: `claudecode-codex-opencode/scripts/english_coach.py`
- Modify: `claudecode-codex-opencode/tests/test_reminder_install.py`
- Modify: `claudecode-codex-opencode/references/installing.md`

- [ ] **Step 1：写带空格路径测试**

```python
def test_systemd_units_quote_paths_with_spaces(self):
    units = install_reminder.build_systemd_units(Path("/tmp/English Coach"), "21:00")
    self.assertIn('WorkingDirectory="/tmp/English Coach"', units["service"])
    self.assertIn('ExecStart="/tmp/English Coach/.venv/bin/python"', units["service"])
```

再覆盖 `%`、反斜杠和双引号，使用专用 `quote_systemd_value()`，不使用 shell 拼接。

- [ ] **Step 2：写 doctor 输出测试**

`doctor --json` 必须报告：

```json
{
  "python_supported": true,
  "skill_root_readable": true,
  "state_dir_writable": true,
  "database_ready": true,
  "notify_send_available": true,
  "systemd_user_available": true
}
```

测试通过依赖注入模拟命令存在性，不调用真实 `systemctl` 或 `notify-send`。

- [ ] **Step 3：实现 systemd 引用和 doctor 命令**

提醒服务必须显式传递 `--state-dir`，日志写入外部状态目录。`doctor` 任一必需检查失败时退出 1；只有可选通知机制缺失时退出 0 并显示 warning。

- [ ] **Step 4：运行 dry-run 集成验证**

```bash
claudecode-codex-opencode/.venv/bin/python claudecode-codex-opencode/scripts/install_reminder.py \
  --root "$(pwd)/claudecode-codex-opencode" \
  --state-dir "/tmp/English Coach State" \
  --time 21:00 \
  --dry-run \
  --systemd-user-dir /tmp/english-coach-systemd
```

预期：生成的两个 unit 文件路径引用正确，不调用 `systemctl`。

- [ ] **Step 5：同步、验证并提交**

```bash
python3.12 tools/sync_distributions.py --write
python3.12 tools/verify_project.py --python claudecode-codex-opencode/.venv/bin/python
git add claudecode-codex-opencode openclaw hermes
git commit -m "fix: harden reminders and diagnostics"
```

### Task 8：收敛 skill 文档和平台元数据

**目标：** `SKILL.md` 只保留触发后必须执行的流程，详细安装和平台差异按需加载。

**Files:**
- Modify: `claudecode-codex-opencode/SKILL.md`
- Modify: `claudecode-codex-opencode/references/installing.md`
- Modify: `claudecode-codex-opencode/agents/openai.yaml`
- Modify: `openclaw/SKILL.md`
- Modify: `hermes/SKILL.md`
- Delete: `openclaw/README.md`
- Delete: `hermes/README.md`
- Modify: `README.md`
- Modify: platform metadata tests

- [ ] **Step 1：增加文档结构断言**

测试必须验证：

- 每个 `SKILL.md` 在 200 行以内。
- 核心 description 覆盖计划、每日任务、签到、进度和提醒触发场景。
- OpenClaw 元数据仍位于 `metadata.openclaw`。
- Hermes 元数据仍位于 `metadata.hermes`，21:00 blueprint 保留。
- `agents/openai.yaml` 的默认提示与当前命令名称一致。

- [ ] **Step 2：精简正文并保持渐进披露**

把跨平台安装细节移到 `references/installing.md`；`SKILL.md` 保留首次运行必须检查 bootstrap/doctor 的一句入口。删除分发目录内的辅助 README，顶层 README 继续承担人类用户的项目介绍。

- [ ] **Step 3：运行三个 skill validator**

```bash
for distribution in claudecode-codex-opencode openclaw hermes; do
  claudecode-codex-opencode/.venv/bin/python tools/validate_skill.py "$distribution"
done

test -n "$SKILL_VALIDATOR"
for distribution in claudecode-codex-opencode openclaw hermes; do
  claudecode-codex-opencode/.venv/bin/python "$SKILL_VALIDATOR" "$distribution"
done
```

预期：本地验证器全部退出 0，外部官方验证器对三个目录均输出 `Skill is valid!`。执行正式发布验证前，把 `SKILL_VALIDATOR` 设置为当前环境实际的 `quick_validate.py`；仓库文档不得写死维护者主目录。

- [ ] **Step 4：验证触发和平台边界**

人工运行三类提示：生成今日任务、提交签到、安装提醒。确认 Agent 只在需要时读取安装或学习科学 reference，OpenClaw/Hermes 不调用 Linux 专属安装器。

- [ ] **Step 5：提交本任务**

```bash
git add README.md claudecode-codex-opencode openclaw hermes
git commit -m "docs: streamline skill instructions"
```

### Task 9：建立 CI 和可重复发布

**目标：** 每次提交自动阻止共享文件漂移、Python 兼容回退和无效 skill 元数据进入主分支。

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `tools/build_release.py`
- Create: `tests/test_release_build.py`
- Modify: platform version metadata
- Modify: `README.md`

- [ ] **Step 1：写发布包测试**

测试必须断言每个发布 ZIP：

- 顶层目录名为 `english-work-abroad-coach`。
- 包含匹配平台的 `SKILL.md`、脚本、references、默认计划。
- 不包含 `.venv`、`__pycache__`、个人数据库、签到、提醒日志或测试缓存。
- 解压后能用 Python 3.9+ 执行 `today --json`。

- [ ] **Step 2：实现确定性发布构建**

```python
def build_release(root: Path, distribution: str, output_dir: Path) -> Path:
    """Build one sanitized, self-contained platform ZIP."""
```

构建前必须执行 `sync_distributions.py --check` 和项目验证；失败时不生成 ZIP。

- [ ] **Step 3：增加 GitHub Actions 矩阵**

CI 至少覆盖：

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    python-version: ["3.9", "3.12"]
```

每个矩阵任务执行核心测试；Ubuntu 额外执行项目内 `tools/validate_skill.py`、共享文件检查和发布包测试。外部官方 validator 作为发布前人工门执行，因为它不属于本仓库依赖。CI 不安装 systemd timer，只运行 unit/dry-run 测试。

- [ ] **Step 4：统一版本**

第一个稳定化发布版本定为 `0.2.0`。OpenClaw、Hermes、发布包文件名和顶层 README 使用相同版本。Claude Code/Codex/opencode 的 `agents/openai.yaml` 若不支持版本字段，则不新增非标准字段。

- [ ] **Step 5：设置公开发布门**

在创建 GitHub Release 前，仓库所有者必须选择并加入明确的许可证文件。未选择许可证时 CI 可以通过，但 `build_release.py --publish-check` 必须退出 1 并报告 `LICENSE file is required for public release`。

- [ ] **Step 6：本地验证并提交**

```bash
python3.12 tools/sync_distributions.py --check
python3.12 tools/verify_project.py --python claudecode-codex-opencode/.venv/bin/python
python3.12 -m unittest discover -s tests -p 'test_release_build.py' -v
python3.12 tools/build_release.py --all --output-dir dist
git add .github tools tests README.md claudecode-codex-opencode openclaw hermes
git commit -m "ci: validate and package all skill distributions"
```

### Task 10：为自适应学习建立独立设计门

**目标：** 工程稳定后，再设计真正影响学习行为的 v0.3 功能，避免把行为变化混入基础设施改造。

**Files:**
- Create after Tasks 1-9 pass: `docs/specs/adaptive-review-design.md`
- Create after design approval: `docs/plans/adaptive-review-implementation-plan.md`

- [ ] **Step 1：收集真实使用样本**

在不提交个人原文的前提下，汇总至少 14 天的结构化指标：完成时长、缺勤日期、表达数量、常见错误标签和用户对任务难度的反馈。

- [ ] **Step 2：比较三种方案**

设计文档必须比较：

1. 仅按日期间隔复习表达。
2. 基于表现的轻量 Leitner 队列。
3. 使用模型动态重写全部学习计划。

默认推荐方案 2，因为它可解释、可离线运行、能复用 SQLite，并且不会让每日计划完全依赖模型输出。

- [ ] **Step 3：锁定 v0.3 最小范围**

v0.3 只包含：表达复习队列、错误标签、到期复习项注入今日任务、签到后更新熟练度。材料自动抓取、语音评分和云同步继续排除。

- [ ] **Step 4：完成设计评审后另写详细实施计划**

独立计划必须继续采用 TDD，定义 `review_items` 数据表、调度算法、CLI/JSON 输出兼容和迁移版本。未经设计批准，不修改当前任务生成逻辑。

## 8. 里程碑与发布顺序

| 里程碑 | 包含任务 | 可交付结果 | 发布判断 |
| --- | --- | --- | --- |
| M1 基线与单一来源 | Task 1-2 | 一键验证、共享文件不漂移 | 内部开发可用 |
| M2 跨设备安装 | Task 3 | Python 3.9+ 契约、uv 路径、运行零三方依赖 | 新设备可重复安装 |
| M3 数据可靠性 | Task 4-5 | 外部 SQLite、旧数据迁移、导入导出 | 多平台共享同一用户状态 |
| M4 正确性与提醒 | Task 6-7 | 边界修复、doctor、可靠 systemd 单元 | 日常长期使用可用 |
| M5 分发质量 | Task 8-9 | 精简 skill、CI、0.2.0 发布包 | 可公开测试分发 |
| M6 学习智能 | Task 10 及其后续计划 | 自适应复习设计和 v0.3 计划 | 单独批准后实施 |

除紧急安全修复外，不跨里程碑并行修改同一批核心文件。每个里程碑完成后运行全部验证并创建可回退的 Git 标签候选，例如 `v0.2.0-rc1`。

## 9. 测试策略

### 9.1 单元测试

- 路径解析和状态目录优先级。
- SQLite 初始化、upsert、并发和迁移幂等。
- 日期、时长、统计和 500 天上限。
- systemd 单元转义和 doctor 状态。
- 同步工具和发布包过滤。

### 9.2 集成测试

- 从空状态目录执行 `today -> checkin -> summary -> export`。
- 从旧 JSON/JSONL 执行 `migrate -> summary -> export`。
- 三个平台分别从只读 skill 目录写入同一临时状态目录。
- Python 3.9 和 3.12 执行 bootstrap 与 quick check。

### 9.3 Skill 验证

- 三个 frontmatter validator 全部通过。
- 三种典型用户提示能够正确触发。
- 平台专属提醒边界不串用。
- `agents/openai.yaml` 与核心 description/命令保持一致。

### 9.4 发布验收

```bash
python3.12 tools/sync_distributions.py --check
python3.12 tools/verify_project.py --python claudecode-codex-opencode/.venv/bin/python
test -n "$SKILL_VALIDATOR"
python3.12 tools/verify_project.py \
  --python claudecode-codex-opencode/.venv/bin/python \
  --validator "$SKILL_VALIDATOR"
python3.12 tools/build_release.py --all --output-dir dist
git status --short
```

预期：所有命令退出 0；构建后除计划内的 `dist/` 忽略文件外，工作区没有运行数据或缓存变更。

## 10. 风险与回滚

| 风险 | 控制措施 | 回滚方式 |
| --- | --- | --- |
| 旧签到迁移错误 | 只复制、不删除旧文件；迁移幂等；导入前备份 | 使用旧 skill 目录继续运行，修复后重新迁移 |
| 三个平台生成错误 | `--check`、平台测试、发布包冒烟测试 | 回退同步工具提交，重新生成分发目录 |
| Python 版本收紧导致旧设备不可用 | 明确 3.9+，提供 uv 3.12 路径 | 保留 v0.1.x 发布包，不修改其数据 |
| SQLite schema 后续变化 | `schema_version` 和顺序迁移 | 从 `backups/` 恢复数据库 |
| Skill 正文精简后触发退化 | metadata 测试和真实提示验证 | 恢复上一版本 SKILL.md |
| 自适应任务影响学习稳定性 | v0.3 独立设计、默认可关闭 | 配置回退固定周主题算法 |

任何迁移步骤都不得自动删除旧数据；任何发布脚本都不得打包用户状态目录。

## 11. 完成定义

本优化计划完成至 M5 时，必须同时满足：

- [ ] 新设备只要具备 Python 3.9+ 或 uv，即可按文档完成安装。
- [ ] Python 版本不满足时在修改环境前快速失败，并给出可执行修复命令。
- [ ] 同一设备上的三个平台共享同一份用户数据库，skill 目录可以只读。
- [ ] 不同设备能够通过 `export` 和 `import --merge` 手动迁移同一份学习状态。
- [ ] 旧计划、签到和提醒日志可以无损、幂等迁移。
- [ ] 计划开始前汇总、非法时长、非法天数和路径空格均有回归测试。
- [ ] 三个平台共享文件漂移会导致本地验证和 CI 失败。
- [ ] Python 3.9/3.12、Linux/Windows/macOS CI 通过。
- [ ] 三个 skill validator 通过，平台元数据和提醒边界正确。
- [ ] 发布 ZIP 不包含环境、缓存或个人数据。
- [ ] README、SKILL.md、安装 reference 和实际命令一致。
- [ ] Git 工作区在日常 `today/checkin/summary/reminder` 后不出现运行数据修改。

M6 不作为 v0.2.0 的发布阻塞项；它必须在真实使用数据和独立设计评审后进入开发。

## 12. 执行纪律

- 每个 Task 使用独立提交，不把多个里程碑压进一个提交。
- 行为修改必须遵循红灯、绿灯、重构顺序。
- 每次修改共享文件后先运行同步工具，再运行全部验证。
- 不在测试中读取或写入真实用户状态目录。
- 不在日志、测试夹具、发布包或 Git 历史中提交个人签到原文。
- 开始下一个 Task 前，把当前 Task 的测试输出和迁移结果记录在提交或 PR 描述中。
- 实施过程中发现新范围时，先更新本计划或建立独立计划，不直接扩展当前 Task。
