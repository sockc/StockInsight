from .schemas import PolicyCategory, PolicyResponse


POLICY_CATEGORIES = [
    PolicyCategory(
        key="export_control",
        name="半导体出口限制",
        status="tracking",
        explanation="记录规则变化，并拆分公司直接暴露、客户暴露、板块暴露和市场情绪传导。",
    ),
    PolicyCategory(
        key="tariff",
        name="关税与贸易政策",
        status="tracking",
        explanation="跟踪关税、贸易限制及供应链成本/需求传导。",
    ),
    PolicyCategory(
        key="ai_regulation",
        name="AI监管",
        status="tracking",
        explanation="跟踪AI计算、模型训练、数据中心与芯片需求相关监管。",
    ),
    PolicyCategory(
        key="fed",
        name="美联储与利率",
        status="tracking",
        explanation="记录FOMC、利率路径及美债收益率变化，并统计ARM历史实际反应。",
    ),
    PolicyCategory(
        key="semiconductor_subsidy",
        name="半导体补贴与产业政策",
        status="tracking",
        explanation="跟踪政府补贴、制造投资、数据中心投资和客户资本开支传导。",
    ),
]


def policy_response(symbol: str) -> PolicyResponse:
    return PolicyResponse(
        symbol=symbol.upper(),
        categories=POLICY_CATEGORIES,
        recent_events=[],
        data_mode="schema_ready",
        note="V0.1 已建立政策分类和事件反应数据库结构；V0.2 接入真实政策/新闻源后才计算影响，不使用主观利好/利空评分。",
    )
