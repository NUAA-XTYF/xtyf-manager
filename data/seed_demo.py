# -*- coding: utf-8 -*-
"""生成一套完全虚构的脱敏演示数据（成员 / 任务 / 资金 / 协作）。

数据写入独立的演示目录，默认与 `.local-test-data` 下服务器快照的使用方式一致：
`restored/` 保存数据库与业务文件，`use-demo-data.ps1` 在当前 PowerShell 会话中
设置数据路径。不会改动仓库源码、根目录 `data.db` 或 `data/` 中的真实数据。

用法：
    python data/seed_demo.py
    python data/seed_demo.py --reset
    python data/seed_demo.py --output D:\\demo-data

随后在仓库根目录执行：
    . .\\.local-test-data\\demo-workspace\\use-demo-data.ps1
    python app.py
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".local-test-data" / "demo-workspace"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = os.environ.get("DEMO_ADMIN_PASSWORD", "Demo@admin2026")
MEMBER_PASSWORD = os.environ.get("DEMO_MEMBER_PASSWORD", "Demo@2026")

parser = argparse.ArgumentParser(description="生成独立的脱敏演示数据")
parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                    help=f"演示数据目录（默认 {DEFAULT_OUTPUT}）")
parser.add_argument("--reset", action="store_true", help="删除演示目录中的 restored/ 后重建")
args = parser.parse_args()

OUTPUT = args.output.expanduser().resolve()
RESTORED = OUTPUT / "restored"
DATA_DIR = RESTORED / "data"
DB_PATH = RESTORED / "data.db"
SECRET_PATH = OUTPUT / "demo-secret.key"
CREDENTIALS_PATH = OUTPUT / "initial-admin-password.txt"

if args.reset and RESTORED.exists():
    shutil.rmtree(RESTORED)
    print(f"[重置] 已删除演示数据目录：{RESTORED}")

for directory in (DATA_DIR / "funds", DATA_DIR / "invoices", DATA_DIR / "task_attachments"):
    directory.mkdir(parents=True, exist_ok=True)

os.environ.update({
    "PROGRESS_DB": str(DB_PATH),
    "FUNDS_DIR": str(DATA_DIR / "funds"),
    "INVOICES_DIR": str(DATA_DIR / "invoices"),
    "TASK_ATTACHMENTS_DIR": str(DATA_DIR / "task_attachments"),
    "PROGRESS_SECRET_PATH": str(SECRET_PATH),
    "PROGRESS_INITIAL_CREDENTIALS_PATH": str(CREDENTIALS_PATH),
    "PROGRESS_INITIAL_ADMIN_PASSWORD": ADMIN_PASSWORD,
    "MAIL_MODE": "preview",
    "PORT": os.environ.get("PORT", "8520"),
})
sys.path.insert(0, str(ROOT))

from werkzeug.security import generate_password_hash  # noqa: E402

import app as application  # noqa: E402  （导入即建表并创建 admin）

GROUPS = ["研发", "设计", "测试", "运营", "宣传", "后勤"]
PROJECTS = ["官网", "移动端", "数据平台", "基础设施"]

# (姓名, 账号, 角色, 专业组, 所属项目)
MEMBERS = [
    ("林远", "lin_yuan", "manager", ["运营"], ["官网", "移动端"]),
    ("陈星", "chen_xing", "member", ["研发"], ["移动端"]),
    ("周锐", "zhou_rui", "member", ["研发"], ["数据平台"]),
    ("赵岩", "zhao_yan", "member", ["设计"], ["官网"]),
    ("王可", "wang_ke", "member", ["测试"], ["移动端", "基础设施"]),
    ("李萌", "li_meng", "member", ["宣传"], ["官网"]),
    ("孙浩", "sun_hao", "member", ["研发"], ["数据平台"]),
    ("吴桐", "wu_tong", "member", ["设计"], ["移动端"]),
    ("郑宇", "zheng_yu", "member", ["测试"], ["基础设施"]),
    ("何晴", "he_qing", "member", ["运营"], ["官网"]),
    ("郭峰", "guo_feng", "member", ["研发"], ["基础设施"]),
]

# key: 标题, 负责人, 专业组, 所属项目, 状态, 进度, 优先级, 开始, 截止, 参与者, 前置, 说明
TASKS = [
    ("website_redesign", "官网首页信息架构改版", "zhao_yan", ["设计"], "官网", "进行中", 65, "高",
     "2026-10-20", "2026-11-30", ["li_meng"], [],
     "调整首页栏目层级与视觉节奏，补充移动端断点，目标把首屏加载控制在 2 秒内。"),
    ("mobile_login", "移动端登录与找回密码优化", "chen_xing", ["研发"], "移动端", "进行中", 40, "高",
     "2026-11-02", "2026-11-25", ["zhou_rui"], ["website_redesign"],
     "统一登录、验证码与找回密码流程，重点验证弱网和重复提交场景。"),
    ("design_system", "设计规范 v3 组件整理", "wu_tong", ["设计"], "移动端", "已完成", 100, "中",
     "2026-10-10", "2026-10-25", ["zhao_yan"], [],
     "整理按钮、表单和反馈组件的间距与状态，输出可复用清单。"),
    ("metric_definition", "数据看板指标口径梳理", "zhou_rui", ["研发"], "数据平台", "阻塞", 30, "高",
     "2026-10-28", "2026-11-20", [], [],
     "统一活跃、留存和转化指标的计算口径，补充指标字典与示例。",
     {"blocker_reason": "上游业务口径尚未确认",
      "blocker_next_action": "安排与业务方评审指标定义，先冻结本期范围",
      "blocker_helper": "lin_yuan", "blocker_follow_up": "2026-11-12"}),
    ("api_docs", "开放接口文档补充", "sun_hao", ["研发"], "数据平台", "进行中", 55, "高",
     "2026-11-02", "2026-11-28", ["zheng_yu"], [],
     "补齐鉴权、分页和错误码说明，用示例请求覆盖常见集成场景。"),
    ("release_cache", "发布流水线缓存优化", "guo_feng", ["研发"], "基础设施", "未开始", 0, "中",
     "2026-11-15", "2026-12-05", [], ["api_docs"],
     "复用依赖与构建缓存，减少重复下载，记录优化前后耗时。"),
    ("mobile_offline", "移动端离线缓存测试", "wang_ke", ["测试"], "移动端", "进行中", 20, "中",
     "2026-11-05", "2026-11-30", [], [],
     "覆盖断网、弱网和恢复连接场景，验证缓存过期与冲突处理。"),
    ("survey", "用户满意度问卷回收", "he_qing", ["运营"], "官网", "未开始", 0, "低",
     "2026-11-20", "2026-12-10", [], [],
     "设计 10 分钟以内的问卷，按用户分层抽样并汇总开放题。"),
    ("promo_video", "秋季宣传片剪辑", "li_meng", ["宣传"], "官网", "已完成", 100, "低",
     "2026-10-01", "2026-10-20", [], [],
     "完成宣传片粗剪、配乐和字幕，已发布到内部频道。"),
    ("onboarding", "新成员入职培训计划", "lin_yuan", ["运营"], None, "未开始", 0, "中",
     "2026-11-10", "2026-11-30", ["he_qing"], [],
     "安排环境搭建、代码规范和轮岗计划，输出培训记录。"),
    ("procurement", "季度物资采购清单", "he_qing", ["运营"], None, "进行中", 70, "中",
     "2026-10-25", "2026-11-15", [], [],
     "汇总各组需求，比价后分批下单，跟踪到货和发票。"),
    ("monitoring", "监控告警规则调整", "zheng_yu", ["测试"], "基础设施", "进行中", 45, "中",
     "2026-10-30", "2026-11-30", [], [],
     "收敛重复告警，补充服务健康度与错误率阈值。"),
    ("stress_test", "数据导出压力测试", "wang_ke", ["测试"], "数据平台", "未开始", 0, "高",
     "2026-12-01", "2026-12-15", ["zhou_rui"], ["metric_definition"],
     "验证大批量导出时的内存占用、超时和重试行为。"),
    ("faq", "客户支持 FAQ 更新", "he_qing", ["运营"], "官网", "已完成", 100, "低",
     "2026-10-22", "2026-11-03", [], [],
     "根据近期工单补充常见问题，统一措辞并补充搜索关键词。"),
    ("design_review", "设计规范评审", "zhao_yan", ["设计"], "移动端", "已取消", 0, "低",
     "2026-10-12", "2026-10-30", [], [],
     "原计划评审因组件范围调整取消，结论已并入 v3 组件整理。"),
    ("cdn_plan", "静态资源 CDN 方案", "guo_feng", ["研发"], "基础设施", "未开始", 0, "中",
     "2026-12-05", "2026-12-20", [], [],
     "评估缓存策略、回源和灰度切换，准备上线检查清单。"),
    ("data_migration", "历史数据迁移演练", "zhou_rui", ["研发"], "数据平台", "进行中", 35, "中",
     "2026-11-06", "2026-11-22", [], [],
     "在隔离环境重放迁移脚本，记录耗时、校验行数与回滚步骤。"),
    ("docs_site", "帮助中心站点搭建", "sun_hao", ["研发"], "官网", "未开始", 0, "低",
     "2026-12-01", "2026-12-25", [], [],
     "搭建静态帮助中心，接入站内搜索和版本切换。"),
    ("security_scan", "依赖安全扫描与修复", "zheng_yu", ["测试"], "基础设施", "进行中", 60, "高",
     "2026-11-01", "2026-11-18", [], [],
     "扫描直接与间接依赖，优先修复高危项并记录例外。"),
    ("annual_plan", "年度技术路线规划", "lin_yuan", ["研发"], None, "未开始", 0, "中",
     "2026-12-01", "2026-12-20", [], [],
     "汇总各组技术债与业务目标，形成下一阶段路线图。"),
]

# (记录类型, 金额, 类别, 来源/去向, 申请人, 发票数, 处理人, 日期, 备注)
FUNDS = [
    ("进", "5000.00", "赞助", "合作方项目启动资金", "林远", 1, "何晴", "2026-09-05", "年度合作第一期"),
    ("出", "1280.00", "设备", "开发用显示器", "赵岩", 1, "何晴", "2026-09-18", "报价单与发票已归档"),
    ("出", "860.00", "软件订阅", "设计工具年度订阅", "吴桐", 1, "何晴", "2026-09-25", "团队版 5 席位"),
    ("出", "450.00", "耗材", "办公耗材补充", "何晴", 1, "何晴", "2026-10-02", "线材与打印纸"),
    ("进", "12000.00", "预算", "部门季度预算", "林远", 2, "何晴", "2026-10-08", "分两笔到账"),
    ("出", "2200.00", "设备", "测试手机与平板", "王可", 1, "何晴", "2026-10-12", "用于兼容性测试"),
    ("出", "680.00", "差旅", "用户访谈往返交通", "李萌", 2, "何晴", "2026-10-19", "4 人往返"),
    ("进", "3000.00", "赞助", "团队文化衫赞助", "李萌", 1, "何晴", "2026-10-20", "印制费用由赞助覆盖"),
    ("出", "1500.00", "宣传", "宣传片拍摄与剪辑", "李萌", 1, "何晴", "2026-10-26", "含外拍交通"),
    ("出", "3200.00", "服务", "云服务器季度费用", "郭峰", 2, "何晴", "2026-11-03", "测试与生产两套环境"),
    ("出", "540.00", "耗材", "打印与装订耗材", "何晴", 1, "何晴", "2026-11-06", "季度补充"),
    ("出", "990.00", "软件订阅", "监控与日志服务", "郑宇", 1, "何晴", "2026-11-08", "按量套餐"),
    ("出", "260.00", "办公", "资料打印装订", "何晴", 1, "林远", "2026-11-09", "培训材料"),
    ("出", "780.00", "设备", "补光灯与拍摄支架", "李萌", 1, "何晴", "2026-11-09", "内容拍摄使用"),
]

TOPICS = [
    ("第四季度发布排期（11/10-11/25）", "lin_yuan", [
        ("chen_xing", "移动端收到，11/12 前把登录流程的联调版本发到群里。"),
        ("zhou_rui", "数据平台这边 11/14 完成指标口径评审，之后可以配合联调。"),
    ]),
    ("数据看板指标定义评审，大家看看还有没有遗漏", "zhou_rui", [
        ("sun_hao", "建议补充异常流量的剔除规则，上一期这块返工最多。"),
        ("guo_feng", "监控告警也可以复用这套指标命名，我整理一下字段。"),
    ]),
    ("本周报销与物资领用提醒", "he_qing", [
        ("zhao_yan", "设计工具的订阅发票已经交到财务，麻烦帮忙登记。"),
    ]),
]

TOPICS_BODY = {
    "第四季度发布排期（11/10-11/25）":
        "本周开始第四季度发布准备，请各组按下面排期执行：\n"
        "1. 11/10-11/13 移动端登录流程联调；\n"
        "2. 11/14-11/18 数据平台接口与看板联调；\n"
        "3. 11/19-11/22 官网内容与视觉复查；\n"
        "4. 11/23-11/25 全流程回归与发布复盘。\n"
        "有冲突直接在话题里回复。",
    "数据看板指标定义评审，大家看看还有没有遗漏":
        "本版指标字典主要改了三处：\n"
        "1. 统一活跃与留存的统计窗口；\n"
        "2. 异常流量单独标记，不计入转化；\n"
        "3. 导出字段与看板展示保持一致。\n"
        "文档在团队空间，欢迎补充。",
    "本周报销与物资领用提醒":
        "本周五前把上个月以来的发票和报销单交到运营组，逾期顺延到下周统一处理。\n"
        "物资领用请先在群里登记，避免重复采购。",
}


def login_client(username: str, password: str):
    client = application.app.test_client()
    token = client.get("/api/csrf").get_json()["csrf_token"]
    response = client.post("/login", json={"username": username, "password": password},
                           headers={"X-CSRF-Token": token})
    assert response.status_code == 200 and response.get_json().get("ok"), \
        f"登录失败 {username}: {response.status_code} {response.get_data(as_text=True)[:300]}"
    client.demo_token = client.get("/api/csrf").get_json()["csrf_token"]
    return client


def call(client, method: str, path: str, *, expect=(200, 201), **kwargs):
    headers = {"X-CSRF-Token": client.demo_token}
    response = getattr(client, method)(path, headers=headers, **kwargs)
    if response.status_code not in expect:
        raise RuntimeError(f"{method.upper()} {path} -> {response.status_code}: "
                           f"{response.get_data(as_text=True)[:500]}")
    data = response.get_json(silent=True)
    if isinstance(data, dict) and data.get("ok") is False:
        raise RuntimeError(f"{method.upper()} {path} 失败: {data}")
    return data


def write_launcher():
    script = f"""$fixtureRoot = Join-Path $PSScriptRoot 'restored'
$env:PROGRESS_DB = Join-Path $fixtureRoot 'data.db'
$env:FUNDS_DIR = Join-Path $fixtureRoot 'data/funds'
$env:INVOICES_DIR = Join-Path $fixtureRoot 'data/invoices'
$env:TASK_ATTACHMENTS_DIR = Join-Path $fixtureRoot 'data/task_attachments'
# The application creates a separate local signing key on first startup.
$env:PROGRESS_SECRET_PATH = Join-Path $PSScriptRoot 'demo-secret.key'
$env:PROGRESS_INITIAL_CREDENTIALS_PATH = Join-Path $PSScriptRoot 'initial-admin-password.txt'
$env:MAIL_MODE = 'preview'
$env:PORT = '{os.environ.get("PORT", "8520")}'
Write-Host "Demo data selected: $fixtureRoot"
"""
    (OUTPUT / "use-demo-data.ps1").write_text(script, encoding="utf-8")


def write_docs():
    readme = f"""# 脱敏演示数据

本目录由 `data/seed_demo.py` 生成，全部成员、任务、资金和话题均为虚构，
不包含任何真实团队、学校、成员或业务数据。

- `restored/`：演示数据库与业务文件。运行应用会修改这里，重新生成请加 `--reset`。
- `use-demo-data.ps1`：在当前 PowerShell 会话中设置演示数据路径，不启动应用。
- `demo-secret.key`：演示环境独立的会话签名密钥，与应用源码分离。
- `provenance.json`：生成时间与数据性质说明。

在仓库根目录运行：

```powershell
. .\\.local-test-data\\demo-workspace\\use-demo-data.ps1
python app.py
```

随后访问 `http://127.0.0.1:{os.environ.get("PORT", "8520")}`。

演示账号：

- 管理员：`{ADMIN_USERNAME}` / `{ADMIN_PASSWORD}`
- 普通成员：`chen_xing` / `{MEMBER_PASSWORD}`（陈星，研发）
- 项管：`lin_yuan` / `{MEMBER_PASSWORD}`（林远，运营）

这些环境变量只影响当前 PowerShell 会话，关闭会话即可清除。
整个 `.local-test-data/` 由仓库本地排除规则忽略，不要强制加入 Git。
"""
    (OUTPUT / "README.md").write_text(readme, encoding="utf-8")
    provenance = {
        "kind": "synthetic-demo",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "generator": "data/seed_demo.py",
        "contains_real_data": False,
        "accounts": {"admin": ADMIN_USERNAME, "manager": "lin_yuan", "member": "chen_xing"},
    }
    (OUTPUT / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute(
            "UPDATE members SET name=?, password_hash=?, role='admin', is_active=1, deleted_at=NULL, "
            "must_change_password=0 WHERE username=?",
            ("管理员", generate_password_hash(ADMIN_PASSWORD), ADMIN_USERNAME))
        if con.execute("SELECT 1 FROM members WHERE username=?", (ADMIN_USERNAME,)).fetchone() is None:
            con.execute(
                "INSERT INTO members(name,username,password_hash,group_name,role,created_at,must_change_password) "
                "VALUES(?,?,?,'','admin',datetime('now','localtime'),0)",
                ("管理员", ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD)))
        if con.execute("SELECT 1 FROM members WHERE username='chen_xing'").fetchone():
            print("检测到已有演示数据（chen_xing 已存在），跳过导入。如需重建请加 --reset。")
            write_launcher()
            write_docs()
            return
        con.commit()
    finally:
        con.close()

    admin = login_client(ADMIN_USERNAME, ADMIN_PASSWORD)

    # ---- 组别与项目（迁移会预置常用项，只补缺失的） ----
    group_ids = {row["name"]: row["id"] for row in call(admin, "get", "/api/groups")["groups"]}
    project_ids = {row["name"]: row["id"] for row in call(admin, "get", "/api/projects")["projects"]}
    for name in GROUPS:
        if name not in group_ids:
            call(admin, "post", "/api/groups", json={"name": name})
    for name in PROJECTS:
        if name not in project_ids:
            call(admin, "post", "/api/projects", json={"name": name})
    group_ids = {row["name"]: row["id"] for row in call(admin, "get", "/api/groups")["groups"]}
    project_ids = {row["name"]: row["id"] for row in call(admin, "get", "/api/projects")["projects"]}
    # 演示库初始化时会预置通用专业组；删除本演示不需要的默认项，避免展示机器人领域词。
    con = sqlite3.connect(DB_PATH)
    try:
        placeholders = ",".join("?" for _ in GROUPS)
        con.execute(
            f"DELETE FROM groups WHERE name NOT IN ({placeholders})",
            GROUPS,
        )
        con.commit()
    finally:
        con.close()

    # ---- 成员 ----
    member_ids = {}
    con = sqlite3.connect(DB_PATH)
    try:
        for name, username, role, groups, projects in MEMBERS:
            data = call(admin, "post", "/api/member", json={
                "name": name, "username": username, "password": MEMBER_PASSWORD,
                "role": role,
                "group_ids": [group_ids[item] for item in groups],
                "project_ids": [project_ids[item] for item in projects],
            })
            member_ids[username] = data["id"]
            con.execute("UPDATE members SET must_change_password=0 WHERE id=?", (data["id"],))
            con.commit()
    finally:
        con.close()
    print(f"[成员] 已创建 {len(member_ids)} 位演示成员")

    # ---- 任务 ----
    task_ids = {}
    versions = {}
    for row in TASKS:
        key, title, owner, groups, project, status, progress, priority, start, due, participants, predecessors, detail, *rest = row
        payload = {
            "title": title,
            "detail": detail,
            "owner_id": member_ids[owner],
            "project_id": project_ids[project] if project else None,
            "group_ids": [group_ids[item] for item in groups],
            "participant_ids": [member_ids[item] for item in participants],
            "predecessor_ids": [task_ids[item] for item in predecessors],
            "status": status,
            "progress": progress,
            "priority": priority,
            "start_date": start,
            "due_date": due,
        }
        if rest and rest[0]:
            blocker = rest[0]
            payload.update({
                "blocker_reason": blocker["blocker_reason"],
                "blocker_next_action": blocker["blocker_next_action"],
                "blocker_helper_id": member_ids.get(blocker.get("blocker_helper"), None),
                "blocker_follow_up": blocker.get("blocker_follow_up", ""),
            })
        data = call(admin, "post", "/api/task", json=payload)
        task_ids[key] = data["id"]
        versions[key] = data["version"]
    print(f"[任务] 已创建 {len(task_ids)} 条任务")

    # ---- 进度动态（让任务时间线有内容） ----
    for key, progress, note in [
        ("website_redesign", 65, "首页信息架构调整完成，移动端断点已补齐，下一步压缩首屏资源。"),
        ("api_docs", 55, "鉴权与分页说明已补齐，正在补充错误码示例。"),
        ("data_migration", 35, "迁移脚本在隔离环境重放成功，正在校验行数与耗时。"),
    ]:
        call(admin, "post", f"/api/task/{task_ids[key]}/progress", data={
            "progress": str(progress), "note": note, "version": str(versions[key])})

    # ---- 资金记录 ----
    record_ids = []
    for record_type, amount, category, target, applicant, count, handler, date, notes in FUNDS:
        data = call(admin, "post", "/funds/api/records", json={
            "request_id": "demo-" + uuid.uuid4().hex,
            "record_type": record_type,
            "amount": amount,
            "category": category,
            "source_dest": target,
            "applicant": applicant,
            "invoice_count": count,
            "handler": handler,
            "record_date": date,
            "notes": notes,
        })
        record_ids.append(data["id"])
    # 前 10 条已审核，后 4 条留待演示审核流程。
    for rid in record_ids[:10]:
        call(admin, "post", f"/funds/api/records/{rid}/review", json={"version": 1})
    print(f"[资金] 已创建 {len(record_ids)} 条记录，其中 10 条已审核、4 条待审核")

    # ---- 协作话题（切换真实作者，保留未读/回复体验） ----
    clients = {name: login_client(name, MEMBER_PASSWORD)
               for name in ("lin_yuan", "chen_xing", "sun_hao", "zhou_rui", "guo_feng", "he_qing", "zhao_yan")}
    topic_count = 0
    for title, author, replies in TOPICS:
        client = clients[author]
        data = call(client, "post", "/discussions/api/topics", json={
            "submission_id": "demo-" + uuid.uuid4().hex,
            "title": title,
            "body": TOPICS_BODY.get(title, ""),
        })
        topic_count += 1
        topic_id = data.get("topic_id")
        for reply_author, body in replies:
            call(clients[reply_author], "post", f"/discussions/api/topics/{topic_id}/messages", json={
                "submission_id": "demo-" + uuid.uuid4().hex,
                "body": body,
            })
    print(f"[协作] 已创建 {topic_count} 个话题及回复")

    write_launcher()
    write_docs()
    print(f"\n演示数据目录：{RESTORED}")
    print("\n完成。演示账号：")
    print(f"  管理员  {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    print(f"  普通成员（lin_yuan 为项管） / {MEMBER_PASSWORD}")
    print(f"  例：chen_xing / {MEMBER_PASSWORD}（陈星，研发）")
    print("\n启动：")
    print(f"  . '{os.path.relpath(OUTPUT, ROOT)}\\use-demo-data.ps1'")
    print("  python app.py  然后访问 http://127.0.0.1:%s" % os.environ.get("PORT", "8520"))


if __name__ == "__main__":
    main()
