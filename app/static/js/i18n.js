/**
 * CropFlow Multilingual (i18n) Client-Side Controller
 * Supports English (en), Marathi (mr), and Chinese (zh).
 */

const CROPFLOW_LANG_KEY = "cropflow_lang";

const I18N_DICTIONARY = {
    "en": {
        "app_title": "CropFlow - Optimal Irrigation Scheduling",
        "brand_name": "CropFlow",
        "brand_tagline": "Irrigation AI & Water Optimization",
        "nav_operations": "OPERATIONS",
        "nav_architecture": "ARCHITECTURE",
        "nav_dashboard": "Dashboard",
        "nav_farms": "Farms & Plots",
        "nav_results": "Results & Audits",
        "nav_overview": "System Overview",
        "nav_health": "Health Check",
        "btn_run_all": "Run All 3 Algorithms",
        "btn_new_farm": "New Farm",
        "btn_add_plot": "Add Plot",
        "btn_add_another_plot": "Add Another Plot",
        "btn_reset_farm": "Reset Sample Farm",
        "btn_save_plot": "Save Plot",
        "btn_save_farm": "Save Farm",
        "btn_cancel": "Cancel",
        "btn_auto_id": "Auto-generate Next ID",
        "kpi_available_water": "Available Water / Total Demand",
        "kpi_allocated_water": "Water Allocated & Unmet Demand",
        "kpi_water_utilization": "Water Utilization Rate",
        "kpi_estimated_cost": "Estimated Irrigation Cost",
        "kpi_net_return": "Net Economic Return",
        "kpi_execution_times": "Algorithm Execution Times",
        "sim_title": "Interactive Drought Scenario Simulator",
        "sim_desc": "Slide to simulate drought curtailment and dynamically re-run water optimization across all plots.",
        "form_plot_id": "Plot ID",
        "form_plot_id_hint": "Must be unique within farm",
        "form_plot_name": "Plot Name",
        "form_area": "Area (Hectares)",
        "form_crop_type": "Crop Type",
        "form_growth_stage": "Growth Stage",
        "form_crop_priority": "Crop Priority (1-5)",
        "form_soil_type": "Soil Type",
        "form_infiltration_rate": "Infiltration Rate (mm/h)",
        "form_cost_per_liter": "Cost per Liter (₹/L)",
        "form_current_moisture": "Current Soil Moisture (%)",
        "form_required_water": "Required Water (Liters)",
        "form_target_moisture": "Target Moisture (%)",
        "form_remaining_demand": "Preprocessed Remaining Water Demand",
        "err_correct_inputs": "Please correct the highlighted inputs below.",
        "err_plot_id_exists": "Plot ID already exists in this farm.",
        "err_plot_id_suggest": "is already taken. Click here to use next available ID:"
    },
    "mr": {
        "app_title": "क्रॉपफ्लो - इष्टतम सिंचन वेळापत्रक",
        "brand_name": "क्रॉपफ्लो",
        "brand_tagline": "सिंचन एआय आणि पाणी नियोजन",
        "nav_operations": "कामकाज",
        "nav_architecture": "रचना व माहिती",
        "nav_dashboard": "डॅशबोर्ड (नियंत्रण कक्ष)",
        "nav_farms": "शेत आणि भूखंड",
        "nav_results": "निकाल आणि ऑडिट",
        "nav_overview": "प्रणाली आढावा",
        "nav_health": "आरोग्य तपासणी",
        "btn_run_all": "सर्व ३ अल्गोरिदम चालवा",
        "btn_new_farm": "नवीन शेत",
        "btn_add_plot": "भूखंड जोडा",
        "btn_add_another_plot": "आणखी भूखंड जोडा",
        "btn_reset_farm": "नमुना शेत रीसेट करा",
        "btn_save_plot": "भूखंड जतन करा",
        "btn_save_farm": "शेत जतन करा",
        "btn_cancel": "रद्द करा",
        "btn_auto_id": "पुढील आयडी आपोआप तयार करा",
        "kpi_available_water": "उपलब्ध पाणी / एकूण मागणी",
        "kpi_allocated_water": "वाटप केलेले पाणी व अपूर्ण मागणी",
        "kpi_water_utilization": "पाणी वापर कार्यक्षमता दर",
        "kpi_estimated_cost": "अंदाजे सिंचन खर्च",
        "kpi_net_return": "निव्वळ आर्थिक परतावा",
        "kpi_execution_times": "अल्गोरिदम अंमलबजावणी वेळ",
        "sim_title": "परस्परसंवादी दुष्काळ परिस्थिती सिम्युलेटर",
        "sim_desc": "दुष्काळाची तीव्रता बदलण्यासाठी स्लाइडर हलवा आणि सर्व भूखंडांसाठी सिंचनाचे त्वरित पुनर्गणन करा.",
        "form_plot_id": "भूखंड ओळख क्रमांक (Plot ID)",
        "form_plot_id_hint": "शेतामध्ये अद्वितीय असणे आवश्यक आहे",
        "form_plot_name": "भूखंडाचे नाव",
        "form_area": "क्षेत्रफळ (हेक्टर)",
        "form_crop_type": "पिकाचा प्रकार",
        "form_growth_stage": "वाढीची अवस्था",
        "form_crop_priority": "पिकाचे प्राधान्य (१ ते ५)",
        "form_soil_type": "मातीचा प्रकार",
        "form_infiltration_rate": "पाणी मुरण्याचा दर (मिमी/तास)",
        "form_cost_per_liter": "प्रति लिटर खर्च (₹/लिटर)",
        "form_current_moisture": "सध्याचा मातीचा ओलावा (%)",
        "form_required_water": "आवश्यक पाणी (लिटर)",
        "form_target_moisture": "लक्ष्य ओलावा (%)",
        "form_remaining_demand": "प्रक्रिया केलेली उर्वरित पाण्याची मागणी",
        "err_correct_inputs": "कृपया खालील हायलाइट केलेल्या त्रुटी दुरुस्त करा.",
        "err_plot_id_exists": "या शेतात हा भूखंड ओळख क्रमांक आधीच अस्तित्वात आहे.",
        "err_plot_id_suggest": "आधीच वापरलेला आहे. पुढील उपलब्ध आयडी वापरण्यासाठी येथे क्लिक करा:"
    },
    "zh": {
        "app_title": "CropFlow - 最优灌溉调度系统",
        "brand_name": "CropFlow",
        "brand_tagline": "智能灌溉与水资源优化",
        "nav_operations": "核心操作",
        "nav_architecture": "系统架构",
        "nav_dashboard": "仪表板",
        "nav_farms": "农场与地块",
        "nav_results": "结果与审计",
        "nav_overview": "系统概览",
        "nav_health": "健康检查",
        "btn_run_all": "运行全部3种算法",
        "btn_new_farm": "新建农场",
        "btn_add_plot": "添加地块",
        "btn_add_another_plot": "添加另一个地块",
        "btn_reset_farm": "重置示例农场",
        "btn_save_plot": "保存地块",
        "btn_save_farm": "保存农场",
        "btn_cancel": "取消",
        "btn_auto_id": "自动生成下一个编号",
        "kpi_available_water": "可用水量 / 总需水量",
        "kpi_allocated_water": "已分配水量与未满足需求",
        "kpi_water_utilization": "水资源利用率",
        "kpi_estimated_cost": "预计灌溉成本",
        "kpi_net_return": "净经济收益",
        "kpi_execution_times": "算法运行耗时",
        "sim_title": "交互式干旱情景模拟器",
        "sim_desc": "拖动滑块模拟干旱限水情景，实时重新计算各地块的水资源分配。",
        "form_plot_id": "地块编号 (Plot ID)",
        "form_plot_id_hint": "在当前农场内必须唯一",
        "form_plot_name": "地块名称",
        "form_area": "面积 (公顷)",
        "form_crop_type": "作物类型",
        "form_growth_stage": "生长阶段",
        "form_crop_priority": "作物优先级 (1-5)",
        "form_soil_type": "土壤类型",
        "form_infiltration_rate": "入渗速率 (mm/h)",
        "form_cost_per_liter": "每升成本 (₹/L)",
        "form_current_moisture": "当前土壤湿度 (%)",
        "form_required_water": "需水量 (升)",
        "form_target_moisture": "目标湿度 (%)",
        "form_remaining_demand": "预处理剩余需水量",
        "err_correct_inputs": "请更正下方高亮显示的输入错误。",
        "err_plot_id_exists": "该地块编号在此农场中已存在。",
        "err_plot_id_suggest": "已被占用。点击此处使用下一个可用编号："
    }
};

function getCurrentLanguage() {
    // Check cookie first, then localStorage, then default to en
    const match = document.cookie.match(new RegExp('(^| )cropflow_lang=([^;]+)'));
    if (match) return match[2];
    const stored = localStorage.getItem(CROPFLOW_LANG_KEY);
    if (stored) return stored;
    return "en";
}

function setLanguage(lang) {
    if (!["en", "mr", "zh"].includes(lang)) lang = "en";
    localStorage.setItem(CROPFLOW_LANG_KEY, lang);
    document.cookie = `cropflow_lang=${lang};path=/;max-age=${30 * 24 * 3600}`;
    window.location.reload();
}

function t(key) {
    const lang = getCurrentLanguage();
    if (I18N_DICTIONARY[lang] && I18N_DICTIONARY[lang][key]) {
        return I18N_DICTIONARY[lang][key];
    }
    if (I18N_DICTIONARY["en"] && I18N_DICTIONARY["en"][key]) {
        return I18N_DICTIONARY["en"][key];
    }
    return key;
}

window.CropFlowI18n = {
    getLang: getCurrentLanguage,
    setLang: setLanguage,
    t: t
};
