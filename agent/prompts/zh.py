"""
中文提示词模板
==============
所有认知模块使用的 LLM 提示词，中文版本。

变量说明（使用 .format() 填充）：
    {identity}         — 角色身份信息（来自 scratch.get_str_iss()）
    {locations}        — 已知地点列表（每行一个）
    {task_desc}        — 当前任务描述（来自日程安排）
    {current_location} — 角色当前所在地址
    {current_time}     — 当前时间（HH:MM 格式）
    {statements}       — 记忆陈述列表（每行一条）
    {n}                — 需要生成的项目数量
    {nearby_agents}    — 同一地点的其他角色
    {other_name}       — 对话对象的名字
    {other_action}     — 对话对象正在做的事
    {my_action}        — 我正在做的事
    {chat_type}        — "small_talk" 或 "deep_talk"
    {current_round}    — 当前轮次
    {total_rounds}     — 总轮次
    {chat_history}     — 已有的对话记录
    {name}             — 角色名字（用于摘要）
    {summary}          — 对话摘要
"""

# 系统提示词：每次 LLM 请求都会发送（role: "system"）
SYSTEM_PROMPT = (
    '你是一个名为"小镇"的模拟世界中的角色。'
    '保持角色扮演。只按要求的格式输出，不要添加额外的解释。\n\n'
    '当你看到附近的其他角色时，你可以选择与他们交谈：\n'
    '- small_talk：1-5轮，随意问候或简短交流\n'
    '- deep_talk：6-20轮，关于你个性和兴趣的深入对话'
)

# =============================================================================
# 计划模块提示词
# =============================================================================

DAILY_SCHEDULE = """{identity}
为今天剩余时间制定日程安排。每个任务需要标注时长（分钟）。
总时长必须恰好为 {total_minutes} 分钟。
当前时间是 {start_time}。从这个时间开始安排日程。

世界中可用的地点：
{locations}

输出格式：每行一个任务，格式为"任务描述（X分钟）"
示例：
起床和晨间洗漱（60）
步行去咖啡馆（15）
在吧台为顾客服务（180）
午餐休息（60）
下午继续在咖啡馆工作（180）
关门后步行回家（30）
晚餐和休息（120）
晚间阅读（60）
睡觉（480）"""


ACTION_DETAIL = """{identity}
当前任务：{task_desc}
当前位置：{current_location}
当前时间：{current_time}

附近的其他角色（你可以看到他们）：
{nearby_agents}

可用地点（你必须从以下地点中选择一个作为行动地址）：
{locations}

为当前任务生成行动详情。每行输出一个字段。
pronunciatio 使用一个 Unicode 表情符号（不要用 :短代码:）。

同时决定是否想和附近的某个角色聊天：
- chat_type: none / small_talk / deep_talk
- chat_with: 角色名字（或 "none"）
- chat_rounds: 对话轮数（small_talk: 1-5轮，deep_talk: 6-20轮，none: 0）

示例输出：
address: 小镇:霍布斯咖啡馆:咖啡厅
description: 为顾客冲泡咖啡
pronunciatio: ☕
object_description: 咖啡机
object_pronunciatio: ☕
chat_type: small_talk
chat_with: Klaus Mueller
chat_rounds: 3"""


# =============================================================================
# 反思模块提示词
# =============================================================================

FOCAL_POINTS = """{identity}
我正在反思最近的经历。根据以下陈述，
找出{n}个最值得思考的重要问题。
关注模式、关系、目标和感受——而非表面细节。

陈述：
{statements}

输出{n}个问题，每行一个。
示例：
我最近都在吃什么？
我和其他人的关系如何？
我在目标上是否有进展？"""


INSIGHTS = """{identity}
我正在反思我的经历。根据以下陈述，
能得出{n}个什么模式或结论？

陈述：
{statements}

对于每个洞察，提供支持它的陈述编号。
输出格式：每行一个洞察，后面用方括号标注支持的编号。
示例：
我经常一个人吃饭 [0, 1, 2]
我应该邀请别人一起吃饭 [1, 2]"""


# =============================================================================
# 对话模块提示词
# =============================================================================

CHAT_PROMPT = """{identity}

我正在{my_action}。
我正在和{other_name}聊天，他/她正在{other_action}。
这是一次{chat_type}（第{current_round}轮，共{total_rounds}轮）。

对话记录：
{chat_history}

生成我的下一句话。保持角色扮演，自然一些。
输出格式：
message: <我要说的话>"""


SUMMARY_PROMPT = """{name}，用1-2句话从你自己的角度总结你和{other_name}的这段对话。

对话记录：
{chat_history}

重点描述你说了什么、你了解到了什么、以及你对这次交流的感受。"""
