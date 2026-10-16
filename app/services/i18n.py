"""CropFlow Internationalization (i18n) Service.
Provides comprehensive translations in English (en), Marathi (mr), and Chinese (zh).
"""

from typing import Dict, Any, Optional

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # Brand and Header
    "app_title": {
        "en": "CropFlow - Optimal Irrigation Scheduling",
        "mr": "क्रॉपफ्लो - इष्टतम सिंचन वेळापत्रक",
        "zh": "CropFlow - 最优灌溉调度系统"
    },
    "brand_name": {
        "en": "CropFlow",
        "mr": "क्रॉपफ्लो",
        "zh": "CropFlow"
    },
    "brand_tagline": {
        "en": "Irrigation AI & Water Optimization",
        "mr": "सिंचन एआय आणि पाणी नियोजन",
        "zh": "智能灌溉与水资源优化"
    },
    "optimizers_ready": {
        "en": "Optimizers Ready",
        "mr": "ऑप्टिमायझर्स तयार",
        "zh": "优化器已就绪"
    },
    "connected": {
        "en": "Connected",
        "mr": "जोडलेले",
        "zh": "已连接"
    },

    # Navigation
    "nav_operations": {
        "en": "Operations",
        "mr": "कामकाज",
        "zh": "核心操作"
    },
    "nav_architecture": {
        "en": "Architecture",
        "mr": "रचना व माहिती",
        "zh": "系统架构"
    },
    "nav_dashboard": {
        "en": "Dashboard",
        "mr": "डॅशबोर्ड (नियंत्रण कक्ष)",
        "zh": "仪表板"
    },
    "nav_farms": {
        "en": "Farms & Plots",
        "mr": "शेत आणि भूखंड",
        "zh": "农场与地块"
    },
    "nav_results": {
        "en": "Results & Audits",
        "mr": "निकाल आणि ऑडिट",
        "zh": "结果与审计"
    },
    "nav_overview": {
        "en": "System Overview",
        "mr": "प्रणाली आढावा",
        "zh": "系统概览"
    },
    "nav_health": {
        "en": "Health Check",
        "mr": "आरोग्य तपासणी",
        "zh": "健康检查"
    },

    # Common Buttons and Actions
    "btn_run_all": {
        "en": "Run All 3 Algorithms",
        "mr": "सर्व ३ अल्गोरिदम चालवा",
        "zh": "运行全部3种算法"
    },
    "btn_new_farm": {
        "en": "New Farm",
        "mr": "नवीन शेत",
        "zh": "新建农场"
    },
    "btn_add_plot": {
        "en": "Add Plot",
        "mr": "भूखंड जोडा",
        "zh": "添加地块"
    },
    "btn_add_another_plot": {
        "en": "Add Another Plot",
        "mr": "आणखी भूखंड जोडा",
        "zh": "添加另一个地块"
    },
    "btn_reset_farm": {
        "en": "Reset Sample Farm",
        "mr": "नमुना शेत रीसेट करा",
        "zh": "重置示例农场"
    },
    "btn_save": {
        "en": "Save",
        "mr": "जतन करा",
        "zh": "保存"
    },
    "btn_save_plot": {
        "en": "Save Plot",
        "mr": "भूखंड जतन करा",
        "zh": "保存地块"
    },
    "btn_save_farm": {
        "en": "Save Farm",
        "mr": "शेत जतन करा",
        "zh": "保存农场"
    },
    "btn_cancel": {
        "en": "Cancel",
        "mr": "रद्द करा",
        "zh": "取消"
    },
    "btn_auto_id": {
        "en": "Auto-generate Next ID",
        "mr": "पुढील आयडी आपोआप तयार करा",
        "zh": "自动生成下一个编号"
    },
    "btn_export_csv": {
        "en": "Export CSV",
        "mr": "CSV निर्यात करा",
        "zh": "导出 CSV"
    },
    "btn_export_json": {
        "en": "Export JSON",
        "mr": "JSON निर्यात करा",
        "zh": "导出 JSON"
    },
    "full_report": {
        "en": "Full Report",
        "mr": "संपूर्ण अहवाल",
        "zh": "完整报告"
    },
    "live_solver": {
        "en": "Live Solver",
        "mr": "थेट सॉल्व्हर",
        "zh": "实时求解器"
    },
    "optimizing": {
        "en": "Optimizing...",
        "mr": "ऑप्टिमायझिंग सुरू आहे...",
        "zh": "正在优化计算..."
    },

    # Dashboard Headings
    "page_dashboard_title": {
        "en": "Irrigation Command Dashboard",
        "mr": "सिंचन आदेश व नियंत्रण कक्ष",
        "zh": "灌溉指挥与调度控制面板"
    },
    "page_operational_dashboard": {
        "en": "Operational Dashboard",
        "mr": "कार्यरत नियंत्रण कक्ष",
        "zh": "运行仪表板"
    },
    "active_farm": {
        "en": "Active Farm",
        "mr": "सक्रिय शेत",
        "zh": "当前农场"
    },
    "location": {
        "en": "Location",
        "mr": "स्थान",
        "zh": "位置"
    },
    "area": {
        "en": "Area",
        "mr": "क्षेत्रफळ",
        "zh": "面积"
    },
    "reservoir": {
        "en": "Reservoir",
        "mr": "पाणी साठा",
        "zh": "蓄水池"
    },
    "budget": {
        "en": "Budget",
        "mr": "पाणी बजेट",
        "zh": "水预算"
    },

    # KPI Summary Cards
    "kpi_available_water": {
        "en": "Available Water / Total Demand",
        "mr": "उपलब्ध पाणी / एकूण मागणी",
        "zh": "可用水量 / 总需水量"
    },
    "kpi_allocated_water": {
        "en": "Allocated & Unmet Demand",
        "mr": "वाटप केलेले पाणी व अपूर्ण मागणी",
        "zh": "已分配水量与未满足需求"
    },
    "kpi_water_utilization": {
        "en": "Water Utilization Rate",
        "mr": "पाणी वापर कार्यक्षमता दर",
        "zh": "水资源利用率"
    },
    "kpi_estimated_cost": {
        "en": "Estimated Irrigation Cost",
        "mr": "अंदाजे सिंचन खर्च",
        "zh": "预计灌溉成本"
    },
    "kpi_net_return": {
        "en": "Net Economic Return",
        "mr": "निव्वळ आर्थिक परतावा",
        "zh": "净经济收益"
    },
    "kpi_execution_times": {
        "en": "Algorithm Execution Times (Actual Outputs)",
        "mr": "अल्गोरिदम अंमलबजावणी वेळ (प्रत्यक्ष मोजलेले निकाल)",
        "zh": "算法运行耗时 (实测输出)"
    },
    "benchmark_subtitle": {
        "en": "Live benchmark measured on the current agricultural dataset",
        "mr": "सध्याच्या शेती डेटावर थेट मोजलेले बेंचमार्क",
        "zh": "基于当前农田数据集的实时测定性能"
    },
    "deficit": {
        "en": "Deficit",
        "mr": "तूट",
        "zh": "亏缺"
    },
    "surplus": {
        "en": "Surplus",
        "mr": "शिल्लक",
        "zh": "盈余"
    },
    "unmet": {
        "en": "Unmet",
        "mr": "अपूर्ण",
        "zh": "未满足"
    },
    "coverage": {
        "en": "Coverage",
        "mr": "कव्हरेज",
        "zh": "满足率"
    },
    "pumping": {
        "en": "Pumping",
        "mr": "पंपिंग प्रवाह",
        "zh": "水泵流量"
    },
    "jain_eq": {
        "en": "Jain Eq",
        "mr": "जैन समता",
        "zh": "Jain 公平指数"
    },
    "net_return_label": {
        "en": "Net Return:",
        "mr": "निव्वळ परतावा:",
        "zh": "净收益:"
    },

    # Algorithms
    "alg_greedy": {
        "en": "Greedy Allocation",
        "mr": "लोभी वाटप (Greedy)",
        "zh": "贪心分配 (Greedy)"
    },
    "alg_greedy_desc": {
        "en": "Priority queue triage • O(N log N)",
        "mr": "प्राधान्य क्रमवारी ट्रायज • O(N log N)",
        "zh": "优先队列分流 • O(N log N)"
    },
    "alg_dp": {
        "en": "Dynamic Programming",
        "mr": "डायनॅमिक प्रोग्रामिंग (DP)",
        "zh": "动态规划 (DP)"
    },
    "alg_dp_desc": {
        "en": "Discretized Bellman knapsack • O(N × M × K)",
        "mr": "विभक्त बेलमन नॅपसॅक • O(N × M × K)",
        "zh": "离散贝尔曼背包 • O(N × M × K)"
    },
    "alg_hybrid": {
        "en": "Hybrid (Greedy + DP)",
        "mr": "हायब्रिड धोरण (Hybrid)",
        "zh": "混合优化策略 (Hybrid)"
    },
    "alg_hybrid_desc": {
        "en": "Survival anchor + refinement",
        "mr": "अस्तित्व आधार + स्थानिक सुधारणा",
        "zh": "保底存活 + 精细优化"
    },
    "proposed_tag": {
        "en": "PROPOSED",
        "mr": "प्रस्तावित",
        "zh": "推荐方案"
    },

    # Drought Simulator
    "sim_title": {
        "en": "Drought Scenario Simulator",
        "mr": "परस्परसंवादी दुष्काळ परिस्थिती सिम्युलेटर",
        "zh": "干旱情景模拟器"
    },
    "sim_desc": {
        "en": "Slide to simulate drought curtailment and dynamically re-run water optimization across all plots.",
        "mr": "दुष्काळाची तीव्रता बदलण्यासाठी स्लाइडर हलवा आणि सर्व भूखंडांसाठी सिंचनाचे त्वरित पुनर्गणन करा.",
        "zh": "拖动滑块模拟干旱限水情景，实时重新计算各地块的水资源分配。"
    },
    "tier_normal": {
        "en": "Normal (100%)",
        "mr": "सामान्य (१००%)",
        "zh": "正常 (100%)"
    },
    "tier_mild": {
        "en": "Mild (75%)",
        "mr": "हलका दुष्काळ (७५%)",
        "zh": "轻度干旱 (75%)"
    },
    "tier_moderate": {
        "en": "Moderate (50%)",
        "mr": "मध्यम दुष्काळ (५०%)",
        "zh": "中度干旱 (50%)"
    },
    "tier_severe": {
        "en": "Severe (25%)",
        "mr": "गंभीर दुष्काळ (२५%)",
        "zh": "重度干旱 (25%)"
    },
    "tier_emergency": {
        "en": "Emergency (10%)",
        "mr": "आपत्कालीन (१०%)",
        "zh": "紧急限水 (10%)"
    },

    # Charts and Plots
    "plot_allocation_title": {
        "en": "Water Allocation by Plot",
        "mr": "भूखंडनिहाय पाणी वाटप",
        "zh": "各地块水资源分配"
    },
    "plot_allocation_desc": {
        "en": "Demand vs Allocated Water volume per agricultural plot",
        "mr": "प्रत्येक शेती भूखंडाची मागणी विरुद्ध वाटप केलेले पाणी",
        "zh": "各地块需水量与已分配水量对比"
    },
    "strategy_comparison_title": {
        "en": "Strategy Comparison",
        "mr": "धोरणांची तुलना",
        "zh": "策略综合对比"
    },
    "strategy_comparison_desc": {
        "en": "Greedy vs Dynamic Programming vs Hybrid",
        "mr": "लोभी विरुद्ध डायनॅमिक प्रोग्रामिंग विरुद्ध हायब्रिड",
        "zh": "贪心算法 vs 动态规划 vs 混合策略"
    },
    "drought_curve_title": {
        "en": "Yield Preservation Across Drought Severities",
        "mr": "दुष्काळाच्या विविध टप्प्यांत पीक उत्पादन रक्षण",
        "zh": "不同干旱程度下的保产对比"
    },
    "drought_curve_desc": {
        "en": "Illustrates how the Hybrid strategy prevents complete starvation in severe drought conditions.",
        "mr": "गंभीर दुष्काळात हायब्रिड धोरण पिकांचे संपूर्ण नुकसान कसे टाळते हे दर्शवते.",
        "zh": "展示混合策略如何在严重干旱下避免地块绝收。"
    },

    # Detailed Table
    "detailed_table_title": {
        "en": "Detailed Plot Demand, Allocation & Unmet Water Table",
        "mr": "तपशीलवार भूखंड मागणी, वाटप आणि अपूर्ण पाणी तक्ता",
        "zh": "详细地块需水量、分配量与未满足需水表"
    },
    "detailed_table_desc": {
        "en": "Auditable engineering breakdown across all managed agricultural plots",
        "mr": "सर्व शेती भूखंडांचे ऑडिट करण्यायोग्य अभियांत्रिकी विश्लेषण",
        "zh": "所有受管地块的可审计工程细目"
    },
    "th_plot_id_name": {
        "en": "Plot ID & Name",
        "mr": "भूखंड क्र. व नाव",
        "zh": "地块编号与名称"
    },
    "th_crop_stage": {
        "en": "Crop & Stage",
        "mr": "पीक आणि अवस्था",
        "zh": "作物与生长阶段"
    },
    "th_soil_area": {
        "en": "Soil & Area",
        "mr": "माती आणि क्षेत्रफळ",
        "zh": "土壤与面积"
    },
    "th_moisture": {
        "en": "Moisture",
        "mr": "ओलावा",
        "zh": "土壤湿度"
    },
    "th_demand_m3": {
        "en": "Demand (m³)",
        "mr": "मागणी (m³)",
        "zh": "需水量 (m³)"
    },
    "th_allocated_m3": {
        "en": "Allocated (m³)",
        "mr": "वाटप (m³)",
        "zh": "分配量 (m³)"
    },
    "th_unmet_m3": {
        "en": "Unmet (m³)",
        "mr": "अपूर्ण (m³)",
        "zh": "未满足 (m³)"
    },
    "th_coverage_pct": {
        "en": "Coverage (%)",
        "mr": "कव्हरेज (%)",
        "zh": "满足率 (%)"
    },
    "th_yield_pct": {
        "en": "Yield (%)",
        "mr": "उत्पादन (%)",
        "zh": "保产率 (%)"
    },
    "th_cost_rs": {
        "en": "Cost (₹)",
        "mr": "खर्च (₹)",
        "zh": "成本 (₹)"
    },

    # History Table
    "history_runs": {
        "en": "Recent Optimization History View",
        "mr": "अलीकडील ऑप्टिमायझेशन इतिहास",
        "zh": "近期优化历史记录"
    },
    "recent_history_desc": {
        "en": "Historical algorithm executions logged in SQLite database",
        "mr": "एसक्यूलाइट डेटाबेसमध्ये नोंदवलेली मागील अल्गोरिदम अंमलबजावणी",
        "zh": "SQLite数据库记录的历次算法运行"
    },
    "full_audit_log": {
        "en": "Full Audit Log",
        "mr": "संपूर्ण ऑडिट लॉग",
        "zh": "完整审计日志"
    },
    "th_run_id": {
        "en": "Run ID",
        "mr": "रन आयडी",
        "zh": "运行编号"
    },
    "th_timestamp": {
        "en": "Timestamp",
        "mr": "वेळ",
        "zh": "时间戳"
    },
    "th_algorithm": {
        "en": "Algorithm",
        "mr": "अल्गोरिदम",
        "zh": "算法"
    },
    "th_fairness": {
        "en": "Fairness",
        "mr": "समता",
        "zh": "公平指数"
    },
    "th_export": {
        "en": "Export",
        "mr": "निर्यात",
        "zh": "导出"
    },
    "empty_history_prompt": {
        "en": "No historical runs saved yet. Click \"Run All 3 Algorithms\" above to benchmark and save runs.",
        "mr": "अद्याप कोणतेही मागील रन जतन केलेले नाहीत. बेंचमार्क करण्यासाठी आणि जतन करण्यासाठी वरील \"सर्व ३ अल्गोरिदम चालवा\" वर क्लिक करा.",
        "zh": "暂无保存的历史运行记录。请点击上方的“运行全部3种算法”进行基准测试并保存。"
    },

    # Farm & Plot Form Labels
    "form_plot_id": {
        "en": "Plot ID",
        "mr": "भूखंड ओळख क्रमांक (Plot ID)",
        "zh": "地块编号 (Plot ID)"
    },
    "form_plot_id_hint": {
        "en": "Must be unique within farm",
        "mr": "शेतामध्ये अद्वितीय असणे आवश्यक आहे",
        "zh": "在当前农场内必须唯一"
    },
    "form_plot_name": {
        "en": "Plot Name",
        "mr": "भूखंडाचे नाव",
        "zh": "地块名称"
    },
    "form_area": {
        "en": "Area (Hectares)",
        "mr": "क्षेत्रफळ (हेक्टर)",
        "zh": "面积 (公顷)"
    },
    "form_crop_type": {
        "en": "Crop Type",
        "mr": "पिकाचा प्रकार",
        "zh": "作物类型"
    },
    "form_growth_stage": {
        "en": "Growth Stage",
        "mr": "वाढीची अवस्था",
        "zh": "生长阶段"
    },
    "form_crop_priority": {
        "en": "Crop Priority (1-5)",
        "mr": "पिकाचे प्राधान्य (१ ते ५)",
        "zh": "作物优先级 (1-5)"
    },
    "form_soil_type": {
        "en": "Soil Type",
        "mr": "मातीचा प्रकार",
        "zh": "土壤类型"
    },
    "form_infiltration_rate": {
        "en": "Infiltration Rate (mm/h)",
        "mr": "पाणी मुरण्याचा दर (मिमी/तास)",
        "zh": "入渗速率 (mm/h)"
    },
    "form_cost_per_liter": {
        "en": "Cost per Liter (₹/L)",
        "mr": "प्रति लिटर खर्च (₹/लिटर)",
        "zh": "每升成本 (₹/L)"
    },
    "form_current_moisture": {
        "en": "Current Soil Moisture (%)",
        "mr": "सध्याचा मातीचा ओलावा (%)",
        "zh": "当前土壤湿度 (%)"
    },
    "form_required_water": {
        "en": "Required Water (Liters)",
        "mr": "आवश्यक पाणी (लिटर)",
        "zh": "需水量 (升)"
    },
    "form_target_moisture": {
        "en": "Target Moisture (%)",
        "mr": "लक्ष्य ओलावा (%)",
        "zh": "目标湿度 (%)"
    },
    "form_remaining_demand": {
        "en": "Preprocessed Remaining Water Demand",
        "mr": "प्रक्रिया केलेली उर्वरित पाण्याची मागणी",
        "zh": "预处理剩余需水量"
    },

    # Validation Error Messages
    "err_correct_inputs": {
        "en": "Please correct the highlighted inputs below.",
        "mr": "कृपया खाली हायलाइट केलेल्या त्रुटी दुरुस्त करा.",
        "zh": "请更正下方高亮显示的输入错误。"
    },
    "err_plot_id_exists": {
        "en": "Plot ID already exists in this farm.",
        "mr": "या शेतात हा भूखंड ओळख क्रमांक आधीच अस्तित्वात आहे.",
        "zh": "该地块编号在此农场中已存在。"
    },
    "err_plot_id_suggest": {
        "en": "is already taken. Click here to use next available ID:",
        "mr": "आधीच वापरलेला आहे. पुढील उपलब्ध आयडी वापरण्यासाठी येथे क्लिक करा:",
        "zh": "已被占用。点击此处使用下一个可用编号："
    },

    # Notice and Info
    "telemetry_notice": {
        "en": "Agronomic Data Source Notice: CropFlow operates on manually entered or simulated farm scenarios. No real-time sensor streams or automated telemetry are claimed.",
        "mr": "कृषी माहिती स्रोत सूचना: क्रॉपफ्लो मॅन्युअली प्रविष्ट केलेल्या किंवा सिम्युलेटेड शेताच्या डेटावर कार्य करते. रिअल-टाइम सेन्सरचा दावा केला जात नाही.",
        "zh": "农学数据源提示：CropFlow 运行于手动录入或模拟的农田场景。不假定存在实时传感器或自动物联网遥测。"
    },
    "farm_summary": {
        "en": "Farm Summary",
        "mr": "शेत सारांश",
        "zh": "农场概览"
    },
    "drought_severity": {
        "en": "Drought Severity",
        "mr": "दुष्काळाची तीव्रता",
        "zh": "干旱等级"
    },
    "time_window": {
        "en": "Irrigation Time Window",
        "mr": "सिंचन वेळ खिडकी",
        "zh": "灌溉时间窗口"
    },
    "economics": {
        "en": "Economics (₹)",
        "mr": "आर्थिक दर (₹)",
        "zh": "经济核算 (₹)"
    },
    "pump_capacity": {
        "en": "Pump Capacity",
        "mr": "पंप क्षमता",
        "zh": "水泵流量"
    },
    "schedule_title": {
        "en": "Actionable Hourly Irrigation Pump Schedule",
        "mr": "तासनिहाय सिंचन पंप वेळापत्रक",
        "zh": "可执行逐小时灌溉水泵运行调度表"
    },
    "sim_emergency": {
        "en": "10% Emergency",
        "mr": "१०% आपत्कालीन",
        "zh": "10% 紧急限水"
    },
    "sim_normal": {
        "en": "100% Normal",
        "mr": "१००% सामान्य",
        "zh": "100% 正常供水"
    },
    "supply": {
        "en": "Supply",
        "mr": "पाणी पुरवठा",
        "zh": "供水量"
    },
    "strategy_hybrid": {
        "en": "Hybrid",
        "mr": "हायब्रिड",
        "zh": "混合策略"
    },
    "strategy_dp": {
        "en": "DP",
        "mr": "डीपी (DP)",
        "zh": "动态规划"
    },
    "strategy_greedy": {
        "en": "Greedy",
        "mr": "ग्रीडी",
        "zh": "贪心"
    },
    "tab_cost": {
        "en": "Cost (₹)",
        "mr": "खर्च (₹)",
        "zh": "成本 (₹)"
    },
    "tab_runtime": {
        "en": "Runtime",
        "mr": "वेळ",
        "zh": "耗时"
    },
    "tab_yield": {
        "en": "Yield",
        "mr": "उत्पादन",
        "zh": "产量"
    },
    "supply_range": {
        "en": "10% → 100% Supply",
        "mr": "१०% → १००% पाणी पुरवठा",
        "zh": "10% → 100% 供水"
    },
    "soil_moisture_title": {
        "en": "Soil Moisture vs Wilting & Field Capacity",
        "mr": "मातीचा ओलावा विरुद्ध सुकणे व धारण क्षमता",
        "zh": "土壤湿度对比凋萎点与田间持水量"
    },
    "agronomic_limits": {
        "en": "Agronomic Limits",
        "mr": "कृषी मर्यादा",
        "zh": "农学阈值"
    },
    "soil_moisture_desc": {
        "en": "Current soil moisture deficit dictates baseline survival prioritization.",
        "mr": "सध्याची मातीतील ओलाव्याची तूट जगण्याच्या निकषांवर सिंचन प्राधान्य ठरवते.",
        "zh": "当前土壤含水量亏缺决定作物的保底生存优先级。"
    },
    "plot_eval_prefix": {
        "en": "Plot-by-plot evaluation under active",
        "mr": "सक्रिय धोरणांतर्गत प्रत्येक भूखंडाचे मूल्यांकन:",
        "zh": "当前策略下各地块评估："
    },
    "total_budget": {
        "en": "Total Budget",
        "mr": "एकूण बजेट",
        "zh": "总预算"
    },
    "btn_edit_plots": {
        "en": "Edit Plots",
        "mr": "भूखंड संपादित करा",
        "zh": "编辑地块"
    },
    "th_avail_water": {
        "en": "Available Water",
        "mr": "उपलब्ध पाणी",
        "zh": "可用水量"
    },
    "th_allocated": {
        "en": "Allocated",
        "mr": "वाटप",
        "zh": "已分配"
    },
    "th_irrigation_cost": {
        "en": "Irrigation Cost",
        "mr": "सिंचन खर्च",
        "zh": "灌溉成本"
    },
    "th_net_return": {
        "en": "Net Return",
        "mr": "निव्वळ परतावा",
        "zh": "净收益"
    },
    "no_plots_configured": {
        "en": "No Farm Plots Configured",
        "mr": "कोणतेही भूखंड कॉन्फिगर केलेले नाहीत",
        "zh": "未配置农田地块"
    },
    "no_plots_desc": {
        "en": "To begin optimal irrigation scheduling, register your agricultural plots with soil moisture levels, crop sensitivities, and water demand.",
        "mr": "इष्टतम सिंचन वेळापत्रक सुरू करण्यासाठी, मातीतील ओलावा, पीक संवेदनशीलता आणि पाण्याची मागणी यासह तुमचे भूखंड नोंदवा.",
        "zh": "要开始最优灌溉调度，请配置带有土壤含水量、作物敏感度和需水量的农田地块。"
    },
    "results_title": {
        "en": "Optimization Results & Comparisons",
        "mr": "ऑप्टिमायझेशन निकाल व तुलना",
        "zh": "优化结果与方案对比"
    },
    "history_audit_title": {
        "en": "Historical Optimization Runs Audit",
        "mr": "मागील ऑप्टिमायझेशन ऑडिट नोंदी",
        "zh": "历次优化运行审计记录"
    },
    "farms_title": {
        "en": "Farm & Plot Management",
        "mr": "शेत आणि भूखंड व्यवस्थापन",
        "zh": "农场与地块管理"
    },
    "plot_count": {
        "en": "Plots",
        "mr": "भूखंड",
        "zh": "地块数"
    },
    "total_demand": {
        "en": "Total Demand",
        "mr": "एकूण मागणी",
        "zh": "总需水"
    },
    "water_budget": {
        "en": "Water Budget",
        "mr": "पाणी बजेट",
        "zh": "水预算"
    },
    "manage_plots": {
        "en": "Manage Plots",
        "mr": "भूखंड व्यवस्थापित करा",
        "zh": "管理地块"
    },
    "actions": {
        "en": "Actions",
        "mr": "क्रिया",
        "zh": "操作"
    },
    "th_crop": {
        "en": "Crop",
        "mr": "पीक",
        "zh": "作物"
    },
    "th_area_ha": {
        "en": "Area (ha)",
        "mr": "क्षेत्रफळ (हेक्टर)",
        "zh": "面积 (公顷)"
    },
    "th_priority": {
        "en": "Priority",
        "mr": "प्राधान्य",
        "zh": "优先级"
    },
    "th_current_moisture": {
        "en": "Current Moisture",
        "mr": "सध्याचा ओलावा",
        "zh": "当前湿度"
    },
    "th_target_moisture": {
        "en": "Target Moisture",
        "mr": "लक्ष्य ओलावा",
        "zh": "目标湿度"
    },
    "th_status": {
        "en": "Status",
        "mr": "स्थिती",
        "zh": "状态"
    },
    "farm_data_collection": {
        "en": "Farm Data Collection & Preprocessing",
        "mr": "शेत माहिती संकलन आणि पूर्वप्रक्रिया",
        "zh": "农场数据采集与预处理"
    },
    "manual_simulated_badge": {
        "en": "Manual / Simulated Inputs",
        "mr": "मॅन्युअल / सिम्युलेटेड इनपुट",
        "zh": "手动 / 模拟录入"
    },
    "farm_data_desc": {
        "en": "Collects plot agronomic metrics, calculates remaining water demand, and enforces non-negative & uniqueness constraints.",
        "mr": "भूखंडांचे कृषी मापदंड संकलित करते, उर्वरित पाण्याची मागणी मोजते आणि अचूकतेचे नियम लागू करते.",
        "zh": "采集地块农学指标，计算剩余需水量，并强制执行非负与唯一性约束。"
    },
    "farm_plots": {
        "en": "Farm Plots",
        "mr": "शेतातील भूखंड",
        "zh": "农本地块"
    },
    "soil": {
        "en": "Soil",
        "mr": "माती",
        "zh": "土壤"
    },
    "required_water": {
        "en": "Required Water",
        "mr": "आवश्यक पाणी",
        "zh": "需水量"
    },
    "remaining_water_demand": {
        "en": "Remaining Water Demand",
        "mr": "उर्वरित पाण्याची मागणी",
        "zh": "剩余需水量"
    },
    "assumptions_title": {
        "en": "Documented Assumptions for Remaining Water Demand",
        "mr": "उर्वरित पाणी मागणीसाठी नोंदवलेली गृहितके",
        "zh": "剩余需水量的记录假设"
    },
    "create_farm_title": {
        "en": "Create Farm Profile",
        "mr": "नवीन शेत प्रोफाइल तयार करा",
        "zh": "创建农场档案"
    },
    "add_plot_title": {
        "en": "Add Farm Plot (Data Collection)",
        "mr": "शेताचा भूखंड जोडा (माहिती संकलन)",
        "zh": "添加农田地块 (数据采集)"
    },
    "label_farm_name": {
        "en": "Farm Name",
        "mr": "शेताचे नाव",
        "zh": "农场名称"
    },
    "label_farm_location": {
        "en": "Location / Basin",
        "mr": "स्थान / पाणलोट क्षेत्र",
        "zh": "地理位置 / 流域"
    },
    "label_avail_water_liters": {
        "en": "Total Available Water (Liters)",
        "mr": "एकूण उपलब्ध पाणी (लिटर)",
        "zh": "总可用水量 (升)"
    },
    "label_irrigation_start": {
        "en": "Irrigation Start (Time)",
        "mr": "सिंचन सुरू होण्याची वेळ",
        "zh": "灌溉开始时间"
    },
    "label_irrigation_end": {
        "en": "Irrigation End (Time)",
        "mr": "सिंचन संपण्याची वेळ",
        "zh": "灌溉结束时间"
    },
    "label_pump_capacity": {
        "en": "Pump Flow Capacity (m³/h)",
        "mr": "पंप प्रवाह क्षमता (m³/तास)",
        "zh": "水泵流量 (m³/h)"
    },
    "label_window_duration": {
        "en": "Window Duration (Hours)",
        "mr": "कालावधी (तास)",
        "zh": "时间窗口长度 (小时)"
    },
    "label_total_farm_area": {
        "en": "Total Farm Area",
        "mr": "शेताचे एकूण क्षेत्रफळ",
        "zh": "农场总面积"
    },
    "energy": {
        "en": "Energy",
        "mr": "ऊर्जा",
        "zh": "电费"
    },
    "labor": {
        "en": "Labor",
        "mr": "मजुरी",
        "zh": "人工"
    },
    "status_deficit_active": {
        "en": "Status: Moisture Deficit Active",
        "mr": "स्थिती: ओलावा तूट सक्रिय",
        "zh": "状态：水分亏缺有效"
    },
    "health_title": {
        "en": "System Health & Engine Architecture",
        "mr": "प्रणाली आरोग्य आणि इंजिन रचना",
        "zh": "系统健康状况与引擎架构"
    },
    "health_subtitle": {
        "en": "Real-time service diagnostics, database connectivity, and optimization algorithm specifications",
        "mr": "रिअल-टाइम सेवा निदान, डेटाबेस कनेक्टिव्हिटी आणि ऑप्टिमायझेशन अल्गोरिदम तपशील",
        "zh": "实时服务诊断、数据库连接性与优化算法规范"
    },
    "sys_status_healthy": {
        "en": "System Status: Healthy",
        "mr": "प्रणाली स्थिती: उत्तम (Healthy)",
        "zh": "系统状态：正常运行"
    },
    "db_connected": {
        "en": "SQLite Database Connected",
        "mr": "एसक्यूलाइट डेटाबेस जोडलेला आहे",
        "zh": "SQLite 数据库已连接"
    },
    "farms_count_label": {
        "en": "Registered Farms",
        "mr": "नोंदणीकृत शेते",
        "zh": "已注册农场"
    },
    "plots_count_label": {
        "en": "Managed Plots",
        "mr": "व्यवस्थापित भूखंड",
        "zh": "受管地块"
    },
    "algorithms_spec": {
        "en": "Algorithm Suite Complexity & Mathematical Roles",
        "mr": "अल्गोरिदम संच जटिलता आणि गणितीय भूमिका",
        "zh": "算法套件复杂度与数学定位"
    },
    "raw_json_api": {
        "en": "View Raw JSON API",
        "mr": "कच्चा JSON API पहा",
        "zh": "查看原始 JSON API"
    },
    "role_greedy": {
        "en": "Rapid urgent triage based on crop sensitivity and moisture deficit",
        "mr": "पीक संवेदनशीलता आणि ओलावा तुटीवर आधारित जलद आणीबाणी ट्रायज",
        "zh": "基于作物敏感度与水分亏缺的快速紧急分流"
    },
    "role_dp": {
        "en": "Global yield-payoff optimization across discretized resource levels",
        "mr": "विभक्त संसाधन पातळ्यांवर जागतिक उत्पन्न-परतावा इष्टतमीकरण",
        "zh": "离散资源层级下的全局产量回报最大化优化"
    },
    "role_hybrid": {
        "en": "Proposed balanced architecture: survival baseline anchor with DP residual refinement",
        "mr": "प्रस्तावित संतुलित रचना: जगण्याचा आधार स्तंभ + डीपी उर्वरित सुधारणा",
        "zh": "推荐均衡架构：保底存活锚点 + 动态规划余量精细化寻优"
    },
    "complexity_label": {
        "en": "Time Complexity",
        "mr": "वेळ जटिलता (Time Complexity)",
        "zh": "时间复杂度"
    },
    "math_role_label": {
        "en": "Mathematical Role",
        "mr": "गणितीय भूमिका (Mathematical Role)",
        "zh": "数学定位与职责"
    }
}


def get_translation(key: str, lang: Optional[str] = "en") -> str:
    """Retrieve translated string for key, falling back to English if missing."""
    target_lang = lang if lang in ("en", "mr", "zh") else "en"
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    return entry.get(target_lang) or entry.get("en", key)


def get_all_translations(lang: Optional[str] = "en") -> Dict[str, str]:
    """Retrieve all translated strings for the selected language."""
    target_lang = lang if lang in ("en", "mr", "zh") else "en"
    return {
        key: values.get(target_lang, values.get("en", key))
        for key, values in TRANSLATIONS.items()
    }
