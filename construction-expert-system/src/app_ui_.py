
from pathlib import Path
from typing import Dict, Optional
import contextlib
# =========================
# Data & Math
# =========================
import pandas as pd

# =========================
# Streamlit
# =========================
import streamlit as st

# =========================
# Project imports
# =========================
from expert_system import (
    load_all_datasets,
    # FOUNDATIONS
    find_best_foundation_rule_safe,
    select_concrete_for_rule,
    select_rebar_for_rule,
    select_foundation_waterproofing,
    # COLUMNS
    choose_best_column_rule,
    # BEAMS
    choose_best_beam_rule,
)

# =========================
# 🌍 Language System (Stable)
# =========================

def init_lang():
    if "lang" not in st.session_state:
        st.session_state["lang"] = "ar"   # default

def tr(ar: str, en: str) -> str:
    return ar if st.session_state.get("lang", "ar") == "ar" else en

def language_switcher_sidebar():
    init_lang()

    st.sidebar.markdown("### 🌐 " + tr("اللغة", "Language"))

    # ✅ radio هو الأفضل لأنه يحفظ الحالة تلقائياً
    lang = st.sidebar.radio(
        label=tr("اختر اللغة", "Choose language"),
        options=["ar", "en"],
        index=0 if st.session_state["lang"] == "ar" else 1,
        format_func=lambda x: "🇮🇶 العربية" if x == "ar" else "🇬🇧 English",
        key="lang_radio",   # key مختلف عن "lang" حتى ما يصير تعارض
    )

    # ✅ تحديث اللغة فقط إذا تغيّرت
    if lang != st.session_state["lang"]:
        st.session_state["lang"] = lang
        st.rerun()

# -------------------------------------------------
#  مسار ملف شعار الجامعة
#  تأكد أن الصورة موجودة في:  src/images/university_logo.jpg
# -------------------------------------------------
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
import streamlit as st

# ==========================
# Paths (مهم للنشر)
# ==========================
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent          # = .../construction-expert-system/src
PROJECT_DIR = BASE_DIR.parent                       # = .../construction-expert-system
DATASET_DIR = PROJECT_DIR / "dataset"               # = .../construction-expert-system/dataset

# Images داخل src/images ✅
IMAGES_DIR = BASE_DIR / "images"
UNIVERSITY_LOGO_PATH = IMAGES_DIR / "university_logo.jpg"

# ملف المواد الموحد (ضعه داخل dataset/ حتى يشتغل على الكلاود)
MASTER_MATERIALS_PATH = DATASET_DIR / "materials_master.xlsx"


@st.cache_data
def load_materials_master() -> Optional[pd.DataFrame]:
    if MASTER_MATERIALS_PATH.exists():
        return pd.read_excel(MASTER_MATERIALS_PATH)
    return None


# ==========================
# كاش تحميل الداتا
# ==========================
@st.cache_data
def get_datasets() -> Dict[str, pd.DataFrame]:
    """يستدعي load_all_datasets مرة واحدة فقط ويخزن النتيجة في الكاش."""
    return load_all_datasets()
# ==========================
# الهيدر (اسم الجامعة والقسم + الشعار)
# ==========================

def render_header():
    import streamlit as st

    # ✅ Title inside a centered rectangular card (NO UNIVERSITY LOGO)
    st.markdown("""
      <div class="main-title-card">
        <div class="t1">Construction Material Expert System</div>
        <div class="t2">نظام خبير لاختيار المواد الإنشائية</div>
      </div>
    """, unsafe_allow_html=True)

    # ✅ Gold separator (optional)
    st.markdown("---")


# ==========================
# دالة مساعدة لاختيار جدول من القاموس
# ==========================
def pick_df(datasets: Dict[str, pd.DataFrame], keys) -> Optional[pd.DataFrame]:
    """
    يحاول يرجع أول DataFrame موجود من القائمة keys.
    """
    for k in keys:
        if k in datasets:
            df = datasets[k]
            if df is not None and isinstance(df, pd.DataFrame):
                return df
    return None

def pick_best_rule_generic(df: pd.DataFrame, criteria: dict) -> Optional[pd.Series]:
    """
    فلترة بسيطة لجداول القواعد:
    - نطبّق الفلتر فقط إذا العمود موجود في الشيت
    - وإذا الفلتر خلا النتائج صفر، نتجاهله (حتى لا تضيع كل الداتا)
    - ترجع أول صف بعد الفلترة كأفضل قاعدة
    """
    if df is None or df.empty:
        return None

    subset = df.copy()

    for col, val in criteria.items():
        if val is None:
            continue
        if col not in subset.columns:
            continue

        mask = subset[col].astype(str).str.strip() == str(val).strip()
        if mask.any():
            subset = subset[mask]

    if subset.empty:
        return None

    return subset.iloc[0]

# ==========================================
#   FOUNDATION UI (واجهة الأساسات)
# ==========================================
def run_foundation_ui(project_type: str, structural_system: str, datasets: Dict[str, pd.DataFrame]):
    st.subheader("⚙ إعدادات الأساسات (Foundation Settings)")

    col1, col2 = st.columns(2)

    with col1:
        soil = st.selectbox(
            "Soil Type (نوع التربة)",
            ["Clay", "Sand", "Gravel", "Rock", "Mixed_Soil", "Soft_Clay"],
            index=0,
            key="f_soil",
        )

        gwt = st.selectbox(
            "Groundwater Level (منسوب المياه الجوفية)",
            ["Low", "Medium", "High", "Very_High"],
            index=0,
            key="f_gwt",
        )

        seismic = st.selectbox(
            "Seismic Zone Level (مستوى منطقة الزلازل)",
            ["Low", "Moderate", "High", "Very_High"],
            index=1,
            key="f_seismic",
        )

    with col2:
        excavation = st.selectbox(
            "Excavation Risk Level (خطورة الحفر)",
            ["Low", "Medium", "High", "Very_High"],
            index=1,
            key="f_exc",
        )

        aggressiveness = st.selectbox(
            "Soil Aggressiveness (عدوانية التربة كيميائياً)",
            ["Normal", "Medium_Sulfate", "High_Sulfate", "Marine_Environment"],
            index=0,
            key="f_aggr",
        )

        min_fc = st.number_input(
            "Minimum concrete strength f'c (MPa) [اتركها صفر لاستخدام قيمة الكود]",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="f_min_fc",
        )

    st.markdown("---")

    if not st.button("📐 تشغيل تصميم الأساسات", key="btn_run_foundation"):
        return

    # === جلب الداتا ===
    found_df = pick_df(datasets, ["foundation_rules_df", "foundations_rules"])
    conc_df = pick_df(datasets, ["concrete_df", "concrete_materials"])
    rebar_df = pick_df(datasets, ["rebar_df", "rebar_materials"])
    wp_df = pick_df(datasets, ["waterproofing_df", "waterproofing_materials"])

    if found_df is None or found_df.empty:
        st.error("⚠ لا توجد قواعد تصميم للأساسات (foundation_rules).")
        return

    best_rule = find_best_foundation_rule_safe(
        found_df,
        project_type,
        structural_system,
        soil,
        gwt,
        seismic,
        excavation,
        aggressiveness,
        min_fc,
    )

    if best_rule is None:
        st.error("❌ لم يتم العثور على قرار هندسي مناسب للأساسات.")
        return

    # ========= عرض القرار الهندسي =========
    st.subheader("✅ القرار الهندسي للأساسات (Engineering Decision)")

    decision_df = best_rule.to_frame(name="Value (القيمة)").reset_index()
    decision_df.columns = ["Parameter (المعيار)", "Value (القيمة)"]
    st.dataframe(decision_df, use_container_width=True)

    # ========= الخرسانة =========
    st.subheader("🧱 أفضل خلطات الخرسانة للأساسات (Top Concrete Mixes)")

    if conc_df is not None and not conc_df.empty:
        conc_sel = select_concrete_for_rule(conc_df, best_rule, top_n=3)
    else:
        conc_sel = None

    if conc_sel is not None and not conc_sel.empty:
        cols_to_show = []
        for c in [
            "Mix_Name",
            "Material_ID",
            "Strength_MPa",
            "Cement_Type",
            "Exposure_Class",
            "Cost_Index",
            "concrete_score",
        ]:
            if c in conc_sel.columns:
                cols_to_show.append(c)
        st.dataframe(conc_sel[cols_to_show], use_container_width=True)
    else:
        st.warning("لا توجد خلطات خرسانة مطابقة.")

    # ========= حديد التسليح =========
    st.subheader("🔩 أفضل حديد تسليح للأساسات (Top Rebar Options)")

    if rebar_df is not None and not rebar_df.empty:
        rebar_sel = select_rebar_for_rule(rebar_df, best_rule, top_n=3)
    else:
        rebar_sel = None

    if rebar_sel is not None and not rebar_sel.empty:
        cols_to_show = []
        for c in [
            "Rebar_ID",
            "Steel_Grade",
            "Yield_Strength_MPa",
            "Coating_Type",
            "Corrosion_Resistance_Level",
            "Seismic_Suitability",
            "Best_Use_Case",
            "Cost_Index",
            "rebar_score",
        ]:
            if c in rebar_sel.columns:
                cols_to_show.append(c)
        st.dataframe(rebar_sel[cols_to_show], use_container_width=True)
    else:
        st.warning("لا يوجد حديد تسليح مطابق.")

    # ========= العزل =========
    st.subheader("💧 أفضل أنظمة عزل للأساسات (Waterproofing Systems)")

    if wp_df is not None and not wp_df.empty:
        wp_sel = select_foundation_waterproofing(best_rule, wp_df, top_n=3)
    else:
        wp_sel = None

    if wp_sel is not None and not wp_sel.empty:
        cols_to_show = []
        for c in [
            "Material_ID",
            "System_Category",
            "Product_Name",
            "Best_Use_Case",
            "final_score",
        ]:
            if c in wp_sel.columns:
                cols_to_show.append(c)
        st.dataframe(wp_sel[cols_to_show], use_container_width=True)
    else:
        st.warning("لا توجد مواد عزل مطابقة.")

# ============================================
#  COLUMN UI (واجهة الأعمدة)
# ============================================
def run_column_ui(project_type: str, structural_system: str, datasets: dict):
    st.subheader("⚙ إعدادات الأعمدة (Column Settings)")

    col1, col2 = st.columns(2)

    # -------- مدخلات الأعمدة من الواجهة --------
    with col1:
        height_class = st.selectbox(
            "Building Height Class (تصنيف ارتفاع المبنى)",
            ["Low_Rise", "Medium_Rise", "High_Rise"],
            index=0,
            key="c_height",
        )

        load_level = st.selectbox(
            "Column Load Level (مستوى حمل العمود)",
            ["Light", "Medium", "Heavy"],
            index=1,
            key="c_load",
        )

        col_position = st.selectbox(
            "Column Position (موضع العمود)",
            ["Interior", "Edge", "Corner"],
            index=0,
            key="c_pos",
        )

    with col2:
        seismic_level = st.selectbox(
            "Seismic Zone Level (مستوى منطقة الزلازل)",
            ["Low", "Moderate", "High", "Very_High"],
            index=1,
            key="c_seismic",
        )

        exposure_class = st.selectbox(
            "Exposure Class (درجة التعرض البيئي)",
            ["XC1", "XC2", "XC3", "XC4"],
            index=1,
            key="c_exposure",
        )

        min_fc = st.number_input(
            "Minimum f'c (MPa) [اتركه صفر لقيمة الكود] "
            "(أدنى مقاومة خرسانة مطلوبة)",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="c_min_fc",
        )

    st.markdown("---")

    # زر التشغيل
    if not st.button("📐 تشغيل تصميم الأعمدة", key="run_column_btn"):
        return

    # لو النظام معدني → لا خرسانة ولا حديد، فقط توجيه
    if structural_system == "Steel_Frame":
        st.info("🧱 النظام الإنشائي معدني (Steel Frame) → الأعمدة تكون مقاطع فولاذية، "
                "وليست خرسانية مسلّحة.")
        st.markdown(
            """
            *📐 ملاحظات تصميمية للأعمدة الفولاذية:*

            - يتم اختيار المقطع من جداول AISC Shapes (W, H, I, Box ...)
            - التصميم حسب *AISC 360*
            - يعتمد على:
              - القوى المحورية والعزوم (من التحليل الإنشائي)
              - نسبة النحافة (Slenderness Ratio)
              - طول الانبعاج (Buckling Length)
              - متطلبات الزلازل (Seismic Detailing)
            """)
        return

    # -------- قراءة الداتا من القاموس (باستخدام pick_df) --------
    col_df   = pick_df(datasets, ["column_rules_df", "columns_rules"])
    conc_df  = pick_df(datasets, ["concrete_df", "concrete_materials"])
    rebar_df = pick_df(datasets, ["rebar_df", "rebar_materials"])

    if col_df is None or col_df.empty:
        st.error("❌ لا توجد قواعد تصميم للأعمدة (columns_rules).")
        return

    # -------- اختيار أفضل قاعدة تصميم للأعمدة --------
    from expert_system import (
        choose_best_column_rule,
        select_concrete_for_rule,
        select_rebar_for_rule,
    )

    crit = {
        "Project_Type":       project_type,
        "Structural_System":  structural_system,
        "Height_Class":       height_class,
        "Load_Level":         load_level,
        "Column_Position":    col_position,
        "Seismic_Zone_Level": seismic_level,
        "Exposure_Class":     exposure_class,
    }
    if min_fc > 0:
        crit["Min_Concrete_Strength_MPa"] = float(min_fc)

    best_rule = choose_best_column_rule(col_df, crit)

    if best_rule is None:
        st.error("❌ لم يتم العثور على قرار هندسي مناسب للأعمدة مع هذه المدخلات.")
        return

    # -------- عرض القرار الهندسي في جدول --------
    st.subheader("✅ القرار الهندسي للأعمدة (Column Engineering Decision)")

    decision_df = best_rule.to_frame(name="Value").reset_index()
    decision_df.columns = ["Parameter (المعيار)", "Value (القيمة)"]
    st.dataframe(decision_df, use_container_width=True)

    # -------- أفضل خلطات خرسانة للأعمدة --------
    st.subheader("🧱 أفضل خلطات الخرسانة للأعمدة (Top Concrete Mixes)")

    if conc_df is not None and not conc_df.empty:
        conc_sel = select_concrete_for_rule(conc_df, best_rule, top_n=3)
        if conc_sel is not None and not conc_sel.empty:
            conc_view = conc_sel[[
                "Mix_Name",
                "Material_ID",
                "Strength_MPa",
                "Cement_Type",
                "Exposure_Class",
                "Cost_Index",
            ]].copy()
            st.dataframe(conc_view, use_container_width=True)
        else:
            st.warning("لا توجد خلطات خرسانة مطابقة لمتطلبات هذا العمود.")
    else:
        st.warning("لا يوجد ملف مواد خرسانية (concrete_materials).")

    # -------- أفضل حديد تسليح للأعمدة --------
    st.subheader("🔩 أفضل حديد تسليح للأعمدة (Top Rebar Options)")

    if rebar_df is not None and not rebar_df.empty:
        rebar_sel = select_rebar_for_rule(rebar_df, best_rule, top_n=3)
        if rebar_sel is not None and not rebar_sel.empty:
            rebar_view = rebar_sel[[
                "Rebar_ID",
                "Steel_Grade",
                "Yield_Strength_MPa",
                "Coating_Type",
                "Corrosion_Resistance_Level",
                "Seismic_Suitability",
                "Best_Use_Case",
            ]].copy()
            st.dataframe(rebar_view, use_container_width=True)
        else:
            st.warning("لا توجد خيارات حديد تسليح مطابقة لهذا العمود.")
    else:
        st.warning("لا يوجد ملف مواد حديد تسليح (rebar_materials).")
# ==========================================
#   BEAM UI (واجهة الكمرات)
# ==========================================
def run_beam_ui(project_type: str, structural_system: str, datasets: Dict[str, pd.DataFrame]):
    st.subheader("⚙ إعدادات الكمرات (Beam Settings)")

    col1, col2 = st.columns(2)

    with col1:
        beam_role = st.selectbox(
            "Beam Role (دور الكمرة)",
            ["Floor_Beam", "Primary_Beam", "Secondary_Beam", "Edge_Beam", "Cantilever_Beam"],
            index=0,
            key="b_role",
        )

        span_range = st.selectbox(
            "Span Range (مدى البحر m)",
            ["3-5m", "5-7m", "7-10m"],
            index=1,
            key="b_span",
        )

        load_type = st.selectbox(
            "Load Type (نوع الحمل)",
            ["Uniform", "Point", "Combined"],
            index=0,
            key="b_load_type",
        )

    with col2:
        moment_level = st.selectbox(
            "Moment Level (مستوى العزم)",
            ["Low", "Medium", "High"],
            index=2,
            key="b_moment",
        )

        shear_level = st.selectbox(
            "Shear Level (مستوى القص)",
            ["Low", "Medium", "High"],
            index=2,
            key="b_shear",
        )

        seismic_level = st.selectbox(
            "Seismic Zone Level (مستوى الزلازل)",
            ["Low", "Moderate", "High", "Very_High"],
            index=2,
            key="b_seismic",
        )

    env_type = st.selectbox(
        "Environment Type (نوع البيئة)",
        ["Normal", "XC2", "Marine"],
        index=0,
        key="b_env",
    )

    min_fc = st.number_input(
        "Minimum concrete strength f'c (MPa) [اتركها صفر لاستخدام قيمة الكود]",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key="b_min_fc",
    )

    st.markdown("---")

    if not st.button("📐 تشغيل تصميم الكمرات", key="btn_run_beams"):
        return

    beam_df = pick_df(datasets, ["beam_rules_df", "beams_rules"])
    conc_df = pick_df(datasets, ["concrete_df", "concrete_materials"])
    rebar_df = pick_df(datasets, ["rebar_df", "rebar_materials"])

    if beam_df is None or beam_df.empty:
        st.error("⚠ لا توجد قواعد تصميم للكمرات (beam_rules).")
        return

    crit = {
        "Project_Type": project_type,
        "Structural_System": structural_system,
        "Beam_Role": beam_role,
        "Span_Range_m": span_range,
        "Load_Type": load_type,
        "Moment_Level": moment_level,
        "Shear_Level": shear_level,
        "Seismic_Zone_Level": seismic_level,
        "Environment_Type": env_type,
    }
    if min_fc > 0:
        crit["Min_Concrete_Strength_MPa"] = min_fc

    best_rule = choose_best_beam_rule(beam_df, crit)

    if best_rule is None:
        st.error("❌ لم يتم العثور على قرار هندسي مناسب للكمرات.")
        return

    # ========= القرار الهندسي =========
    st.subheader("✅ القرار الهندسي للكمرات (Beam Engineering Decision)")

    decision_df = best_rule.to_frame(name="Value (القيمة)").reset_index()
    decision_df.columns = ["Parameter (المعيار)", "Value (القيمة)"]
    st.dataframe(decision_df, use_container_width=True)

    # ========= الخرسانة =========
    st.subheader("🧱 أفضل خلطات الخرسانة للكمرات")

    if conc_df is not None and not conc_df.empty:
        conc_sel = select_concrete_for_rule(conc_df, best_rule, top_n=3)
    else:
        conc_sel = None

    if conc_sel is not None and not conc_sel.empty:
        cols_to_show = []
        for c in [
            "Mix_Name",
            "Material_ID",
            "Strength_MPa",
            "Cement_Type",
            "Exposure_Class",
            "Cost_Index",
            "concrete_score",
        ]:
            if c in conc_sel.columns:
                cols_to_show.append(c)
        st.dataframe(conc_sel[cols_to_show], use_container_width=True)
    else:
        st.warning("لا توجد خلطات خرسانة مطابقة.")

    # ========= الحديد =========
    st.subheader("🔩 أفضل حديد تسليح للكمرات")

    if rebar_df is not None and not rebar_df.empty:
        rebar_sel = select_rebar_for_rule(rebar_df, best_rule, top_n=3)
    else:
        rebar_sel = None

    if rebar_sel is not None and not rebar_sel.empty:
        cols_to_show = []
        for c in [
            "Rebar_ID",
            "Steel_Grade",
            "Yield_Strength_MPa",
            "Coating_Type",
            "Corrosion_Resistance_Level",
            "Seismic_Suitability",
            "Best_Use_Case",
            "Cost_Index",
            "rebar_score",
        ]:
            if c in rebar_sel.columns:
                cols_to_show.append(c)
        st.dataframe(rebar_sel[cols_to_show], use_container_width=True)
    else:
        st.warning("لا يوجد حديد تسليح مطابق.")

def run_slab_ui(project_type: str, structural_system: str, datasets: dict):
    st.subheader("⚙ إعدادات البلاطات (Slab Settings)")

    col1, col2 = st.columns(2)

    with col1:
        slab_type = st.selectbox(
            "Slab Type (نوع البلاطة)",
            ["One_Way_Slab", "Two_Way_Slab", "Flat_Slab", "Solid_Slab", "Hollow_Core"],
            index=0,
            key="slab_type",
        )

        load_level = st.selectbox(
            "Load Level (مستوى الحمل)",
            ["Low", "Medium", "High"],
            index=1,
            key="slab_load",
        )

    with col2:
        seismic_level = st.selectbox(
            "Seismic Zone Level (مستوى الزلازل)",
            ["Low", "Moderate", "High", "Very_High"],
            index=1,
            key="slab_seismic",
        )

        env_type = st.selectbox(
            "Environment Type (نوع البيئة)",
            ["Normal", "XC2", "Marine"],
            index=0,
            key="slab_env",
        )

        min_fc = st.number_input(
            "Minimum f'c (MPa) [اختياري] (أدنى مقاومة خرسانة مطلوبة)",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="slab_min_fc",
        )

    st.markdown("---")

    if not st.button("📐 تشغيل تصميم البلاطات", key="run_slab_btn"):
        return

    # نجلب جداول القواعد والمواد
    slab_df = pick_df(datasets, ["slab_rules_df", "slabs_rules"])
    conc_df = pick_df(datasets, ["concrete_df", "concrete_materials"])
    rebar_df = pick_df(datasets, ["rebar_df", "rebar_materials"])
    wp_df = pick_df(datasets, ["waterproofing_df", "waterproofing_materials"])

    if slab_df is None or slab_df.empty:
        st.error("❌ لا توجد قواعد تصميم للبلاطات (slab rules).")
        return

    # نبني معايير الفلترة
    crit = {
        "Project_Type": project_type,
        "Structural_System": structural_system,
        "Slab_Type": slab_type,
        "Load_Level": load_level,
        "Seismic_Zone_Level": seismic_level,
        "Environment_Type": env_type,
    }

    best_rule = pick_best_rule_generic(slab_df, crit)

    if best_rule is None:
        st.error("❌ لم يتم العثور على قاعدة مناسبة للبلاطات حسب المعايير المدخلة.")
        return

    # ===== عرض القرار الهندسي بشكل جدول =====
    st.subheader("✅ القرار الهندسي للبلاطات (Slab Engineering Decision)")

    decision_df = best_rule.to_frame(name="Value (القيمة)").reset_index()
    decision_df.columns = ["Parameter (المعيار)", "Value (القيمة)"]
    st.dataframe(decision_df, use_container_width=True)

    reason = best_rule.get("Reason_Description", "")
    if reason:
        st.info(f"شرح القرار (Explanation):\n{reason}")

    # ===== اختيار الخرسانة وحديد التسليح =====
    from expert_system import select_concrete_for_rule, select_rebar_for_rule

    st.subheader("🧱 أفضل خلطات خرسانة للبلاطات (Top Concrete Mixes for Slabs)")
    if conc_df is not None and not conc_df.empty:
        conc_sel = select_concrete_for_rule(conc_df, best_rule, top_n=3)
        if conc_sel is not None and not conc_sel.empty:
            st.dataframe(
                conc_sel[
                    [
                        "Material_ID",
                        "Strength_MPa",
                        "Cement_Type",
                        "Exposure_Class",
                        "Cost_Index",
                    ]
                ],
                use_container_width=True,
            )
        else:
            st.warning("لا توجد خلطات خرسانة مطابقة.")
    else:
        st.warning("لا توجد داتا للخرسانة (concrete_df).")

    st.subheader("🔩 أفضل حديد تسليح للبلاطات (Top Rebar for Slabs)")
    if rebar_df is not None and not rebar_df.empty:
        rebar_sel = select_rebar_for_rule(rebar_df, best_rule, top_n=3)
        if rebar_sel is not None and not rebar_sel.empty:
            st.dataframe(
                rebar_sel[
                    [
                        "Rebar_ID",
                        "Steel_Grade",
                        "Yield_Strength_MPa",
                        "Coating_Type",
                        "Cost_Index",
                    ]
                ],
                use_container_width=True,
            )
        else:
            st.warning("لا يوجد حديد تسليح مطابق.")
    else:
        st.warning("لا توجد داتا لحديد التسليح (rebar_df).")

def bridge_expert_logic(profile: dict):
    """
    Expert decisions for BRIDGE projects
    Output is SIMPLE and UI-ready (no IDs, no tables)
    """

    decisions = {
        "recommended": [
            {
                "name": "Pre-stressed Concrete Girders",
                "reason": "تقلل الترخيم والتشققات ومناسبة للفضاءات الطويلة"
            },
            {
                "name": "Sulfate Resistant Cement (SRC)",
                "reason": "مقاوم للهجوم الكبريتي في البيئات البحرية والعدوانية"
            },
            {
                "name": "Epoxy Coated Reinforcement",
                "reason": "يحمي حديد التسليح من التآكل بسبب الأملاح والرطوبة"
            },
            {
                "name": "Elastomeric Bearings",
                "reason": "تسمح بالحركة الحرارية وتمتص الاهتزازات"
            },
            {
                "name": "Low Permeability Deck Concrete",
                "reason": "تقلل نفاذية الماء وتحمي التسليح"
            },
            {
                "name": "Deck Waterproofing Membrane",
                "reason": "تمنع تسرب المياه إلى بلاطة الجسر"
            },
        ],

        "conditional": [
            {
                "name": "RC Concrete Girders",
                "reason": "مقبولة فقط للفضاءات القصيرة والمتوسطة"
            },
            {
                "name": "Ordinary Cement with Coatings",
                "reason": "مسموح فقط عند وجود نظام حماية كيميائي كامل"
            },
        ],

        "blocked": [
            {
                "name": "Ordinary Portland Cement (OPC)",
                "reason": "غير مقاوم للكبريتات ويؤدي إلى تلف مبكر"
            },
            {
                "name": "No Waterproofing System",
                "reason": "يسبب صدأ التسليح وفشل مبكر للجسر"
            },
            {
                "name": "Carpet or Flexible Finishes",
                "reason": "غير مناسبة للأحمال والظروف البيئية للجسور"
            },
        ],
    }

    return decisions


def run_industrial_advisor_ui(render_system):
    # ===== Industrial Factory (PEB) =====

    # عنوان المشروع
    import streamlit as st
    st.markdown("### Industrial Factory – Steel Structure (PEB)")
    st.markdown("مصنع صناعي – هيكل معدني مسبق الهندسة")
    st.markdown("---")

    render_system(
        "1) Foundations (Substructure) – Footings & Pedestals",
        "١) الأساسات (القواعد ورقاب الأعمدة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Isolated footings + RC pedestals", "قواعد منفصلة + رقاب خرسانية",
             "Economic for steel structures; transfers point loads efficiently and elevates steel above damp ground.",
             "اقتصادي للهياكل المعدنية؛ ينقل الأحمال المركزة بكفاءة ويرفع الحديد عن الرطوبة."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Raft foundation", "لبشة خرسانية",
             "Only for very weak soil or exceptionally high loads; otherwise unnecessary cost.",
             "فقط للتربة الضعيفة جداً أو الأحمال الكبيرة جداً؛ غير ذلك كلفة غير مبررة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Strip foundations in brick/stone", "أساسات شريطية من طوب/حجر",
             "Cannot resist uplift or moments from wind actions on tall steel frames.",
             "لا تقاوم الشد والعزوم الناتجة عن الرياح على الهياكل المعدنية العالية."),
        ],
        height=300
    )

    render_system(
        "2) Structural Skeleton – Main Frames",
        "٢) الهيكل الإنشائي (الإطارات الرئيسية)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "PEB (Pre-Engineered Building)", "نظام معدني مسبق الهندسة (PEB)",
             "Large clear spans and tapered members can cut steel weight/cost significantly versus conventional frames.",
             "فضاءات واسعة بدون أعمدة وسطية ومقاطع متدرجة تقلل وزن/كلفة الحديد مقارنة بالتقليدي."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Concrete frame", "هيكل خرساني تقليدي",
             "For multi-storey factories or severe chemical environments that accelerate steel corrosion.",
             "للمصانع متعددة الطوابق أو البيئات الكيميائية التي تسرّع تآكل الحديد."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Load-bearing wall system", "نظام حوائط حاملة",
             "Not suitable for wide factory roofs and vibrations; unsafe under lateral wind actions.",
             "غير مناسب لأسقف الفضاءات الواسعة واهتزازات المعدات؛ غير آمن تحت الرياح الجانبية."),
        ],
        height=300
    )

    render_system(
        "3) Industrial Flooring – Production Hall",
        "٣) الأرضيات الصناعية (صالة الإنتاج)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Power-troweled concrete + dry shake hardener", "خرسانة مروحة + مقسي سطح",
             "Monolithic hard surface; resists forklift abrasion and oils and reduces dusting.",
             "سطح صلد متجانس؛ يقاوم احتكاك الرافعات والزيوت ويقلل الغبار."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Epoxy coating", "طلاء إيبوكسي",
             "Only for clean rooms (food/pharma); heavy impact may cause peeling in heavy industries.",
             "فقط للغرف النظيفة (غذاء/دواء)؛ قد يتقشر مع الصدمات بالصناعات الثقيلة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Ceramic/normal tiles", "سيراميك/بلاط اعتيادي",
             "Joints become weak points under hard wheels; rapid cracking and debonding.",
             "الفواصل نقطة ضعف مع عجلات الرافعات؛ تكسر وتفكك سريع."),
        ],
        height=300
    )

    render_system(
        "4) Building Envelope – Roof & Upper Cladding",
        "٤) الغلاف الخارجي (السقف والجدران العلوية)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Sandwich panels", "ألواح ساندوتش بانل",
             "Excellent thermal insulation; reduces cooling loads and limits solar heat gain.",
             "عزل حراري ممتاز؛ يقلل أحمال التكييف ويمنع دخول حرارة الشمس."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Single-skin metal sheet", "صاج مفرد",
             "Only for non-conditioned open stores; condensation and poor insulation are major issues.",
             "فقط للمخازن غير المكيفة؛ يسبب تكثف وضعف عزل."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Asbestos sheets", "ألواح أسبستوس",
             "Carcinogenic and internationally banned; violates health/environment regulations.",
             "مسرطن ومحظور دولياً؛ مخالف للصحة والبيئة."),
        ],
        height=300
    )

    render_system(
        "5) Side Walls – Lower Impact Zone",
        "٥) الجدران الجانبية (منطقة الصدمات السفلية)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Blockwork up to 3m + metal cladding above", "بلوك حتى 3م + صاج للأعلى",
             "Lower zone must resist vehicle/forklift impacts; upper cladding reduces weight and cost.",
             "السفلي يتحمل صدمات الرافعات؛ العلوي صاج لتخفيف الوزن والكلفة."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Precast concrete walls", "جدران خرسانية مسبقة الصب",
             "For high-security/high-risk facilities; fast erection but higher cost and heavy lifting required.",
             "للمنشآت الأمنية/عالية الخطورة؛ تركيب سريع لكن كلفة أعلى ومعدات رفع."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Curtain wall glazing in production areas", "واجهات زجاجية بمناطق الإنتاج",
             "Breakage hazard and greenhouse effect; unsafe for industrial operations.",
             "خطر الكسر والشظايا ويزيد الحرارة (بيت زجاجي)؛ غير آمن صناعياً."),
        ],
        height=320
    )

    render_system(
        "6) Fire Protection – Steel Frame",
        "٦) الوقاية من الحريق (حماية الهيكل المعدني)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Intumescent fireproof paint", "دهان منتفخ مقاوم للحريق",
             "Expands under heat to form an insulating layer; provides evacuation time (typically 1–2 hours).",
             "ينتفخ عند الحرارة ليكوّن طبقة عازلة؛ يوفر زمن إخلاء (عادة 1–2 ساعة)."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Concrete encasement (selected columns)", "تغليف خرساني (لبعض الأعمدة)",
             "Use for lower columns exposed to mechanical impacts; effective but increases size/weight.",
             "للأعمدة السفلية المعرضة للصدمات؛ ممتاز لكنه يزيد الحجم والوزن."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Unprotected exposed steel", "حديد مكشوف بدون حماية",
             "Steel loses strength rapidly at high temperature; can lead to roof collapse within minutes.",
             "الحديد يفقد مقاومته بسرعة مع الحرارة؛ قد يسبب انهيار السقف خلال دقائق."),
        ],
        height=330
    )

    render_system(
        "7) Accessories – Natural Ventilation & Daylighting",
        "٧) الملحقات والتهوية (تهوية وإضاءة طبيعية)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Turbo ventilators + skylights", "مراوح توربينية + سكاي لايت",
             "Passive hot-air extraction without electricity; daylight reduces energy consumption.",
             "سحب هواء ساخن بدون كهرباء؛ إضاءة نهارية تقلل استهلاك الطاقة."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Large electric exhaust fans", "مراوح شفط كهربائية كبيرة",
             "Only when toxic fumes/heavy dust exist; high energy demand.",
             "فقط عند وجود أبخرة سامة/غبار كثيف؛ تستهلك طاقة عالية."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Hanging lights on loose wiring", "إضاءة معلقة بأسلاك عادية",
             "Factory vibrations may cut cables and drop fixtures; use rigid conduits/supports.",
             "اهتزازات المصنع قد تقطع الأسلاك وتسقط الإنارة؛ يجب مواسير/تثبيت صلب."),
        ],
        height=320
    )

    render_system(
        "8) Rainwater Drainage – Gutters & Downpipes",
        "٨) تصريف مياه الأمطار (مزاريب وأنابيب)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Galvanized gutters + external UPVC downpipes", "مزاريب مجلفنة + UPVC خارجي",
             "Galvanized steel resists corrosion and large roof runoff; external pipes are easy to service/replace.",
             "المجلفن يقاوم الصدأ ويتحمل مياه السقف الكبيرة؛ الأنابيب الخارجية سهلة الصيانة."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Valley gutters (internal)", "مزاريب داخلية",
             "Only for multi-span layouts; clogging risks require strict periodic maintenance.",
             "فقط للمشاريع متعددة الفضاءات؛ خطر انسداد ويحتاج صيانة دقيقة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Hidden drainage inside columns/walls", "تصريف مخفي داخل الأعمدة/الجدران",
             "Leaks/blocks go unnoticed and damage foundations; repairs require demolition.",
             "الانسداد/الكسر غير مرئي ويسبب ضرر للأساسات؛ إصلاحه يتطلب تكسير."),
        ],
        height=340
    )

    render_system(
        "9) Industrial Access – Truck Doors",
        "٩) الأبواب والمداخل (بوابات الشاحنات)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Motorized rolling shutters / sectional doors", "رول شتر كهربائي / أبواب مقطعية",
             "Space-saving upward opening; wind resistant; fast operation limits dust and preserves conditioning.",
             "تفتح للأعلى وتوفر مساحة؛ مقاومة للرياح؛ سريعة لتقليل الغبار وحفظ التكييف."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Sliding doors", "أبواب منزلقة",
             "Only for very wide openings; tracks get dirty and need space/maintenance.",
             "فقط للفتحات العريضة جداً؛ السكة تتسخ وتتعطل وتحتاج مساحة وصيانة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Swing gates for main access", "بوابات مفصلية للمداخل الرئيسية",
             "Unsafe in strong wind and consumes maneuvering space for trucks.",
             "غير آمنة مع الرياح وتستهلك مساحة مناورة للشاحنات."),
        ],
        height=320
    )

    render_system(
        "10) Logistics Yard – External Truck Traffic",
        "١٠) الساحات الخارجية والتحميل (حركة الشاحنات)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Heavy-duty concrete pavers (8–10 cm)", "إنترلوك عالي التحمل (8–10 سم)",
             "Durable and flexible; easy to remove/relay for future services without demolition.",
             "متحمل ومرن؛ يمكن فكه وإعادته بسهولة للتمديدات بدون تكسير."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Reinforced concrete slab (selected zones)", "بلاطة خرسانية مسلحة (مناطق محددة)",
             "Use at loading docks and tight turning zones; better against tire scrubbing but harder to repair.",
             "للأرصفة ومناطق الدوران؛ تقاوم فرك الإطارات لكن صيانتها أصعب."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Asphalt in truck parking zones", "أسفلت بمناطق وقوف الشاحنات",
             "Rutting under static heavy loads in hot weather; forms depressions quickly.",
             "يتخدد تحت الحمل الثابت بالصيف؛ يسبب حفر/تخسفات بسرعة."),
        ],
        height=340
    )

    render_system(
        "11) Collision Protection – Forklifts Impact",
        "١١) الحماية من التصادم (صدمات الرافعات)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Concrete-filled steel bollards", "بولاردات فولاذية مملوءة خرسانة",
             "Absorbs forklift impact and protects primary columns and door zones from failure.",
             "يمتص صدمة الرافعة ويحمي الأعمدة الرئيسية ومناطق الأبواب من الضرر."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Rubber/plastic barriers", "حواجز مطاطية/بلاستيكية",
             "Only for light traffic or pedestrian paths; cannot stop fast/heavy vehicles.",
             "فقط للحركة الخفيفة أو ممرات المشاة؛ لا توقف مركبة ثقيلة مسرعة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Low curbs only", "أرصفة واطئة فقط",
             "Forklift clearance may pass over curb and strike wall/column; needs higher protection.",
             "الرافعة تتجاوز الرصيف وتصطدم بالجدار/العمود؛ يلزم حاجز مرتفع."),
        ],
        height=320
    )

    render_system(
        "12) Mezzanine Offices – Inside Factory",
        "١٢) المكاتب الداخلية (ميزانين داخل المصنع)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Drywall partitions + double acoustic insulation", "جبس بورد + عزل صوتي مزدوج",
             "Lightweight and fast; reduces noise transfer from machinery to office zones.",
             "خفيف وسريع؛ يقلل انتقال ضوضاء الماكينات للمكاتب."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Blockwork (ground floor only)", "بلوك (للأرضي فقط)",
             "Too heavy for mezzanine unless specially designed; acceptable on ground floor.",
             "ثقيل على الميزانين إلا بتصميم مكلف؛ مقبول على الأرضي."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Full glass partitions without acoustic treatment", "قواطع زجاجية بدون عزل صوتي",
             "Factory noise makes office work impractical; requires acoustic-rated systems.",
             "ضوضاء المصنع تجعل العمل مستحيلاً؛ يلزم نظام بعزل صوتي."),
        ],
        height=320
    )

    # ===== Expert Conclusion =====
    import streamlit.components.v1 as components
    conclusion_html = """
    <div style="border:1px solid #e5e5e5; padding:14px; border-radius:10px; font-family:Arial;">
      <div style="font-size:18px; font-weight:700; margin-bottom:6px;">Expert Conclusion</div>
      <div style="direction:rtl; text-align:right; font-family:Amiri, serif; font-size:16px; color:#333; margin-bottom:10px;">الخلاصة الهندسية</div>

      <div style="margin-bottom:6px;">
        <b>PEB steel structure</b> is recommended for clear spans and cost efficiency in typical industrial plants.
      </div>
      <div style="direction:rtl; text-align:right; font-family:Amiri, serif; color:#444; margin-bottom:10px;">
        يوصى بنظام PEB لأنه يحقق فضاءات واسعة وكلفة أقل للمصانع النمطية.
      </div>

      <div style="margin-bottom:6px;">
        <b>Monolithic industrial floors</b> (power trowel + hardener) are essential for forklifts, abrasion, oils, and dust control.
      </div>
      <div style="direction:rtl; text-align:right; font-family:Amiri, serif; color:#444; margin-bottom:10px;">
        الأرضيات المتجانسة (مروحة + مقسي سطح) ضرورية لتحمل الرافعات والاحتكاك والزيوت ومنع الغبار.
      </div>

      <div style="margin-bottom:6px;">
        <b>Fire protection for steel</b> is mandatory; unprotected steel can lead to rapid collapse during fire.
      </div>
      <div style="direction:rtl; text-align:right; font-family:Amiri, serif; color:#444;">
        حماية الحديد من الحريق إلزامية؛ الحديد المكشوف قد يؤدي لانهيار سريع أثناء الحريق.
      </div>
    </div>
    """
    components.html(conclusion_html, height=330, scrolling=False)

def run_hospital_advisor_ui(render_system):
    import streamlit as st

    st.markdown("### Hospital Materials Decisions")
    st.markdown("قرارات مواد المستشفى")
    st.markdown("---")


    # =========================
    # 1) Structural & Foundations
    # =========================
    render_system(
        "1) Foundations & Substructure",
        "١) الأساسات والهيكل السفلي",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "SRC Cement + Low w/c Concrete + Waterproofing",
             "أسمنت مقاوم للكبريتات + خرسانة قليلة النفاذية + عزل مائي",
             "High durability and low permeability; protects basements and critical services from moisture/sulfates.",
             "ديمومة عالية ونفاذية قليلة؛ يحمي الأقبية والخدمات الحساسة من الرطوبة/الكبريتات."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Normal OPC + Enhanced cover + Admixtures",
             "أسمنت عادي + غطاء أكبر + مضافات",
             "Only acceptable in non-aggressive soil with strict QC and curing; otherwise durability risk.",
             "مقبول فقط بتربة غير عدوانية ومع ضبط جودة ومعالجة صارمة؛ وإلا ترتفع مخاطر التلف."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No Waterproofing for basements",
             "بدون عزل مائي للأقبية",
             "Leads to leaks, mold, corrosion, and damage to medical/electrical rooms.",
             "يسبب تسرب وعفن وصدأ وتلف غرف الكهرباء/الأجهزة الطبية."),
        ],
        height=320
    )

    render_system(
        "2) Main Structural System (Hospital Building)",
        "٢) النظام الإنشائي الرئيسي (مبنى المستشفى)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "RC Frame + Shear Walls (Dual System where needed)",
             "إطارات خرسانية + جدران قص (نظام مزدوج عند الحاجة)",
             "Stable for vibrations, good fire resistance, supports heavy medical equipment and future expansions.",
             "ثبات جيد ضد الاهتزازات، مقاومة حريق ممتازة، يتحمل أجهزة ثقيلة وإمكانية توسعة مستقبلية."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Steel Frame + Fireproofing + Vibration Control",
             "هيكل فولاذي + حماية حريق + ضبط اهتزاز",
             "Works if fireproofing and vibration isolation are rigorously designed and maintained.",
             "ينفع إذا تم تصميم حماية الحريق وعزل الاهتزاز بدقة مع صيانة مستمرة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Load-bearing masonry as primary system",
             "حوائط حاملة كنظام رئيسي",
             "Not suitable for hospital spans, flexibility, and seismic/wind demands; limits MEP routing.",
             "غير مناسب لفضاءات المستشفيات والمرونة ومتطلبات الزلازل/الرياح ويعيق مسارات الخدمات."),
        ],
        height=320
    )

    # =========================
    # 2) Envelope (Roof / Façade) + Thermal & Moisture
    # =========================
    render_system(
        "3) Roof System (Leak & Thermal Control)",
        "٣) نظام السقف (منع التسرب والعزل الحراري)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Double-layer Waterproofing Membrane + Thermal Insulation",
             "عزل مائي طبقتين + عزل حراري",
             "Hospitals must prevent leaks above ICUs/ORs; insulation reduces HVAC load and improves comfort.",
             "منع التسرب فوق العناية/العمليات ضروري؛ العزل الحراري يقلل حمل التكييف ويحسن الراحة."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Single waterproofing layer (with strict detailing)",
             "طبقة عزل واحدة (بتفاصيل صارمة)",
             "Only for non-critical blocks and with perfect slopes, drains, and inspections.",
             "فقط لأجزاء غير حرجة ومع ميول وتصريف وفحص دوري ممتاز."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No insulation / poor drainage slopes",
             "بدون عزل حراري / ميول تصريف سيئة",
             "Causes condensation, mold, higher energy bills, and frequent roof failures.",
             "يسبب تكاثف وعفن وكلفة طاقة عالية وفشل متكرر بالسقف."),
        ],
        height=320
    )

    render_system(
        "4) External Walls & Façade",
        "٤) الجدران الخارجية والواجهة",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Insulated façade (AAC/Block + Insulation + durable coating)",
             "جدار معزول (بلوك/أيه-إيه-سي + عزل + طلاء متين)",
             "Controls heat/moisture; durable finish supports hygiene and reduces maintenance.",
             "يسيطر على الحرارة/الرطوبة؛ تشطيب متين يدعم النظافة ويقلل الصيانة."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Curtain wall limited to admin/public areas",
             "واجهات زجاجية بمناطق الإدارة/الاستقبال فقط",
             "Allowed if shading, thermal glazing, and cleaning/safety plan exist.",
             "مسموح إذا يوجد تظليل وزجاج حراري وخطة تنظيف/سلامة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Unsealed porous external finishes",
             "تشطيبات خارجية مسامية غير محكمة",
             "Absorbs moisture and pollutants; stains and rapid deterioration.",
             "تمتص الرطوبة والملوثات؛ تسبب بقع وتدهور سريع."),
        ],
        height=320
    )

    # =========================
    # 3) Internal Partitions / Doors / Infection Control
    # =========================
    render_system(
        "5) Internal Partitions (Cleanability & Acoustics)",
        "٥) القواطع الداخلية (سهولة التعقيم والعزل الصوتي)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Moisture-resistant drywall + washable paint (public/wards)",
             "جبس بورد مقاوم للرطوبة + صبغ قابل للغسل (ممرات/أجنحة)",
             "Fast, clean, and service-friendly; supports hidden MEP and easy repair.",
             "سريع ونظيف ويسهّل الخدمات والصيانة، ويدعم تمديدات مخفية."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Block/brick partitions in impact-prone zones",
             "قواطع بلوك/طابوق بالمناطق المعرضة للصدمات",
             "Use where trolley impacts are high; must be sealed and finished with washable coating.",
             "يستخدم عند كثرة الصدمات (عربات) مع ضرورة الإحكام وطلاء قابل للغسل."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Unsealed wood partitions in clinical zones",
             "قواطع خشبية غير محكمة بالمناطق السريرية",
             "Hard to disinfect; absorbs moisture; infection-control risk.",
             "صعبة التعقيم وتمتص الرطوبة وترفع مخاطر العدوى."),
        ],
        height=320
    )

    render_system(
        "6) Doors (OR/ICU/Radiology/Public)",
        "٦) الأبواب (عمليات/عناية/أشعة/عامة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "HPL/steel hospital doors + antimicrobial surface",
             "أبواب مستشفيات HPL/فولاذ + سطح مضاد للميكروبات",
             "High cleanability, impact resistance, and long life in high-traffic corridors.",
             "تعقيم سهل ومقاومة صدمات وعمر طويل بالممرات المزدحمة."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Automatic sliding doors for OR/ICU entries",
             "أبواب سلايد أوتوماتيك لمداخل العمليات/العناية",
             "Allowed if sensors/backup and maintenance plan exist; improves sterile flow.",
             "مسموح مع حساسات وبدائل وخطة صيانة؛ يحسن الحركة المعقمة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Porous wooden doors in clinical areas",
             "أبواب خشب مسامي بالمناطق السريرية",
             "Absorbs moisture and contaminants; poor infection control.",
             "يمتص رطوبة وملوثات؛ غير مناسب للسيطرة على العدوى."),
        ],
        height=320
    )

    # =========================
    # 4) Flooring by Zones (OR / ICU / Corridors / Wet Areas)
    # =========================
    render_system(
        "7) Flooring - Operating Rooms (OR)",
        "٧) الأرضيات - غرف العمليات",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Seamless conductive vinyl (antistatic) + coved skirting",
             "فينيل طبي موصل (مضاد للكهرباء الساكنة) + وزرة مقعرة",
             "Seamless disinfection; antistatic for equipment; coved edges prevent dirt traps.",
             "تعقيم بدون فواصل؛ مضاد للكهرباء الساكنة للأجهزة؛ الزوايا المقعرة تمنع تجمع الأوساخ."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Epoxy resin floor (OR-grade) with strict substrate prep",
             "أرضية إيبوكسي (مواصفات عمليات) مع تجهيز صارم للسطح",
             "Works if cracks/joints are controlled and installation is perfect; repair plan needed.",
             "ينجح إذا تم ضبط الفواصل والتشققات والتركيب ممتاز مع خطة إصلاح."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Ceramic tiles with grout joints",
             "سيراميك بفواصل إسمنتية",
             "Grout joints harbor microbes and complicate sterile cleaning.",
             "الفواصل تجمع ميكروبات وتعرقل التنظيف المعقم."),
        ],
        height=340
    )

    render_system(
        "8) Flooring - ICU / Wards / Corridors",
        "٨) الأرضيات - العناية/الأجنحة/الممرات",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Homogeneous vinyl sheet (seam-welded)",
             "فينيل متجانس لفّات (تلحيم فواصل)",
             "Durable, quiet under trolleys, easy cleaning, and long service life.",
             "متين وهادئ مع العربات وسهل التنظيف وعمره طويل."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Rubber flooring (high traffic) with proper maintenance",
             "مطاط طبي (للحركة العالية) مع صيانة",
             "Excellent slip and noise control but needs correct cleaning products.",
             "ممتاز ضد الانزلاق والضوضاء لكن يحتاج مواد تنظيف مناسبة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Carpet in clinical corridors",
             "سجاد بالممرات السريرية",
             "Traps dust/pathogens; difficult disinfection; infection-control risk.",
             "يحجز غبار/ممرضات وصعب تعقيمه ويرفع مخاطر العدوى."),
        ],
        height=340
    )

    render_system(
        "9) Flooring - Wet Areas (Toilets / CSSD / Labs)",
        "٩) الأرضيات - المناطق الرطبة (حمامات/تعقيم/مختبرات)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Anti-slip ceramic/porcelain + epoxy grout + proper slopes",
             "بورسلان/سيراميك مانع انزلاق + فواصل إيبوكسي + ميول صحيحة",
             "Slip safety + chemical resistance; epoxy grout improves hygiene in wet zones.",
             "أمان ضد الانزلاق ومقاومة كيميائية؛ فواصل إيبوكسي تعزز النظافة بالمناطق الرطبة."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Epoxy floor with chemical-resistant topcoat",
             "إيبوكسي مع طبقة مقاومة كيميائية",
             "Good for labs if chemical class is known and maintenance is scheduled.",
             "جيد للمختبرات إذا نوع المواد الكيميائية معروف وتوجد صيانة دورية."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Polished marble in wet clinical areas",
             "رخام مصقول بمناطق رطبة",
             "High slip risk and staining; unsafe for patients/staff.",
             "خطر انزلاق عالي وسهل التبقع؛ غير آمن للمرضى والكوادر."),
        ],
        height=340
    )

    # =========================
    # 5) Ceilings (OR / Imaging / Corridors)
    # =========================
    render_system(
        "10) Ceilings - OR / ICU / Clean Areas",
        "١٠) الأسقف - العمليات/العناية/المناطق النظيفة",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Sealed hygienic ceiling (metal/PVC) with flush access panels",
             "سقف صحي محكم (معدني/PVC) مع فتحات ملساء",
             "Easy wipe-down; prevents dust; supports clean HVAC diffusers and lighting.",
             "سهل المسح ويمنع الغبار ويدعم فتحات تكييف وإنارة صحية."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Moisture-resistant gypsum with medical-grade paint",
             "جبس مقاوم للرطوبة مع صبغ طبي",
             "Allowed in non-sterile areas only; must be sealed and maintained.",
             "مسموح فقط بمناطق غير معقمة مع إحكام وصيانة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Open-grid ceilings in clinical rooms",
             "سقوف شبكية مفتوحة بالغرف السريرية",
             "Dust traps and poor infection control; exposes services.",
             "تجمع غبار وتضعف السيطرة على العدوى وتكشف الخدمات."),
        ],
        height=340
    )

    # =========================
    # 6) MEP Core (HVAC / Plumbing / Medical Gases)
    # =========================
    render_system(
        "11) HVAC - Critical Areas (OR/ICU/Isolation)",
        "١١) التكييف - المناطق الحرجة (عمليات/عناية/عزل)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "HEPA filtration + pressure control (positive/negative) + dedicated AHU",
             "فلترة HEPA + تحكم ضغط (موجب/سالب) + وحدة مناولة مستقلة",
             "Controls infection via airflow direction and high filtration; essential for OR/isolation rooms.",
             "يسيطر على العدوى باتجاه الهواء والفلترة العالية؛ أساسي للعمليات/العزل."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Central HVAC with zoning + strict balancing",
             "تكييف مركزي مع تقسيم زونات + وزن دقيق",
             "Acceptable if balancing and monitoring are continuous; otherwise pressure failures occur.",
             "مقبول إذا توجد مراقبة ووزن مستمر؛ وإلا يحدث فشل ضغط الغرف."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Split AC for OR/ICU",
             "سبلت للعمليات/العناية",
             "No sterile filtration/pressure control; high infection risk.",
             "لا يوفر فلترة/ضغط معقم؛ يرفع خطر العدوى."),
        ],
        height=360
    )

    render_system(
        "12) Plumbing - Hot/Cold/Drainage",
        "١٢) السباكة - مياه/تصريف",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "PP-R / Copper for hot water + floor drains with traps",
             "PP-R / نحاس للماء الحار + مصارف أرضية مع سيفونات",
             "Reliable and hygienic; proper traps prevent odors and contamination backflow.",
             "موثوق وصحي؛ السيفونات تمنع الروائح والارتداد الملوث."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "UPVC for drainage with proper venting",
             "UPVC للتصريف مع تهوية صحيحة",
             "Works if venting and slopes are correct; maintenance access required.",
             "ينجح إذا التهوية والميول صحيحة مع توفير فتحات صيانة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Hidden drainage without access points",
             "تصريف مخفي بدون فتحات صيانة",
             "Any blockage/leak becomes destructive; unacceptable in hospitals.",
             "أي انسداد/تسرب يصبح كارثي؛ غير مقبول بالمستشفيات."),
        ],
        height=340
    )

    render_system(
        "13) Medical Gases (O2 / Vacuum / Air)",
        "١٣) الغازات الطبية (أوكسجين/فاكيوم/هواء)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Copper medical gas piping + labeled zones + alarm panels",
             "أنابيب نحاس للغازات + زونات مع وسم + إنذارات",
             "Safety and compatibility; zoning isolates faults and protects ICU/OR supply.",
             "أمان وتوافق؛ التقسيم يعزل الأعطال ويحمي تزويد العناية/العمليات."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Manifold system with redundancy plan",
             "نظام مانيفولد مع تكرار احتياطي",
             "Acceptable if redundancy and monitoring are present; tested commissioning required.",
             "مقبول بوجود احتياط ومراقبة مع فحص وتشغيل دقيق."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Unregulated cylinders inside clinical corridors",
             "اسطوانات غير منظمة داخل الممرات",
             "High safety hazard; blocks egress and increases fire/explosion risk.",
             "خطر سلامة عالي ويعيق الإخلاء ويرفع مخاطر الحريق/الانفجار."),
        ],
        height=360
    )

    # =========================
    # 7) Electrical & Lighting (OR / Imaging / Public)
    # =========================
    render_system(
        "14) Power System (UPS + Generator)",
        "١٤) منظومة القدرة (UPS + مولد)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Generator + UPS for critical loads (OR/ICU/Imaging)",
             "مولد + UPS للأحمال الحرجة (عمليات/عناية/أشعة)",
             "Ensures life-safety continuity; prevents device failure during outages.",
             "يضمن استمرارية إنقاذ الحياة ويمنع توقف الأجهزة عند انقطاع الكهرباء."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Generator only (no UPS) for non-critical blocks",
             "مولد فقط (بدون UPS) للأجزاء غير الحرجة",
             "Allowed for admin/public areas; not for ICU/OR equipment.",
             "مقبول للإدارة/العامة فقط؛ غير مناسب لأجهزة العناية/العمليات."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No backup power",
             "بدون قدرة احتياطية",
             "Unacceptable for hospital operation; life-safety risk.",
             "غير مقبول لتشغيل المستشفى ويعرض سلامة المرضى للخطر."),
        ],
        height=340
    )

    render_system(
        "15) Lighting - OR / ICU / Corridors",
        "١٥) الإنارة - عمليات/عناية/ممرات",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "LED medical-grade + emergency lighting + low-glare",
             "LED بمواصفات طبية + إنارة طوارئ + تقليل الوهج",
             "Stable light, low heat, energy efficient; emergency lights support evacuation.",
             "ضوء ثابت وحرارة قليلة وتوفير طاقة؛ إنارة الطوارئ تدعم الإخلاء."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Standard LED with proper diffusion (non-critical areas)",
             "LED اعتيادي مع ناشر ضوء (مناطق غير حرجة)",
             "Acceptable in offices/visitors areas if glare and maintenance are controlled.",
             "مقبول بالمكاتب/الزوار إذا تم ضبط الوهج والصيانة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Flicker-prone/poor-quality fixtures in clinical rooms",
             "إنارة رديئة تسبب وميض بالغرف السريرية",
             "Causes discomfort and errors; poor reliability in critical care.",
             "تسبب إجهاد وأخطاء وضعف موثوقية بالعناية الحرجة."),
        ],
        height=340
    )

    # =========================
    # 8) Radiology / MRI / CT (Shielding + Vibration)
    # =========================
    render_system(
        "16) Radiology Rooms (X-ray/CT) - Shielding",
        "١٦) غرف الأشعة (سينية/CT) - التدريع",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Lead shielding in walls/doors + lead glass window",
             "تدريع رصاص بالجدران/الأبواب + زجاج رصاص",
             "Mandatory for radiation protection; ensures safe exposure limits for staff/public.",
             "إلزامي للحماية من الإشعاع ويضمن حدود تعرض آمنة للكوادر والعامة."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "High-density concrete where lead is constrained",
             "خرسانة عالية الكثافة عند تعذر الرصاص",
             "Can substitute in some designs if thickness/calculations are correct.",
             "يمكن أن تعوض ببعض الحالات إذا السماكة والحسابات صحيحة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No shielding / normal doors",
             "بدون تدريع / أبواب عادية",
             "Unsafe radiation leakage; violates regulations and endangers people.",
             "تسرب إشعاعي خطر ويخالف الضوابط ويعرض الناس للأذى."),
        ],
        height=360
    )

    render_system(
        "17) MRI Room - Non-magnetic Requirements",
        "١٧) غرفة الرنين MRI - متطلبات اللا مغناطيسية",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Non-magnetic fixtures + RF shielding (Faraday cage)",
             "تجهيزات غير مغناطيسية + تدريع ترددات (قفص فاراداي)",
             "Prevents hazards and signal interference; ensures imaging quality and safety.",
             "يمنع المخاطر والتداخل ويضمن جودة التصوير والسلامة."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Controlled access hardware with strict signage and training",
             "معدات دخول مضبوطة مع لافتات وتدريب",
             "Works if staff training and access control are enforced.",
             "ينجح إذا تدريب الكوادر والسيطرة على الدخول صارمة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Ferromagnetic items in MRI zone",
             "مواد/معدات مغناطيسية بمنطقة MRI",
             "Projectile hazard; severe injury risk and equipment damage.",
             "خطر قذف شديد قد يسبب إصابات خطيرة وتلف الجهاز."),
        ],
        height=360
    )

    # =========================
    # 9) Fire Safety (Doors / Compartmentation)
    # =========================
    render_system(
        "18) Fire Protection & Egress",
        "١٨) السلامة من الحريق والإخلاء",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Fire-rated doors + compartments + alarms/sprinklers",
             "أبواب مقاومة حريق + تقسيم قطاعات + إنذار/رش",
             "Controls smoke spread and protects evacuation routes in high-occupancy buildings.",
             "يحد من الدخان ويحمي مسارات الإخلاء في مبنى عالي الإشغال."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Partial sprinklers (only where allowed by code)",
             "رش جزئي (حسب سماح الكود)",
             "Acceptable only if authority and code allow; must keep protected exits.",
             "مقبول فقط إذا الجهة والكود يسمحان مع حماية مخارج الإخلاء."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No fire-rated separation in clinical blocks",
             "بدون فصل مقاوم حريق بالكتل السريرية",
             "Rapid smoke spread; catastrophic risk during emergencies.",
             "انتشار دخان سريع وخطر كارثي أثناء الطوارئ."),
        ],
        height=360
    )

    # =========================
    # 10) Finishes (Walls / Paint) - Cleanability
    # =========================
    render_system(
        "19) Internal Wall Finishes (Hygiene)",
        "١٩) تشطيبات الجدران الداخلية (النظافة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Washable antimicrobial paint / PVC wall protection in corridors",
             "دهان قابل للغسل مضاد للميكروبات / حماية PVC بالممرات",
             "Supports infection control and resists trolley impacts in high-traffic areas.",
             "يدعم السيطرة على العدوى ويقاوم صدمات العربات بالممرات."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Ceramic wall tiles in wet rooms only",
             "تبليط جدران بالمناطق الرطبة فقط",
             "Good in toilets/CSSD if joints are sealed and maintained.",
             "ممتاز بالحمامات/التعقيم إذا الفواصل محكمة وتحت صيانة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Textured/porous paints in clinical zones",
             "دهانات خشنة/مسامية بالمناطق السريرية",
             "Difficult to disinfect; traps dirt and microbes.",
             "صعبة التعقيم وتحبس الأوساخ والميكروبات."),
        ],
        height=340
    )

    # =========================
    # 11) Summary (Short)
    # =========================
    render_system(
        "20) Expert Summary (Hospital)",
        "٢٠) خلاصة الخبير (المستشفى)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "OR/ICU: Seamless vinyl + hygienic ceiling + HEPA & pressure control",
             "العمليات/العناية: فينيل بدون فواصل + سقف صحي + HEPA وتحكم ضغط",
             "This trio is the core of infection-control decisions in critical areas.",
             "هذا الثلاثي هو قلب قرارات السيطرة على العدوى بالمناطق الحرجة."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Public/Admin: broader material options with maintenance plan",
             "العامة/الإدارة: خيارات أوسع مع خطة صيانة",
             "Materials can be relaxed in non-clinical areas only.",
             "يمكن تخفيف الاشتراطات فقط بالمناطق غير السريرية."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Carpet in clinical + Split AC in OR/ICU + No shielding in radiology",
             "سجاد سريري + سبليت بالعمليات/العناية + بدون تدريع للأشعة",
             "These are high-risk choices that break infection/safety requirements.",
             "هذه اختيارات عالية الخطورة وتخالف متطلبات العدوى/السلامة."),
        ],
        height=320
    )


def run_residential_advisor_ui(render_system):
    """
    Residential Materials Decisions (NO buttons here)
    Uses shared render_system(title_en, title_ar, rows, height)
    """

    import streamlit as st

    st.markdown("### Residential Materials Decisions")
    st.markdown("قرارات مواد المشروع السكني")
    st.markdown("---")

    # =========================================================
    # 1) Foundations & Substructure
    # =========================================================
    render_system(
        "1) Foundations & Substructure",
        "١) الأساسات والهيكل السفلي",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "RC isolated footings / strip footings (as per soil) with good waterproofing",
             "قواعد منفصلة/شريطية حسب التربة مع عزل مائي جيد",
             "Common economical system for residential loads; waterproofing protects against rising damp.",
             "حل اقتصادي شائع لأحمال السكن؛ العزل يمنع الرطوبة الصاعدة."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Raft foundation (only for weak soil / differential settlement risk)",
             "لبشة (فقط للتربة الضعيفة/خطر هبوط تفاضلي)",
             "Use when soil capacity is low or settlement control is critical.",
             "تستخدم عند ضعف تحمل التربة أو عند أهمية السيطرة على الهبوط."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Unengineered stone/masonry foundations",
             "أساسات حجر/طابوق بدون تصميم هندسي",
             "Uncontrolled quality and poor performance under settlement and moisture.",
             "جودة غير مضمونة وأداء ضعيف مع الهبوط والرطوبة."),
        ],
        height=300
    )

    # =========================================================
    # 2) Structural System (Frame / Walls)
    # =========================================================
    render_system(
        "2) Structural System (Main Skeleton)",
        "٢) النظام الإنشائي (الهيكل الرئيسي)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "RC frame (columns + beams + slabs)",
             "هيكل خرساني (أعمدة + كمرات + بلاطات)",
             "Flexible layouts, easy future modifications, and good overall performance.",
             "مرونة بالتقسيمات وسهولة التعديل مستقبلاً وأداء إنشائي جيد."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Load-bearing walls (only for low-rise and proper wall thickness/details)",
             "حوائط حاملة (فقط للمباني الواطئة ومع سماكات وتفاصيل صحيحة)",
             "Allowed for small residential buildings if lateral stability and openings are controlled.",
             "مسموح للمباني الصغيرة إذا تم ضبط الاستقرار الجانبي والفتحات."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Random mixed systems without detailing (weak connections)",
             "أنظمة مختلطة عشوائية بدون تفاصيل ربط",
             "Creates weak load paths and cracking; unsafe behavior under lateral loads.",
             "يسبب مسارات حمل ضعيفة وتشققات وسلوك غير آمن تحت الأحمال الجانبية."),
        ],
        height=300
    )

    # =========================================================
    # 3) External Walls (Facade / Envelope)
    # =========================================================
    render_system(
        "3) External Walls (Facade System)",
        "٣) الجدران الخارجية (الواجهة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "AAC blocks / insulated wall system (double wall where needed)",
             "طابوق AAC / نظام جدار معزول (جدار مزدوج عند الحاجة)",
             "Reduces dead load and improves thermal comfort; saves energy for cooling/heating.",
             "يقلل الأحمال الميتة ويحسن الراحة الحرارية ويوفر طاقة التبريد/التدفئة."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Hollow block + added insulation layer",
             "بلوك مفرغ + طبقة عزل إضافية",
             "OK if insulation and moisture protection layers are properly applied.",
             "مقبول إذا تم تنفيذ العزل والحماية من الرطوبة بشكل صحيح."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Single wythe wall with no insulation in hot climates",
             "جدار طبقة واحدة بدون عزل بالبيئات الحارة",
             "Causes overheating and high energy cost; poor indoor comfort.",
             "يسبب حرارة داخلية وكلفة تشغيل عالية وراحة منخفضة."),
        ],
        height=300
    )

    # =========================================================
    # 4) Internal Partitions (Walls)
    # =========================================================
    render_system(
        "4) Internal Partitions (Walls)",
        "٤) القواطع الداخلية (الجدران)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Drywall partitions + acoustic insulation where needed",
             "قواطع جبس بورد + عزل صوتي عند الحاجة",
             "Fast, clean, and flexible; supports good acoustic performance for bedrooms.",
             "سريع ونظيف ومرن؛ يعطي عزل صوتي جيد لغرف النوم."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Hollow block internal walls (wet areas / high impact zones)",
             "بلوك مفرغ داخلي (للمناطق الرطبة/مناطق الصدمات)",
             "Use in bathrooms/kitchens for tiles and fixtures, but avoid excess weight everywhere.",
             "يستخدم بالحمامات/المطابخ للسيراميك والملحقات مع تجنب زيادة الوزن بكل البيت."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "AAC as main load-bearing walls without proper structural design",
             "استخدام AAC كحوائط حاملة بدون تصميم إنشائي",
             "Not suitable as primary load-bearing without engineered detailing and verification.",
             "غير مناسب كحامل رئيسي بدون تفاصيل هندسية وتحقق إنشائي."),
        ],
        height=320
    )

    # =========================================================
    # 5) Roof System & Waterproofing
    # =========================================================
    render_system(
        "5) Roof System & Waterproofing",
        "٥) السقف والعزل المائي",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "RC roof slab + multi-layer waterproofing membrane + insulation",
             "بلاطة سقف خرسانية + عزل مائي متعدد الطبقات + عزل حراري",
             "Prevents leakage and reduces heat gain; improves durability and comfort.",
             "يمنع التسرب ويقلل اكتساب الحرارة ويحسن الديمومة والراحة."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Single waterproofing layer (only with excellent slope/drainage and QC)",
             "طبقة عزل واحدة (فقط مع ميول وتصريف ممتاز وضبط جودة)",
             "Acceptable only if detailing at drains/parapets is perfect.",
             "مقبول فقط إذا كانت تفاصيل المصارف والبارابيت مثالية."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No waterproofing / direct finishes on roof slab",
             "بدون عزل مائي / تشطيب مباشر فوق الخرسانة",
             "High leakage risk leading to mold, corrosion, and interior damage.",
             "خطر تسرب عالي يسبب عفن وصدأ وتلف داخلي."),
        ],
        height=300
    )

    # =========================================================
    # 6) Flooring (Wet / Dry)
    # =========================================================
    render_system(
        "6) Flooring (Wet & Dry Areas)",
        "٦) الأرضيات (الرطبة والجافة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Porcelain / anti-slip ceramic for wet areas + parquet/LVT for dry areas",
             "بورسلان/سيراميك مانع انزلاق للرطبة + باركيه/فينيل جاف للمناطق الجافة",
             "Right material per zone: slip safety in wet areas and comfort/acoustics in bedrooms/living.",
             "اختيار مناسب لكل منطقة: أمان انزلاق بالرطبة وراحة/عزل صوتي بالجافة."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Marble (limited zones, non-polished where slip risk exists)",
             "رخام (بمناطق محدودة وغير مصقول عند خطر الانزلاق)",
             "Use only where maintenance and slip control are manageable.",
             "يستخدم فقط عند إمكانية الصيانة وضبط الانزلاق."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Carpet in bathrooms/kitchens",
             "موكيت في الحمامات/المطابخ",
             "Absorbs moisture and odors; hygiene and mold risk.",
             "يمتص الرطوبة والروائح؛ خطر عفن ونظافة ضعيفة."),
        ],
        height=320
    )

    # =========================================================
    # 7) Doors & Windows
    # =========================================================
    render_system(
        "7) Doors & Windows",
        "٧) الأبواب والنوافذ",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "UPVC / aluminum thermal break windows + quality seals",
             "نوافذ UPVC / ألمنيوم حراري مع جوانات جيدة",
             "Improves thermal comfort and reduces air leakage/dust entry.",
             "يحسن الراحة الحرارية ويقلل تسرب الهواء/الغبار."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Timber doors (indoor) with moisture protection",
             "أبواب خشب (داخلية) مع حماية رطوبة",
             "OK indoors if humidity is controlled; avoid wet exposure.",
             "مقبولة داخلياً إذا كانت الرطوبة مسيطَر عليها وتجنب الماء."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Unsealed cheap windows in hot/dusty climates",
             "نوافذ رديئة بدون إحكام بالبيئات الحارة/المغبرة",
             "Causes heat gain and dust infiltration; poor living quality.",
             "تسبب حرارة ودخول غبار؛ جودة سكن ضعيفة."),
        ],
        height=300
    )

    # =========================================================
    # 8) Fire Safety (Basic)
    # =========================================================
    render_system(
        "8) Fire Safety (Residential Basics)",
        "٨) السلامة من الحريق (أساسيات السكن)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Fire-rated doors for stairs + smoke alarms + safe electrical conduits",
             "أبواب مقاومة للحريق للدرج + كواشف دخان + مواسير كهرباء آمنة",
             "Improves evacuation safety and reduces ignition/spread risk.",
             "يرفع أمان الإخلاء ويقلل خطر الاشتعال والانتشار."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Standard doors (only for non-critical internal rooms)",
             "أبواب اعتيادية (فقط لغرف داخلية غير حرجة)",
             "Acceptable away from escape routes; ensure proper hardware.",
             "مقبولة بعيداً عن مسارات الهروب مع تثبيت ملحقات مناسبة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Exposed wiring / non-standard electrical installations",
             "أسلاك مكشوفة/تنفيذ كهرباء غير نظامي",
             "Major fire hazard; unacceptable for any residential building.",
             "خطر حريق كبير؛ غير مقبول لأي سكن."),
        ],
        height=320
    )

def run_school_advisor_ui(render_system):
    import streamlit as st

    st.markdown("### School Materials Decisions")
    st.markdown("قرارات مواد مشروع المدرسة")
    st.markdown("---")

    # =========================================================
    # A) Substructure (Foundations / Ground moisture)
    # =========================================================
    render_system(
        "1) Foundations (Typical School Blocks)",
        "١) الأساسات (مباني المدرسة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "RC Isolated/Strip Footings + DPM", "قواعد منفصلة/شريطية خرسانية + عزل رطوبة (DPM)",
             "Fits typical classroom loads; DPM prevents rising damp that ruins finishes and indoor air quality.",
             "مناسب لأحمال الصفوف؛ عزل الرطوبة يمنع الرطوبة الصاعدة التي تتلف التشطيبات وتؤثر على جودة الهواء."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Raft Foundation", "لبشة خرسانية",
             "Only if soil is weak/variable or settlement risk is high across the site.",
             "فقط إذا التربة ضعيفة/متغيرة أو خطر الهبوط عالي على كامل الموقع."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No moisture protection at ground contact", "بدون حماية رطوبة عند تماس التربة",
             "Leads to dampness, mold and repeated maintenance—unacceptable for schools.",
             "يسبب رطوبة وعفن وصيانة متكررة—غير مقبول للمدارس."),
        ],
        height=360
    )

    render_system(
        "2) Wet Areas Waterproofing (Toilets / Wash Zones)",
        "٢) عزل المناطق الرطبة (الحمامات/مغاسل)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Cementitious waterproofing + proper slope + floor drain", "عزل إسمنتي + ميول صحيحة + مصرف أرضي",
             "Most practical under tiles; with correct slopes it prevents leakage to classrooms below.",
             "الأكثر عمليّة تحت التبليط؛ ومع ميول صحيحة يمنع التسرب للأماكن المجاورة."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Bituminous membrane under screed", "غشاء بيتوميني تحت المونة/السcreed",
             "Works if protected against puncture and detailing around drains is perfect.",
             "ينجح إذا تم حمايته من الثقب وكانت تفاصيل المصارف ممتازة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Tiles without waterproofing layer", "تبليط بدون طبقة عزل",
             "Grout joints leak over time; causes hidden damage and odors.",
             "الفواصل تتسرب مع الوقت؛ تسبب تلف مخفي وروائح."),
        ],
        height=360
    )

    # =========================================================
    # B) Structural System (General for school)
    # =========================================================
    render_system(
        "3) Structural System (School: Safety & Regularity)",
        "٣) النظام الإنشائي (المدرسة: أمان وانتظام)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "RC Frame with good detailing + shear walls where needed", "هيكل خرسانة مسلحة + جدران قص عند الحاجة",
             "Provides predictable behavior and safe evacuation routes; better stiffness control in corridors/stairs.",
             "سلوك إنشائي متوقع ومسارات إخلاء آمنة؛ سيطرة أفضل على الصلابة بالممرات والسلالم."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Steel frame for halls / gyms", "هيكل فولاذي للصالات/الرياضة",
             "Excellent for long spans but needs fire protection and corrosion control plan.",
             "ممتاز للفضاءات الكبيرة لكن يحتاج حماية حريق وخطة تآكل/صيانة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Load bearing walls for multi-bay school blocks", "حوائط حاملة لمباني مدرسة متعددة البحور",
             "Limits flexibility and openings; poor performance with future modifications and services.",
             "يقيّد المرونة والفتحات؛ ضعيف مع التعديلات المستقبلية وتمديدات الخدمات."),
        ],
        height=380
    )

    # =========================================================
    # C) Classrooms (Floors / Walls / Ceilings)
    # =========================================================
    render_system(
        "4) Classroom Flooring (Low slip + Easy cleaning)",
        "٤) أرضيات الصفوف (مانع انزلاق + سهل تنظيف)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "LVT / Vinyl tiles (commercial grade)", "فينيل بلاطات (درجة تجارية)",
             "Reduces noise from chairs, warm underfoot, easy cleaning, quick replacement of damaged tiles.",
             "يقلل ضجيج الكراسي، مريح، سهل التنظيف، وسهل تبديل البلاطات المتضررة."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Porcelain tiles (mat finish, anti-slip)", "بورسلين مطفي مانع انزلاق",
             "Durable but noisier; requires good skirting and joint detailing to avoid dirt accumulation.",
             "متحمل لكن أكثر ضجيجاً؛ يحتاج نعلة وتفاصيل فواصل جيدة لتجنب تجمع الأوساخ."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Polished marble / glossy ceramic in classrooms", "رخام مصقول/سيراميك لامع في الصفوف",
             "Slip risk and glare; not suitable for high student traffic.",
             "خطر انزلاق وبهر؛ غير مناسب لحركة الطلبة."),
        ],
        height=380
    )

    render_system(
        "5) Classroom Walls (Impact resistance + Maintainability)",
        "٥) جدران الصفوف (مقاومة صدمات + صيانة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Blockwork / RC walls + washable paint", "بلوك/خرسانة + صبغ قابل للغسل",
             "Withstands student impact; washable paint reduces maintenance and keeps hygiene.",
             "يتحمل صدمات الطلبة؛ الصبغ القابل للغسل يقلل الصيانة ويحافظ على النظافة."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Drywall partitions with impact boards", "جبس بورد مع ألواح مقاومة للصدمات",
             "OK for admin zones; must use reinforced boards and corner guards in student areas.",
             "مقبول للإدارة؛ يجب استخدام ألواح مقواة وزوايا حماية في مناطق الطلبة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Standard drywall in high-traffic student corridors", "جبس بورد عادي في ممرات الطلبة",
             "Damages quickly; frequent repairs and poor lifecycle cost.",
             "يتضرر بسرعة؛ صيانة متكررة وتكلفة تشغيلية عالية."),
        ],
        height=380
    )

    render_system(
        "6) Classroom Ceilings (Access + Acoustic)",
        "٦) أسقف الصفوف (وصول للخدمات + صوت)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Acoustic ceiling tiles (lay-in) + access grid", "سقف صوتي بلاطات + شبكة وصول",
             "Improves speech clarity and reduces reverberation; easy access for lighting/HVAC maintenance.",
             "يحسن وضوح الصوت ويقلل الصدى؛ وصول سهل لصيانة الإنارة والتكييف."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Gypsum ceiling with access panels", "سقف جبس مع فتحات صيانة",
             "Works if enough access panels are planned; otherwise maintenance becomes costly.",
             "ينجح إذا خُطط لفتحات صيانة كافية؛ غير ذلك الصيانة تصبح مكلفة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No ceiling (exposed services) in classrooms", "بدون سقف (خدمات مكشوفة) في الصفوف",
             "Noise and visual clutter; not suitable for learning environment.",
             "ضجيج وتشويش بصري؛ غير مناسب لبيئة تعليمية."),
        ],
        height=380
    )

    # =========================================================
    # D) Corridors / Stairs (Safety)
    # =========================================================
    render_system(
        "7) Corridors Flooring (High traffic + Safety)",
        "٧) أرضيات الممرات (تحمل عالي + أمان)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Terrazzo or heavy-duty porcelain (anti-slip)", "تيرازو أو بورسلين عالي التحمل (مانع انزلاق)",
             "Best lifecycle for constant student traffic; resistant to abrasion and easy to clean.",
             "أفضل عمر تشغيلي لحركة الطلبة؛ مقاوم للاهتراء وسهل التنظيف."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Vinyl sheet with welded seams", "فينيل رول مع لحام الفواصل",
             "Good safety but needs excellent substrate and edge protection at corners.",
             "جيد للأمان لكن يحتاج تحضير سطح ممتاز وحماية حواف عند الزوايا."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Glossy ceramic in corridors", "سيراميك لامع في الممرات",
             "High slip risk during cleaning and rainy shoes.",
             "خطر انزلاق عالي أثناء التنظيف ومع أحذية مبللة."),
        ],
        height=380
    )

    render_system(
        "8) Staircases & Handrails (Critical safety)",
        "٨) السلالم والدرابزين (أمان حرج)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "RC stairs + anti-slip nosing + continuous handrails", "سلالم خرسانية + حافة مانعة انزلاق + درابزين مستمر",
             "Prevents falls; nosing improves grip; continuous handrails support children movement.",
             "يمنع السقوط؛ الحافة تزيد التماسك؛ الدرابزين المستمر يخدم الأطفال."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Steel stairs (protected) for secondary exits", "سلالم فولاذية (محميّة) للمخارج الثانوية",
             "Requires fire protection and anti-corrosion detailing.",
             "تحتاج حماية حريق وتفاصيل مقاومة تآكل."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No handrails / short handrails", "بدون درابزين/درابزين قصير",
             "Unacceptable for school codes and child safety.",
             "غير مقبول وفق اشتراطات المدارس وأمان الأطفال."),
        ],
        height=380
    )

    # =========================================================
    # E) Toilets / Wash zones
    # =========================================================
    render_system(
        "9) Toilets Finishes (Hygiene + Durability)",
        "٩) تشطيبات الحمامات (نظافة + ديمومة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Anti-slip porcelain + epoxy grout + cement board partitions", "بورسلين مانع انزلاق + ترويبة إيبوكسي + ألواح أسمنتية",
             "Epoxy grout reduces staining; cement board resists moisture and supports tiles.",
             "ترويبة الإيبوكسي تقلل التصبغ؛ الألواح الأسمنتية مقاومة للرطوبة وتدعم التبليط."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Ceramic tiles + high quality waterproof grout", "سيراميك + ترويبة عزل جيدة",
             "Works if cleaning schedule is strict and waterproofing is perfect.",
             "تنجح مع تنظيف منتظم وعزل ممتاز."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Standard gypsum board in toilets", "جبس بورد عادي في الحمامات",
             "Absorbs moisture and fails; leads to mold and damage.",
             "يمتص الرطوبة ويفشل؛ يسبب عفن وتلف."),
        ],
        height=400
    )

    # =========================================================
    # F) Science Labs / Computer rooms / Library
    # =========================================================
    render_system(
        "10) Science Labs (Chemical resistance)",
        "١٠) مختبرات العلوم (مقاومة كيميائية)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Epoxy flooring + chemical-resistant wall finish", "أرضية إيبوكسي + دهان مقاوم كيميائياً",
             "Handles spills and repeated cleaning; reduces damage and slip risk when detailed correctly.",
             "يتحمل الانسكابات والتنظيف المتكرر؛ يقلل التلف وخطر الانزلاق مع تفاصيل صحيحة."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Heavy-duty porcelain + sealed joints", "بورسلين قوي + فواصل محكمة",
             "Acceptable if joints are sealed and maintenance is enforced.",
             "مقبول إذا الفواصل محكمة والصيانة مستمرة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Wood/laminate flooring in labs", "خشب/لامينيت في المختبر",
             "Absorbs chemicals and moisture; fails quickly and becomes unsafe.",
             "يمتص مواد كيميائية ورطوبة؛ يفشل بسرعة ويصبح غير آمن."),
        ],
        height=400
    )

    render_system(
        "11) Library / Quiet Zones (Acoustic comfort)",
        "١١) المكتبة/مناطق هادئة (راحة صوتية)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Carpet tiles (commercial) + acoustic ceiling", "موكيت بلاطات تجاري + سقف صوتي",
             "Reduces noise significantly and improves concentration; modular replacement for damaged tiles.",
             "يقلل الضوضاء بشكل كبير ويحسن التركيز؛ يمكن تبديل البلاطات المتضررة بسهولة."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "LVT + acoustic underlay", "فينيل + طبقة عزل صوتي",
             "Good compromise if carpet is not desired; ensure proper underlay selection.",
             "حل وسط جيد إذا لا ترغب بالموكيت؛ اختر طبقة عزل مناسبة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Hard glossy tiles with no acoustic treatment", "بلاط صلب لامع بدون معالجة صوتية",
             "High reverberation makes the space noisy and unsuitable for learning.",
             "يرفع الصدى ويجعل المكان مزعج وغير مناسب للتعلم."),
        ],
        height=400
    )

    # =========================================================
    # G) Doors (classrooms / exits)
    # =========================================================
    render_system(
        "12) Doors (Classrooms vs Exits)",
        "١٢) الأبواب (الصفوف مقابل مخارج الطوارئ)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Solid core doors + kick plates; fire-rated doors for exits", "أبواب مصمتة + صفائح حماية؛ أبواب مقاومة حريق للمخارج",
             "Solid core resists abuse; fire-rated doors secure safe evacuation routes.",
             "المصمتة تتحمل الاستخدام العنيف؛ أبواب الحريق تؤمن مسارات الإخلاء."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Hollow core doors for admin-only zones", "أبواب مفرغة للإدارة فقط",
             "Only in low-traffic areas; add edge protection to reduce damage.",
             "فقط بمناطق قليلة الحركة؛ أضف حماية للحواف."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Glass doors in high-traffic student routes", "أبواب زجاجية بممرات الطلبة",
             "Breakage risk and injury hazard; not suitable for crowd movement.",
             "خطر كسر وإصابات؛ غير مناسب لحركة تجمعات الطلبة."),
        ],
        height=400
    )

    # =========================================================
    # H) Lighting (materials-level decisions)
    # =========================================================
    render_system(
        "13) Lighting (Classrooms & Corridors)",
        "١٣) الإنارة (الصفوف والممرات)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "LED panels with diffusers + emergency lighting", "ألواح LED مع ناشر + إنارة طوارئ",
             "Uniform glare control improves learning; emergency lighting is essential for safe evacuation.",
             "توزيع ضوء متجانس يقلل البهر؛ إنارة الطوارئ ضرورية للإخلاء."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "LED battens / downlights", "لمبات خطية LED / سبوتات",
             "Use where ceiling layout needs it; avoid harsh glare and ensure proper spacing.",
             "تستخدم حسب توزيع السقف؛ تجنب البهر وحقق تباعد صحيح."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Poor quality flickering lamps", "مصابيح رديئة تسبب وميض",
             "Flicker increases eye strain and reduces concentration.",
             "الوميض يزيد إجهاد العين ويقلل التركيز."),
        ],
        height=400
    )

    # =========================================================
    # I) External Works (yards, walkways, parking, playground)
    # =========================================================
    render_system(
        "14) School Yard & Walkways (Safety + Repairability)",
        "١٤) الساحات والممرات الخارجية (أمان + سهولة صيانة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Interlocking concrete pavers + proper subbase", "إنترلوك خرساني + طبقات تأسيس صحيحة",
             "Slip-resistant and repairable; easy to lift and re-lay after utilities work.",
             "مانع انزلاق وقابل للصيانة؛ يسهل فكّه وإعادته بعد أعمال الخدمات."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Broom-finished concrete slabs", "خرسانة نهائي فرشاة",
             "Good durability if joints and curing are controlled; less repair-friendly than pavers.",
             "متحملة مع ضبط الفواصل والمعالجة؛ لكنها أصعب إصلاحاً من الإنترلوك."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Glossy tiles outdoors", "تبليط لامع بالخارج",
             "Extremely slippery when wet; hazardous for children.",
             "ينزلق بشدة عند البلل؛ خطر على الأطفال."),
        ],
        height=400
    )

    render_system(
        "15) Playground Surfaces (Child Safety)",
        "١٥) أرضيات ساحة الألعاب (أمان الأطفال)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Rubber safety tiles / EPDM surface", "بلاطات مطاط أمان / سطح EPDM",
             "Impact-absorbing surface reduces injury risk from falls.",
             "يمتص الصدمات ويقلل خطر الإصابات عند السقوط."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Natural grass with drainage & maintenance", "عشب طبيعي مع تصريف وصيانة",
             "Acceptable if maintained; becomes muddy/slippery without drainage.",
             "مقبول مع صيانة؛ يتحول لوحل/انزلاق بدون تصريف."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Bare concrete/asphalt in play zones", "خرسانة/أسفلت مكشوف بساحة الألعاب",
             "High injury risk and excessive heat in summer.",
             "خطر إصابات عالي وسخونة شديدة صيفاً."),
        ],
        height=420
    )

    # =========================================================
    # J) Fire Safety (materials-level only)
    # =========================================================
    render_system(
        "16) Fire Safety (Egress & Materials)",
        "١٦) السلامة من الحريق (المخارج والمواد)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Fire-rated doors for exits + fire-stopping at penetrations", "أبواب مقاومة حريق للمخارج + سدّات حريق للفتحات",
             "Protects escape routes and prevents smoke spread through service penetrations.",
             "يحمي مسارات الإخلاء ويمنع انتقال الدخان عبر فتحات الخدمات."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Standard materials with strict compartmentation", "مواد اعتيادية مع تقسيم حريق صارم",
             "Works only if compartments and smoke control are properly detailed.",
             "تنجح فقط إذا تقسيم الحريق والسيطرة على الدخان منفذة بدقة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Exposed foam insulation without protection", "فوم عزل مكشوف بدون حماية",
             "Fire hazard; must be protected with appropriate coverings/systems.",
             "خطر حريق؛ يجب تغطيته بأنظمة حماية مناسبة."),
        ],
        height=420
    )

def run_commercial_advisor_ui(render_system):
    import streamlit as st

    st.markdown("### Commercial Materials Decisions")
    st.markdown("قرارات مواد مشروع تجاري (مول/محلات/مكاتب)")
    st.markdown("---")

    # =========================================================
    # A) Substructure (Foundations / Ground moisture)
    # =========================================================
    render_system(
        "1) Foundations (Commercial Loads & Flexibility)",
        "١) الأساسات (أحمال تجارية + مرونة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "RC footing/raft as per soil + DPM + proper drainage", "قواعد/لبشة حسب التربة + عزل رطوبة (DPM) + تصريف",
             "Commercial spaces face higher live loads and frequent re-fit; moisture control protects finishes and MEP zones.",
             "المشاريع التجارية أحمالها أعلى وتتعرض لتغييرات؛ ضبط الرطوبة يحمي التشطيبات ومناطق الخدمات."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Raft foundation (thickened) for weak soil", "لبشة مُدعّمة للتربة الضعيفة",
             "Use only when bearing capacity is low or differential settlement risk is high.",
             "تستخدم فقط عند ضعف تحمل التربة أو خطر هبوط تفاضلي عالي."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Ignoring ground waterproofing near basements", "إهمال عزل المناطق القريبة من القبو/البدروم",
             "Leads to leakage, mold, and repeated shutdown/repairs—high operational loss.",
             "يسبب تسرب وعفن وإيقاف وصيانة متكررة—خسارة تشغيلية كبيرة."),
        ],
        height=380
    )

    render_system(
        "2) Basement / Retaining Walls Waterproofing",
        "٢) عزل البدروم/الجدران الساندة",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Membrane waterproofing + protection board + drainage layer", "غشاء عزل + لوح حماية + طبقة تصريف",
             "Basements are high-risk for water ingress; drainage relieves hydrostatic pressure and protects interiors.",
             "البدرومات معرضة للتسرب؛ التصريف يقلل ضغط الماء ويحمي المساحات الداخلية."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Cementitious waterproofing (internal) + crack injection plan", "عزل إسمنتي داخلي + خطة حقن شقوق",
             "Acceptable only for low water table and with strict crack control and maintenance access.",
             "مقبول فقط مع منسوب ماء منخفض وضبط شقوق وإتاحة صيانة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No drainage for retaining walls", "بدون تصريف للجدار الساند",
             "Water pressure builds up causing leakage and structural distress over time.",
             "يتراكم ضغط الماء ويسبب تسرب ومشاكل إنشائية مع الزمن."),
        ],
        height=400
    )

    # =========================================================
    # B) Structural System (Commercial spans / change of use)
    # =========================================================
    render_system(
        "3) Structural System (Retail Flexibility)",
        "٣) النظام الإنشائي (مرونة تجارية)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "RC frame / composite systems for open plans", "هيكل خرسانة/أنظمة مركبة للمساحات المفتوحة",
             "Retail needs open bays and future reconfiguration; frames allow flexible partitions and services.",
             "المشروع التجاري يحتاج فضاءات مفتوحة وتعديل مستقبلي؛ الإطارات تسمح بقواطع وخدمات مرنة."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Steel frame for malls/large spans with fire protection", "هيكل فولاذي لفضاءات كبيرة مع حماية حريق",
             "Excellent for long spans but requires certified fireproofing and corrosion control plan.",
             "ممتاز للبحور الطويلة لكن يحتاج حماية حريق معتمدة وخطة تآكل."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Load-bearing walls for multi-tenant retail", "حوائط حاملة لمشروع تجاري متعدد المحلات",
             "Restricts openings and future tenant changes; incompatible with MEP routing and flexibility.",
             "يقيّد الفتحات وتغيير المستأجرين؛ غير مناسب لمرونة الخدمات."),
        ],
        height=380
    )

    # =========================================================
    # C) Floors (Retail / corridors / food court / parking)
    # =========================================================
    render_system(
        "4) Retail & Corridor Flooring (High Traffic)",
        "٤) أرضيات المحلات والممرات (حركة عالية)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Full-body porcelain (anti-slip) / terrazzo in main corridors", "بورسلين Full Body مانع انزلاق / تيرازو للممرات",
             "Resists abrasion from constant foot traffic and cleaning machines; long lifecycle and good appearance.",
             "مقاوم للاهتراء مع حركة دائمة وآلات تنظيف؛ عمر تشغيلي طويل ومظهر جيد."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Polished porcelain in low-risk zones", "بورسلين لامع بمناطق محددة",
             "Only if slip risk is controlled and cleaning protocol avoids wet/gloss hazards.",
             "فقط إذا تم ضبط الانزلاق وبروتوكول التنظيف يمنع المخاطر."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Glossy ceramic in entrances", "سيراميك لامع عند المداخل",
             "Wet shoes + glossy finish = high slip accidents and liability.",
             "أحذية مبللة + سطح لامع = حوادث انزلاق ومسؤولية قانونية."),
        ],
        height=400
    )

    render_system(
        "5) Food Court / Kitchens Flooring (Wet & Hygiene)",
        "٥) أرضيات الفودكورت/المطابخ (رطوبة + نظافة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Anti-slip tiles + epoxy grout + proper floor drains", "تبليط مانع انزلاق + ترويبة إيبوكسي + مصارف",
             "Grease and water demand anti-slip and stain resistance; epoxy grout reduces bacteria and discoloration.",
             "الدهون والماء تتطلب منع انزلاق ومقاومة تصبغ؛ الإيبوكسي يقلل البكتيريا وتغير اللون."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Epoxy flooring system", "نظام أرضية إيبوكسي",
             "Works well if substrate prep is perfect and mechanical impact is controlled.",
             "ينجح إذا تحضير السطح ممتاز وتم ضبط الصدمات الميكانيكية."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Wood/laminate in wet service areas", "خشب/لامينيت بمناطق رطبة",
             "Swells and fails; hygiene and slip risks increase significantly.",
             "ينتفخ ويفشل؛ يزيد مخاطر النظافة والانزلاق."),
        ],
        height=420
    )

    render_system(
        "6) Parking Floors (Ramps & Basements)",
        "٦) أرضيات المواقف (منحدرات/بدروم)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Broom-finished concrete + anti-slip ramp coating", "خرسانة نهائي فرشاة + طلاء مانع انزلاق للرامبات",
             "Provides traction for vehicles and pedestrians; withstands tire abrasion and oils.",
             "يوفر تماسك للمركبات والمشاة؛ يتحمل احتكاك الإطارات والزيوت."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Epoxy/polyurethane coating system", "إيبوكسي/بولي يوريثان",
             "Good chemical resistance but needs maintenance plan and careful detailing at joints.",
             "مقاومة كيميائية جيدة لكن تحتاج خطة صيانة وتفاصيل فواصل دقيقة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Smooth polished concrete in ramps", "خرسانة ملساء مصقولة في المنحدرات",
             "High slip risk with water/oil; unsafe during peak use.",
             "خطر انزلاق عالي مع ماء/زيت؛ غير آمن وقت الذروة."),
        ],
        height=420
    )

    # =========================================================
    # D) Walls / Partitions / Shopfronts
    # =========================================================
    render_system(
        "7) Partitions (Tenants & Services)",
        "٧) القواطع (محلات وخدمات)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Drywall partitions (double layer) + rockwool in key zones", "جبس بورد (طبقتين) + صوف صخري",
             "Fast reconfiguration for tenants; rockwool improves acoustic comfort between shops and corridors.",
             "تغيير سريع للمستأجرين؛ الصوف الصخري يحسن العزل الصوتي بين المحلات والممرات."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Block partitions for back-of-house / storage", "بلوك للخدمات/المخازن",
             "Use where impact resistance is needed; consider weight and foundation loads.",
             "يستخدم عند الحاجة لمقاومة صدمات؛ انتبه للأوزان وأحمال الأساسات."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Single-layer drywall in high-traffic service corridors", "جبس طبقة واحدة بممرات خدمات مزدحمة",
             "Damages easily and increases maintenance; poor lifecycle for commercial operations.",
             "يتضرر بسرعة ويزيد الصيانة؛ غير اقتصادي تشغيلياً."),
        ],
        height=420
    )

    render_system(
        "8) Facade / Shopfront Glazing (Safety)",
        "٨) واجهات/واجهات محلات زجاجية (أمان)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Tempered/laminated safety glass + proper framing", "زجاج سيكوريت/مصفح + إطارات صحيحة",
             "Public areas require safety glazing to reduce injury risk if broken.",
             "المناطق العامة تتطلب زجاج أمان لتقليل الإصابات عند الكسر."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Curtain wall systems with maintenance access", "كرتن وول مع وصول صيانة",
             "Allowed only with cleaning/maintenance strategy and drainage detailing.",
             "مسموح فقط مع خطة تنظيف وصيانة وتفاصيل تصريف جيدة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Ordinary annealed glass in public circulation", "زجاج عادي في مناطق عامة",
             "Breaks into sharp shards; unacceptable safety risk and liability.",
             "يتكسر لشظايا حادة؛ خطر أمان ومسؤولية عالية."),
        ],
        height=420
    )

    # =========================================================
    # E) Ceilings / MEP access / Acoustics
    # =========================================================
    render_system(
        "9) Ceilings (MEP Access + Acoustics)",
        "٩) الأسقف (وصول للخدمات + صوت)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Suspended ceiling grid + acoustic tiles in public zones", "سقف معلق شبكة + بلاطات صوتية",
             "Provides service access for HVAC/fire systems; acoustic tiles reduce noise in malls and corridors.",
             "يوفر وصول للخدمات (تكييف/إطفاء)؛ يقلل الضوضاء في الممرات والمول."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Gypsum ceiling with planned access panels", "سقف جبس مع فتحات صيانة",
             "Works if access points are sufficient; otherwise maintenance becomes costly and disruptive.",
             "ينجح إذا فتحات الصيانة كافية؛ وإلا الصيانة مكلفة ومزعجة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No ceiling with exposed services in customer areas", "بدون سقف وخدمات مكشوفة بمناطق الزبائن",
             "Visual clutter and higher noise; lowers perceived quality of commercial space.",
             "تشويش بصري وضوضاء؛ يقلل جودة المكان التجاري."),
        ],
        height=420
    )

    # =========================================================
    # F) Fire Safety (Egress / Materials-level)
    # =========================================================
    render_system(
        "10) Fire Safety (Commercial: Crowd & Liability)",
        "١٠) السلامة من الحريق (تجمعات ومسؤولية)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Fire-rated doors for exits + fire stopping + smoke control basics", "أبواب حريق للمخارج + سدّات حريق + مبادئ تحكم دخان",
             "Commercial buildings host crowds; protecting egress routes is critical to reduce fatalities and legal risk.",
             "المشاريع التجارية تستقبل تجمعات؛ حماية المخارج أساسية لتقليل الخطر والمسؤولية."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Standard partitions with strict compartmentation", "قواطع اعتيادية مع تقسيم حريق صارم",
             "Only if fire compartments and penetrations sealing are properly enforced.",
             "فقط إذا تقسيم الحريق وسدّ الفتحات منفذ بدقة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Combustible finishes in escape corridors", "تشطيبات قابلة للاشتعال بممرات الهروب",
             "Increases smoke/toxic gases; unacceptable in commercial egress routes.",
             "يزيد الدخان والغازات السامة؛ غير مقبول بممرات الإخلاء."),
        ],
        height=440
    )

    # =========================================================
    # G) Lighting (Retail comfort)
    # =========================================================
    render_system(
        "11) Lighting (Retail & Public Areas)",
        "١١) الإنارة (محلات ومناطق عامة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "LED (high efficiency) + emergency lighting + proper glare control", "LED عالي الكفاءة + طوارئ + تقليل بهر",
             "Good visual comfort improves shopping experience; emergency lighting is mandatory for safe evacuation.",
             "راحة بصرية تحسن تجربة التسوق؛ إنارة الطوارئ ضرورية للإخلاء."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Decorative lighting (feature) with base uniform lighting", "إنارة ديكورية مع إنارة أساسية",
             "Use as accent only; ensure base lighting meets safety and visibility requirements.",
             "تستخدم كإضافة فقط؛ يجب أن تحقق الإنارة الأساسية متطلبات السلامة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Flickering / low-quality lamps", "مصابيح رديئة/وميض",
             "Causes discomfort and undermines perceived quality; higher maintenance and failures.",
             "تسبب إزعاج وتقلل جودة المكان؛ أعطال وصيانة أعلى."),
        ],
        height=420
    )

    # =========================================================
    # H) External Works (entrance plazas / walkways)
    # =========================================================
    render_system(
        "12) Entrance Plazas & Walkways (Slip Safety)",
        "١٢) الساحات الخارجية والممرات (منع انزلاق)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Textured stone / anti-slip pavers + proper drainage", "حجر خشن/إنترلوك مانع انزلاق + تصريف",
             "Entrance areas get wet; texture + drainage reduces slip accidents and claims.",
             "المداخل تتعرض للبلل؛ الخشونة والتصريف يقللان حوادث الانزلاق."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Stamped concrete with non-slip finish", "خرسانة مطبوعة مع إنهاء مانع انزلاق",
             "OK if finish is truly anti-slip and maintenance keeps it clean.",
             "مقبولة إذا الإنهاء مانع انزلاق فعلاً والصيانة جيدة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Polished stone at main entrances", "حجر مصقول عند المداخل",
             "Very slippery when wet; unacceptable for public access zones.",
             "ينزلق بشدة عند البلل؛ غير مقبول للمناطق العامة."),
        ],
        height=420
    )

def run_parking_advisor_ui(render_system):
    import streamlit as st

    st.markdown("### Parking Materials Decisions")
    st.markdown("قرارات مواد مشروع مواقف السيارات")
    st.markdown("---")

    # =========================================================
    # 1) Structural System
    # =========================================================
    render_system(
        "1) Structural System (Ramps & Large Spans)",
        "١) النظام الإنشائي (منحدرات وبحور واسعة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "RC frame / post-tensioned slabs", "هيكل خرسانة أو بلاطات شد لاحق",
             "Provides long spans with fewer columns, improving circulation and parking efficiency.",
             "يوفر بحور طويلة مع أعمدة أقل، مما يحسن حركة السيارات وكفاءة المواقف."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Steel structure with fire protection", "هيكل فولاذي مع حماية حريق",
             "Works well but needs certified fireproofing and corrosion protection.",
             "فعال لكنه يحتاج حماية حريق وتآكل معتمدة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Load bearing walls", "حوائط حاملة",
             "Restricts circulation and cannot accommodate ramps and large openings.",
             "يقيّد الحركة ولا يناسب المنحدرات والفتحات الواسعة."),
        ],
        height=380
    )

    # =========================================================
    # 2) Parking Floors (Flat areas)
    # =========================================================
    render_system(
        "2) Parking Floors (Traffic & Oils)",
        "٢) أرضيات المواقف (حركة وزيوت)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Broom-finished concrete + surface hardener", "خرسانة بإنهاء فرشاة + مقسي سطح",
             "Provides traction, resists tire abrasion and oil contamination.",
             "يوفر تماسك، ويقاوم احتكاك الإطارات والزيوت."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Epoxy / PU coating system", "نظام إيبوكسي أو بولي يوريثان",
             "Good chemical resistance but needs strict surface prep and maintenance.",
             "مقاومة كيميائية جيدة لكن تحتاج تحضير سطح وصيانة دقيقة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Tiles or polished surfaces", "تبليط أو أسطح ملساء مصقولة",
             "High slip risk and joint failure under vehicle loads.",
             "خطر انزلاق عالي وفشل الفواصل تحت أحمال السيارات."),
        ],
        height=400
    )

    # =========================================================
    # 3) Ramps
    # =========================================================
    render_system(
        "3) Ramps (Safety Critical)",
        "٣) المنحدرات (عنصر أمان أساسي)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Grooved / broom-finished concrete + anti-slip coating", "خرسانة مخددة أو فرشاة + طلاء مانع انزلاق",
             "Ensures traction for vehicles and pedestrians, especially when wet.",
             "يضمن تماسك المركبات والمشاة خاصة عند البلل."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Asphalt with high-friction aggregate", "أسفلت مع ركام عالي الاحتكاك",
             "Acceptable only with proper drainage and frequent maintenance.",
             "مقبول فقط مع تصريف جيد وصيانة دورية."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Smooth concrete or tiles", "خرسانة ملساء أو بلاط",
             "Extremely slippery and unsafe on slopes.",
             "خطير جداً ويسبب انزلاق شديد على المنحدرات."),
        ],
        height=400
    )

    # =========================================================
    # 4) Waterproofing (Basement Parking)
    # =========================================================
    render_system(
        "4) Waterproofing (Basements)",
        "٤) العزل المائي (المواقف السفلية)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Membrane waterproofing + drainage layer", "غشاء عزل + طبقة تصريف",
             "Prevents leakage and protects structure and vehicles from moisture.",
             "يمنع التسرب ويحمي الهيكل والسيارات من الرطوبة."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Cementitious internal waterproofing", "عزل إسمنتي داخلي",
             "Only for low water table and with crack injection strategy.",
             "فقط مع منسوب ماء منخفض وخطة حقن شقوق."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No waterproofing system", "بدون نظام عزل",
             "Leads to chronic leakage, corrosion, and service shutdown.",
             "يسبب تسرب دائم وصدأ وتوقف تشغيلي."),
        ],
        height=400
    )

    # =========================================================
    # 5) Fire Safety
    # =========================================================
    render_system(
        "5) Fire Safety (Life Safety)",
        "٥) السلامة من الحريق (حماية الأرواح)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Fire-rated walls + smoke ventilation + fire doors", "جدران مقاومة حريق + تهوية دخان + أبواب حريق",
             "Vehicle fires generate heavy smoke; compartmentation and ventilation are essential.",
             "حرائق السيارات تولد دخان كثيف؛ التقسيم والتهوية ضروريان."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Open parking with natural ventilation", "موقف مفتوح بتهوية طبيعية",
             "Acceptable only if code allows and openings are sufficient.",
             "مقبول فقط إذا الكود يسمح والفتحات كافية."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No smoke control strategy", "بدون نظام تحكم بالدخان",
             "Extremely dangerous for evacuation and firefighting.",
             "خطير جداً على الإخلاء والإطفاء."),
        ],
        height=420
    )

    # =========================================================
    # 6) Lighting
    # =========================================================
    render_system(
        "6) Lighting (Visibility & Safety)",
        "٦) الإنارة (رؤية وأمان)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "LED lighting + emergency lighting", "إنارة LED + إنارة طوارئ",
             "Good visibility reduces accidents and improves user safety.",
             "رؤية جيدة تقلل الحوادث وتحسن أمان المستخدمين."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Motion-sensor lighting in low-traffic zones", "إنارة بحساس حركة بالمناطق قليلة الاستخدام",
             "Energy saving but must not create dark zones.",
             "توفر طاقة لكن يجب ألا تخلق مناطق مظلمة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Poor or uneven lighting", "إنارة ضعيفة أو غير منتظمة",
             "Increases accidents, theft risk, and user complaints.",
             "تزيد الحوادث وخطر السرقة وشكاوى المستخدمين."),
        ],
        height=400
    )

    # =========================================================
    # 7) Markings & Barriers
    # =========================================================
    render_system(
        "7) Markings & Protection",
        "٧) التخطيط والحماية",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Durable floor markings + steel bollards", "تخطيط أرضيات متين + بولاردات فولاذية",
             "Organizes traffic and protects columns and pedestrians.",
             "ينظم الحركة ويحمي الأعمدة والمشاة."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Plastic/rubber barriers", "حواجز بلاستيكية أو مطاطية",
             "Only for low-speed, low-impact zones.",
             "فقط للمناطق منخفضة السرعة والتأثير."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No protection for columns", "بدون حماية للأعمدة",
             "Vehicle impact can cause structural damage.",
             "اصطدام السيارات قد يسبب ضرر إنشائي."),
        ],
        height=400
    )

def run_warehouse_advisor_ui(render_system):
    import streamlit as st

    st.markdown("### Warehouse Materials Decisions")
    st.markdown("قرارات مواد مشروع مخزن / Warehouse")
    st.markdown("---")

    # =========================================================
    # 1) Foundations (heavy storage loads)
    # =========================================================
    render_system(
        "1) Foundations (Heavy Storage Loads)",
        "١) الأساسات (أحمال تخزين عالية)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Isolated/strip footings or raft as per soil + DPM", "قواعد منفصلة/شريطية أو لبشة حسب التربة + عزل رطوبة",
             "Warehouses have high point loads from racks; moisture control protects slabs and goods.",
             "المخازن فيها أحمال مركّزة من الرفوف؛ ضبط الرطوبة يحمي البلاطة والبضائع."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Raft foundation for weak soil", "لبشة للتربة الضعيفة",
             "Use only when bearing capacity is low or settlement risk is high.",
             "تستخدم فقط عند ضعف تحمل التربة أو وجود خطر هبوط."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Shallow poor-quality foundations without soil check", "أساسات سطحية ضعيفة بدون فحص تربة",
             "Leads to differential settlement and rack misalignment; high operational risk.",
             "يسبب هبوط تفاضلي وعدم استقامة الرفوف؛ خطر تشغيلي عالي."),
        ],
        height=380
    )

    # =========================================================
    # 2) Structural System (clear span)
    # =========================================================
    render_system(
        "2) Structural System (Clear Span & Speed)",
        "٢) النظام الإنشائي (فضاءات مفتوحة + سرعة تنفيذ)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Steel PEB / steel portal frames", "هيكل معدني PEB / إطارات بوابة",
             "Fast erection and large clear spans improve forklift circulation and storage layout.",
             "تركيب سريع وبحور واسعة تحسن حركة الرافعات وتخطيط التخزين."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "RC frame for multi-storey storage or aggressive chemicals", "هيكل خرسانة للطوابق المتعددة أو بيئات كيميائية",
             "Use when fire resistance or chemical exposure makes steel protection costly.",
             "يستخدم عندما مقاومة الحريق أو التعرض الكيميائي تجعل حماية الحديد مكلفة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Load bearing walls", "حوائط حاملة",
             "Restricts openings and clear span; not suitable for warehouse logistics.",
             "تقيّد الفتحات والفضاءات؛ غير مناسبة للوجستيات."),
        ],
        height=380
    )

    # =========================================================
    # 3) Industrial Slab / Floor (forklifts + racks)
    # =========================================================
    render_system(
        "3) Warehouse Floor Slab (Forklifts & Racks)",
        "٣) بلاطة أرضية المخزن (رافعات + رفوف)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Jointed concrete slab + surface hardener (dust-free)", "بلاطة خرسانية بفواصل + مقسي سطح (مقاوم غبار)",
             "Resists abrasion from forklifts and reduces dust that damages goods and equipment.",
             "تقاوم احتكاك الرافعات وتقلل الغبار الذي يضر البضائع والمعدات."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Fibre-reinforced slab / reduced rebar option", "بلاطة بألياف (تقليل تسليح)",
             "Works if design controls shrinkage cracking and finishing is high quality.",
             "تنجح إذا التصميم يسيطر على تشققات الانكماش والإنهاء ممتاز."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Tiles/ceramic flooring in storage halls", "تبليط/سيراميك بصالات التخزين",
             "Joints fail and tiles crack under rack/forklift loads.",
             "تفشل الفواصل ويتكسر البلاط تحت أحمال الرفوف والرافعات."),
        ],
        height=420
    )

    # =========================================================
    # 4) Racking / Impact Protection
    # =========================================================
    render_system(
        "4) Impact Protection (Racks & Columns)",
        "٤) الحماية من الصدمات (رفوف وأعمدة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Steel bollards + rack end protectors", "بولاردات فولاذية + حماية نهايات الرفوف",
             "Forklift impacts are common; protection prevents structural damage and downtime.",
             "اصطدام الرافعات شائع؛ الحماية تمنع ضرر إنشائي وتوقف العمل."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Rubber/plastic guards", "حمايات مطاطية/بلاستيكية",
             "Only for low-speed zones; not sufficient for heavy forklifts.",
             "فقط للمناطق منخفضة السرعة؛ غير كافية للرافعات الثقيلة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No impact protection", "بدون أي حماية",
             "Increases risk of column damage, rack collapse, and injuries.",
             "يزيد خطر ضرر الأعمدة وانهيار الرفوف والإصابات."),
        ],
        height=420
    )

    # =========================================================
    # 5) Building Envelope (roof/walls insulation)
    # =========================================================
    render_system(
        "5) Envelope (Thermal & Condensation Control)",
        "٥) الغلاف الخارجي (عزل + منع تكثف)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Sandwich panels (roof/walls) with proper sealing", "ساندوتش بانل للسقف والجدران مع إحكام",
             "Controls heat gain and prevents condensation that damages stored goods.",
             "يقلل الحرارة ويمنع التكثف الذي يضر البضائع المخزنة."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Single-skin sheet + insulation layer", "صاج مفرد + طبقة عزل",
             "Acceptable only with vapor barrier and ventilation strategy.",
             "مقبول فقط مع حاجز بخار وتهوية مناسبة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No insulation in hot climates", "بدون عزل في بيئات حارة",
             "Raises internal temperature and damages inventory; high operational cost.",
             "يرفع حرارة الداخل ويضر المخزون؛ كلفة تشغيل عالية."),
        ],
        height=420
    )

    # =========================================================
    # 6) Fire Safety (warehouse = high fuel load)
    # =========================================================
    render_system(
        "6) Fire Safety (High Fuel Load)",
        "٦) السلامة من الحريق (مخزون عالي الاشتعال)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Sprinkler system readiness + fire-rated exits + compartmentation", "جاهزية مرشّات + مخارج حريق + تقسيم",
             "Warehouses store combustible goods; rapid fire spread requires strong fire strategy.",
             "المخازن تحتوي مواد قابلة للاشتعال؛ انتشار الحريق سريع ويحتاج استراتيجية قوية."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Passive fire protection only (limited)", "حماية سلبية فقط (محدودة)",
             "Only for small warehouses with controlled storage and code approval.",
             "فقط للمخازن الصغيرة مع ضبط التخزين وموافقة الكود."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Unprotected steel without fireproofing", "هيكل فولاذي بدون حماية حريق",
             "Steel loses strength quickly in fire leading to roof collapse.",
             "الحديد يفقد مقاومته بسرعة بالحريق ويؤدي لانهيار السقف."),
        ],
        height=440
    )

    # =========================================================
    # 7) Lighting (operations + safety)
    # =========================================================
    render_system(
        "7) Lighting (Operations & Safety)",
        "٧) الإنارة (تشغيل وأمان)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "High-bay LED + emergency lighting", "LED High-Bay + إنارة طوارئ",
             "Improves visibility for forklifts and reduces accidents; efficient energy use.",
             "تحسن الرؤية للرافعات وتقلل الحوادث؛ كفاءة طاقة عالية."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Skylights with glare control", "سكاي لايت مع تقليل بهر",
             "Good daylighting but must control heat and glare; ensure maintenance access.",
             "إنارة نهارية جيدة لكن يجب ضبط الحرارة والبهر مع صيانة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Low / uneven lighting", "إنارة ضعيفة أو غير منتظمة",
             "Causes forklift accidents and operational errors.",
             "تسبب حوادث رافعات وأخطاء تشغيل."),
        ],
        height=420
    )

    # =========================================================
    # 8) Drainage & External Yard (if any)
    # =========================================================
    render_system(
        "8) External Yard & Drainage (Logistics)",
        "٨) الساحات الخارجية والتصريف (لوجستيات)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Heavy-duty pavers or concrete slab + proper drainage", "إنترلوك ثقيل أو بلاطة خرسانة + تصريف",
             "Truck traffic requires durable pavement; drainage prevents standing water and rutting.",
             "حركة الشاحنات تحتاج تبليط قوي؛ التصريف يمنع تجمع الماء والهبوط."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Asphalt in low-load areas", "أسفلت بمناطق أحمال منخفضة",
             "Only for light traffic; avoid heavy static truck loads in hot weather.",
             "فقط لحركة خفيفة؛ تجنب وقوف شاحنات ثقيلة بالصيف."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No drainage on yard", "بدون تصريف بالساحة",
             "Leads to water pooling, subgrade weakening, and pavement failure.",
             "يسبب تجمع ماء وضعف التربة وفشل التبليط."),
        ],
        height=440
    )

def run_restaurant_advisor_ui(render_system):
    import streamlit as st

    st.markdown("### Restaurant Materials Decisions")
    st.markdown("قرارات مواد مشروع مطعم / Restaurant")
    st.markdown("---")

    # =========================================================
    # 1) Structural System (open areas + flexibility)
    # =========================================================
    render_system(
        "1) Structural System (Open Dining & Flexibility)",
        "١) النظام الإنشائي (فراغات مفتوحة ومرونة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "RC frame (flexible layout)", "هيكل خرسانة (مرونة بالتقسيم)",
             "Allows open dining spaces and easy future layout changes with good vibration control.",
             "يسمح بفراغات جلوس مفتوحة وتغيير التقسيم مستقبلاً مع سيطرة جيدة على الاهتزاز."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Steel frame with fire protection", "هيكل فولاذي مع حماية حريق",
             "Works well but must include certified fireproofing and kitchen heat protection.",
             "فعال لكن يجب إضافة حماية حريق معتمدة وحماية من حرارة المطبخ."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Load bearing walls for main layout", "حوائط حاملة للتقسيم الرئيسي",
             "Restricts openings and dining circulation; difficult MEP routing.",
             "تقيّد الفتحات وحركة الزبائن؛ صعب تمرير الخدمات."),
        ],
        height=380
    )

    # =========================================================
    # 2) Kitchen Flooring (grease + wet + slip)
    # =========================================================
    render_system(
        "2) Kitchen Flooring (Grease, Water & Slip Risk)",
        "٢) أرضيات المطبخ (دهون + ماء + انزلاق)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Anti-slip porcelain / quarry tiles (R11/R12)", "بورسلين مانع انزلاق / Quarry Tiles (R11/R12)",
             "High slip resistance and low absorption; safe under oils and washing.",
             "مقاومة انزلاق عالية وامتصاص منخفض؛ آمنة مع الزيوت والغسل."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Epoxy flooring system (commercial grade)", "أرضية إيبوكسي (تجاري)",
             "Excellent hygiene but requires perfect substrate prep and periodic maintenance.",
             "نظافة ممتازة لكن تحتاج تحضير سطح قوي وصيانة دورية."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Polished marble / smooth ceramic", "رخام مصقول / سيراميك أملس",
             "Very slippery when wet/greasy; high accident risk.",
             "ينزلق جداً مع الماء والدهون؛ خطر حوادث عالي."),
        ],
        height=420
    )

    # =========================================================
    # 3) Dining Flooring (comfort + durability + cleaning)
    # =========================================================
    render_system(
        "3) Dining Flooring (Comfort & Cleanability)",
        "٣) أرضيات صالة الطعام (راحة + تنظيف + ديمومة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Porcelain tiles / LVT commercial grade", "بورسلين / فينيل LVT تجاري",
             "Durable, easy to clean, and handles moderate traffic with good aesthetics.",
             "متين وسهل تنظيف ويتحمل حركة متوسطة مع مظهر ممتاز."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Engineered wood (protected finish)", "خشب هندسي (مع حماية سطح)",
             "Good ambiance but must control moisture and use protective coatings.",
             "يعطي جو جميل لكن يجب ضبط الرطوبة واستخدام طبقات حماية."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Carpet in food areas", "موكيت بمناطق الطعام",
             "Absorbs odors and stains; hygiene and maintenance problems.",
             "يمتص الروائح والبقع؛ مشاكل نظافة وصيانة."),
        ],
        height=420
    )

    # =========================================================
    # 4) Walls & Finishes (washable + hygiene)
    # =========================================================
    render_system(
        "4) Walls & Finishes (Washable & Durable)",
        "٤) الجدران والتشطيبات (قابل للغسل ومتين)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Washable paint + ceramic wall tiles in wet zones", "صبغ قابل للغسل + تبليط جدران بالمناطق الرطبة",
             "Maintains hygiene; protects walls from splashes and frequent cleaning chemicals.",
             "يحافظ على النظافة؛ يحمي الجدران من الرش والتنظيف المتكرر."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Decorative wood panels (sealed)", "ألواح ديكور خشبية (مع عزل/سيلر)",
             "Allowed only away from heat/grease; must be sealed and easy to wipe.",
             "مسموحة بعيداً عن الحرارة والدهون؛ يجب أن تكون محكمة وسهلة المسح."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Unsealed porous finishes in kitchen", "تشطيبات مسامية غير محكمة بالمطبخ",
             "Traps grease and bacteria; difficult cleaning and odors.",
             "تحتجز دهون وبكتيريا؛ تنظيف صعب وروائح."),
        ],
        height=420
    )

    # =========================================================
    # 5) Ceiling (grease, maintenance, acoustics)
    # =========================================================
    render_system(
        "5) Ceilings (Kitchen vs Dining)",
        "٥) الأسقف (المطبخ مقابل الصالة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Kitchen: moisture-resistant ceiling | Dining: acoustic ceiling", "المطبخ: سقف مقاوم رطوبة | الصالة: سقف عازل صوت",
             "Kitchen needs washable moisture resistance; dining needs noise control for comfort.",
             "المطبخ يحتاج مقاومة رطوبة وسهولة تنظيف؛ الصالة تحتاج تقليل الضجيج للراحة."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Standard gypsum board (protected)", "جبس بورد اعتيادي (مع حماية)",
             "Only in dry areas; avoid directly above cooking zones unless protected.",
             "فقط بالمناطق الجافة؛ تجنبه فوق الطبخ إلا مع حماية."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Absorbent ceiling over greasy areas", "سقف ماص فوق مناطق الدهون",
             "Absorbs odors and grease; hygiene issues and staining.",
             "يمتص روائح ودهون؛ مشاكل نظافة وبقع."),
        ],
        height=420
    )

    # =========================================================
    # 6) Fire Safety (kitchen fire critical)
    # =========================================================
    render_system(
        "6) Fire Safety (Kitchen Critical)",
        "٦) السلامة من الحريق (المطبخ حساس)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Fire-rated doors + hood suppression + fire-resistant finishes", "أبواب حريق + نظام إطفاء الهود + مواد مقاومة",
             "Cooking fires spread fast; suppression and compartmentation are essential.",
             "حرائق الطبخ تنتشر بسرعة؛ الإطفاء والتقسيم ضروريان."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Fire-rated gypsum partitions", "قواطع جبس مقاومة حريق",
             "Allowed when certified assembly is used and all penetrations are sealed.",
             "مسموح عند استخدام نظام معتمد وإغلاق جميع الفتحات."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Open kitchen without fire control", "مطبخ مفتوح بدون تحكم حريق",
             "High risk to occupants and property; violates safety expectations.",
             "خطر عالي على الناس والممتلكات؛ غير آمن."),
        ],
        height=440
    )

    # =========================================================
    # 7) Ventilation & Grease Ducts
    # =========================================================
    render_system(
        "7) Ventilation (Grease & Odors)",
        "٧) التهوية (دهون وروائح)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Commercial hood + grease ducts + fresh air system", "هود تجاري + دكت دهون + هواء نقي",
             "Controls heat, smoke, and grease; protects interior finishes and improves comfort.",
             "يسيطر على الحرارة والدخان والدهون؛ يحمي التشطيبات ويحسن الراحة."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Recirculating hoods (limited)", "هود تدويري (محدود)",
             "Only for light cooking and with certified filtration and maintenance.",
             "فقط للطبخ الخفيف مع فلاتر معتمدة وصيانة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No grease duct strategy", "بدون حل لدكت الدهون",
             "Causes odor spread, grease deposits, and high fire risk.",
             "يسبب انتشار روائح وترسب دهون وخطر حريق."),
        ],
        height=440
    )

    # =========================================================
    # 8) Doors & Wet Areas (toilets/service)
    # =========================================================
    render_system(
        "8) Doors & Wet Areas (Toilets & Service)",
        "٨) الأبواب والمناطق الرطبة (حمامات وخدمات)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Moisture-resistant doors + stainless hardware", "أبواب مقاومة رطوبة + إكسسوارات ستانلس",
             "Resists humidity and frequent cleaning chemicals; long service life.",
             "تقاوم الرطوبة ومواد التنظيف المتكرر؛ عمر أطول."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Wood doors with sealing", "أبواب خشب مع سيلر",
             "Allowed only in dry areas; must be sealed and maintained.",
             "مسموحة بالمناطق الجافة فقط؛ تحتاج إحكام وصيانة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Untreated wood in toilets/service", "خشب غير معالج بالحمامات",
             "Swells and deforms; hygiene and durability failure.",
             "ينتفخ ويتشوه؛ فشل ديمومة ونظافة."),
        ],
        height=420
    )

    # =========================================================
    # 9) Lighting (warm dining + safe kitchen)
    # =========================================================
    render_system(
        "9) Lighting (Dining Ambience & Kitchen Safety)",
        "٩) الإنارة (جو الصالة + أمان المطبخ)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Dining: warm LED | Kitchen: high-lux task lighting", "الصالة: LED دافئ | المطبخ: إنارة عمل قوية",
             "Dining needs comfort ambience; kitchen needs visibility for safety and hygiene checks.",
             "الصالة تحتاج جو مريح؛ المطبخ يحتاج رؤية للأمان وفحص النظافة."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Decorative lighting with protective covers", "إنارة ديكور مع حماية",
             "Allowed if easy to clean and protected from grease accumulation.",
             "مسموحة إذا سهلة تنظيف ومحمية من تراكم الدهون."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Low lighting in kitchen/work zones", "إنارة ضعيفة بالمطبخ",
             "Increases accidents and reduces quality control.",
             "تزيد الحوادث وتضعف ضبط الجودة."),
        ],
        height=420
    )

    # =========================================================
    # 10) External Areas (entry, sidewalk)
    # =========================================================
    render_system(
        "10) External Entry & Walkways",
        "١٠) المداخل والممرات الخارجية",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Non-slip outdoor tiles / textured concrete", "تبليط خارجي مانع انزلاق / خرسانة خشنة",
             "Prevents slips during rain; durable under foot traffic.",
             "يمنع الانزلاق وقت المطر؛ متين لحركة المشاة."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Natural stone (textured)", "حجر طبيعي (ملمس خشن)",
             "Allowed when textured and sealed; avoid polished finishes.",
             "مسموح إذا خشن ومحكم؛ تجنب المصقول."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Polished stone at entrances", "حجر مصقول بالمداخل",
             "High slip risk in wet conditions.",
             "خطر انزلاق عالي عند البلل."),
        ],
        height=420
    )

def run_tunnel_advisor_ui(render_system):
    import streamlit as st

    st.markdown("### Tunnel Materials Decisions")
    st.markdown("قرارات مواد مشروع نفق / Tunnel")
    st.markdown("---")

    # =========================================================
    # 1) Excavation & Support (temporary works)
    # =========================================================
    render_system(
        "1) Excavation Support (Temporary Works)",
        "١) تدعيم الحفر (أعمال مؤقتة)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Shotcrete + rock bolts / lattice girders", "شوتكريت + مسامير صخرية / جسور شبكية",
             "Controls immediate ground instability and provides rapid initial lining support.",
             "يسيطر على عدم استقرار التربة/الصخر بسرعة ويوفر تدعيم أولي مباشر."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Steel ribs (heavy support)", "أضلاع فولاذية (تدعيم ثقيل)",
             "Use for weak ground zones only; higher cost and needs corrosion control.",
             "تستخدم فقط بالمناطق الضعيفة؛ كلفة أعلى وتحتاج حماية تآكل."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Unsupported excavation", "حفر بدون تدعيم",
             "High collapse risk and unsafe working conditions.",
             "خطر انهيار عالي وبيئة عمل غير آمنة."),
        ],
        height=420
    )

    # =========================================================
    # 2) Primary Lining (initial tunnel shell)
    # =========================================================
    render_system(
        "2) Primary Lining (Initial Shell)",
        "٢) البطانة الأولية (الغلاف الأولي)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Fiber-reinforced shotcrete (FRS)", "شوتكريت مسلح بالألياف",
             "Improves crack control and toughness; ideal for early-age deformation control.",
             "يحسن السيطرة على التشققات والمتانة؛ مناسب للهبوطات المبكرة."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Conventional shotcrete + mesh", "شوتكريت اعتيادي + شبك",
             "Acceptable with strict thickness control and proper curing/adhesion.",
             "مقبول مع ضبط السماكة ومعالجة ولصق صحيح."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Weak low-cement mixes", "خلطات ضعيفة قليلة الإسمنت",
             "Leads to poor bond, high permeability, and early deterioration.",
             "تؤدي لالتصاق ضعيف ونفاذية عالية وتلف مبكر."),
        ],
        height=420
    )

    # =========================================================
    # 3) Final Lining (durability + watertightness)
    # =========================================================
    render_system(
        "3) Final Lining (Durability & Watertightness)",
        "٣) البطانة النهائية (ديمومة + مانعية ماء)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "RC lining with low-permeability concrete + proper cover", "بطانة خرسانة مسلحة بخرسانة قليلة النفاذية + غطاء مناسب",
             "Final lining must resist groundwater and long-term chemical attack with durable concrete.",
             "البطانة النهائية يجب تقاوم المياه الجوفية والهجوم الكيميائي بخرسانة متينة."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Precast segmental lining", "مقاطع مسبقة الصب",
             "Excellent speed and quality but requires accurate gaskets and segment joints control.",
             "جودة وسرعة ممتازة لكن تحتاج دقة عالية في الجوانات والفواصل."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Poor cover / exposed steel", "غطاء خرساني ضعيف / حديد مكشوف",
             "Accelerates corrosion and cracking; reduces tunnel service life.",
             "يسرّع الصدأ والتشققات؛ يقلل عمر النفق."),
        ],
        height=440
    )

    # =========================================================
    # 4) Waterproofing System (membrane + drainage)
    # =========================================================
    render_system(
        "4) Waterproofing & Drainage",
        "٤) العزل المائي والتصريف",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "PVC/HDPE membrane + drainage layer + waterstops", "غشاء PVC/HDPE + طبقة تصريف + Waterstops",
             "Controls leakage and hydrostatic pressure; protects lining and reinforcement.",
             "يمنع التسرب ويخفف ضغط الماء؛ يحمي البطانة والتسليح."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Crystalline waterproofing admixture", "مضافات عزل بلورية",
             "Helps reduce permeability but not a substitute for membrane in high groundwater zones.",
             "تقلل النفاذية لكن لا تغني عن الغشاء بالمياه العالية."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No waterproofing system", "بدون نظام عزل",
             "Leads to chronic leakage, corrosion, staining, and maintenance issues.",
             "يسبب تسرب دائم وصدأ وبقع ومشاكل صيانة."),
        ],
        height=440
    )

    # =========================================================
    # 5) Joints & Seals (segment joints / construction joints)
    # =========================================================
    render_system(
        "5) Joints & Sealing",
        "٥) الفواصل والإحكام",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Hydrophilic + PVC waterstops at joints", "ووترستوب PVC + شريط متمدد (Hydrophilic)",
             "Critical to stop water paths through joints and prevent internal leakage lines.",
             "مهم لإيقاف مسارات الماء عبر الفواصل ومنع التسرب الداخلي."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Sealants only for minor joints", "سيليكون/سيلنت فقط للفواصل الصغيرة",
             "Allowed for non-pressurized minor joints; requires periodic inspection.",
             "مسموح للفواصل الصغيرة غير المضغوطة ويحتاج فحص دوري."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Leaving joints untreated", "ترك الفواصل بدون معالجة",
             "Becomes direct leakage channel and accelerates deterioration at edges.",
             "يصبح قناة تسرب مباشرة ويعجّل التلف عند الحواف."),
        ],
        height=420
    )

    # =========================================================
    # 6) Fire Safety & Lining Protection
    # =========================================================
    render_system(
        "6) Fire Safety (Tunnel Specific)",
        "٦) السلامة من الحريق (خاص بالنفق)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Fire-resistant lining protection (boards/sprays) + fire-rated doors", "حماية بطانة مقاومة حريق + أبواب حريق",
             "Tunnel fires are severe; protection preserves structural integrity and evacuation safety.",
             "حرائق الأنفاق شديدة؛ الحماية تحافظ على سلامة البطانة والإخلاء."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Concrete mix upgrade only (PP fibers)", "تحسين الخلطة فقط (ألياف PP)",
             "Helps reduce spalling but may not be sufficient alone for high-risk tunnels.",
             "تقلل تقشر الخرسانة لكنها قد لا تكفي وحدها بالأنفاق الخطرة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Unprotected surfaces in high-risk tunnel", "أسطح بدون حماية بنفق عالي الخطورة",
             "Spalling and collapse risk increases; unacceptable safety outcome.",
             "يزيد خطر التقشر والانهيار؛ غير مقبول."),
        ],
        height=460
    )

    # =========================================================
    # 7) Ventilation (smoke control)
    # =========================================================
    render_system(
        "7) Ventilation (Smoke & Air Quality)",
        "٧) التهوية (دخان وجودة هواء)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Jet fans / mechanical ventilation with smoke control", "مراوح نفاثة / تهوية ميكانيكية مع تحكم دخان",
             "Ensures smoke extraction during fire and maintains safe visibility/air quality.",
             "تسحب الدخان وقت الحريق وتحافظ على رؤية وهواء آمن."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Natural ventilation (limited cases)", "تهوية طبيعية (حالات محدودة)",
             "Only for short tunnels and open portals; must meet safety requirements.",
             "فقط للأنفاق القصيرة ومداخل مفتوحة مع تحقق متطلبات السلامة."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No ventilation strategy", "بدون استراتيجية تهوية",
             "Causes dangerous smoke accumulation and poor air quality.",
             "يسبب تراكم دخان خطير وجودة هواء سيئة."),
        ],
        height=440
    )

    # =========================================================
    # 8) Lighting & Emergency Systems
    # =========================================================
    render_system(
        "8) Lighting & Emergency Guidance",
        "٨) الإنارة وإرشاد الطوارئ",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "LED tunnel lighting + emergency backup + exit signage", "إنارة LED + طوارئ + لوحات مخارج",
             "Guides drivers and supports evacuation during incidents; high reliability.",
             "تهدي السائقين وتدعم الإخلاء وقت الطوارئ؛ اعتمادية عالية."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Standard lighting without adaptive control", "إنارة عادية بدون تحكم ذكي",
             "Acceptable in small tunnels but less efficient and less safe in transitions.",
             "مقبولة بالأنفاق الصغيرة لكنها أقل كفاءة وأمان عند المداخل."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Insufficient lighting / no emergency power", "إنارة ضعيفة / بدون طوارئ",
             "Increases accidents and makes evacuation unsafe.",
             "يزيد الحوادث ويجعل الإخلاء غير آمن."),
        ],
        height=440
    )

    # =========================================================
    # 9) Drainage Inside Tunnel (water collection)
    # =========================================================
    render_system(
        "9) Internal Drainage (Water Collection)",
        "٩) التصريف الداخلي (تجميع المياه)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Side drains + sump pits + pumps (if required)", "مصارف جانبية + حفر تجميع + مضخات عند الحاجة",
             "Prevents standing water, reduces hydrostatic pressure, and protects pavement.",
             "يمنع تجمع الماء ويقلل ضغط الماء ويحمي الرصف."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Gravity drainage only", "تصريف بالجاذبية فقط",
             "Works only when slopes/outfalls exist and water inflow is low.",
             "ينجح فقط إذا يوجد ميول ومصب مناسب ودخول الماء قليل."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No drainage channels", "بدون قنوات تصريف",
             "Water pooling damages finishing, causes skid risk and long-term leakage issues.",
             "تجمع الماء يضر التشطيبات ويسبب انزلاق ومشاكل تسرب طويلة."),
        ],
        height=440
    )

    # =========================================================
    # 10) Pavement / Road Surface Inside Tunnel
    # =========================================================
    render_system(
        "10) Tunnel Road Surface (Durable & Safe)",
        "١٠) سطح الطريق داخل النفق (متين وآمن)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Dense asphalt / high-performance pavement with skid resistance", "أسفلت كثيف / رصف عالي الأداء مع مقاومة انزلاق",
             "Ensures grip in humid conditions and resists rutting under traffic.",
             "يضمن تماسك مع الرطوبة ويقاوم التخدد تحت المرور."),
            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Concrete pavement with proper joints", "رصف خرسانة مع فواصل صحيحة",
             "Very durable but needs correct joint detailing and noise control.",
             "متين جداً لكن يحتاج فواصل صحيحة وضبط الضجيج."),
            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Low-quality surface with poor skid resistance", "سطح ضعيف بدون مقاومة انزلاق",
             "Increases accidents especially with water and oil contamination.",
             "يزيد الحوادث خصوصاً مع الماء والزيوت."),
        ],
        height=440
    )

def run_bridge_advisor_ui(render_system):
    import streamlit as st

    st.markdown("### Bridge Materials Decisions")
    st.markdown("قرارات مواد الجسر")
    st.markdown("---")

    render_system(
        "1) Deep Foundations (Piles)",
        "١) الأساسات العميقة (الركائز)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "SRC Cement + Epoxy Coated Rebar", "أسمنت مقاوم للكبريتات + حديد مطلي إيبوكسي",
             "Best durability in aggressive/submerged zones; reduces sulfate attack and corrosion.",
             "أفضل ديمومة بالمناطق العدوانية/المغمورة؛ يقلل الكبريتات والصدأ."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Normal materials with strict cover & QC", "مواد اعتيادية مع غطاء كبير وضبط جودة",
             "Allowed only with high cover, excellent compaction, and strict curing.",
             "مسموح فقط مع غطاء كبير ودمك ممتاز ومعالجة صارمة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "OPC Type I in aggressive exposure", "أسمنت عادي في بيئة عدوانية",
             "Not sulfate-resistant; accelerates deterioration and rebar corrosion.",
             "غير مقاوم للكبريتات؛ يسرّع التلف وصدأ الحديد."),
        ],
        height=280
    )

    render_system(
        "2) Substructure (Piers & Abutments)",
        "٢) الهيكل السفلي (الدعامات والأكتاف)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Self-Compacting Concrete (SCC)", "خرسانة ذاتية الدمك",
             "Fills congested reinforcement zones; reduces honeycombing.",
             "تملأ مناطق التسليح الكثيف؛ تقلل التعشيش."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Conventional concrete + superplasticizer", "خرسانة اعتيادية + ملدن",
             "OK only with strict w/c control and curing quality.",
             "مقبولة فقط مع ضبط نسبة الماء والمعالجة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Adding water on site (retempering)", "إضافة ماء بالموقع",
             "Raises w/c and permeability; reduces strength and durability.",
             "يرفع النفاذية ويقلل المقاومة والديمومة."),
        ],
        height=280
    )

    render_system(
        "3) Superstructure (Girders & Deck)",
        "٣) الهيكل العلوي (الروافد وبلاطة السطح)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Pre-stressed concrete girders", "روافد مسبقة الإجهاد",
             "Controls deflection/cracking for longer spans; reduces self-weight.",
             "يسيطر على الترخيم/التشققات للفضاءات الطويلة ويقلل الوزن."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Steel girders + protection system", "روافد فولاذية + حماية",
             "Works well but requires corrosion protection and maintenance plan.",
             "فعّالة لكن تحتاج حماية ضد التآكل وخطة صيانة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Conventional RC beams for long spans", "كمرات تقليدية لفضاءات طويلة",
             "Heavy and crack-prone; inefficient under traffic loads.",
             "ثقيلة وسريعة التشقق؛ غير اقتصادية تحت أحمال المرور."),
        ],
        height=300
    )

    render_system(
        "4) Bearings & Movement",
        "٤) الارتكاز والحركة",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Elastomeric bearings (laminated pads)", "مساند مطاطية مسلحة",
             "Allows thermal movement and absorbs vibration; protects pier head.",
             "تسمح بالحركة الحرارية وتمتص الاهتزاز؛ تحمي رأس الدعامة."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Pot/sliding bearings", "مساند وعائية/انزلاقية",
             "For higher movements/loads; needs precise installation and maintenance.",
             "للأحمال/الحركات الأكبر؛ تحتاج تركيب دقيق وصيانة."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "Monolithic connection (no bearing)", "اتصال مباشر بدون مسند",
             "Restricts movement; causes cracking/spalling at supports.",
             "يمنع الحركة؛ يسبب تشققات وتقشر عند المساند."),
        ],
        height=280
    )

    render_system(
        "5) Deck Protection (Waterproofing & Paving)",
        "٥) حماية السطح (العزل والرصف)",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Waterproofing membrane + polymer asphalt", "غشاء عزل + أسفلت بوليمري",
             "Blocks chlorides/water; asphalt remains flexible under vibration.",
             "يمنع الماء/الأملاح؛ الأسفلت يبقى مرن مع الاهتزاز."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Standard asphalt + excellent drainage/details", "أسفلت اعتيادي + تصريف ممتاز",
             "Only acceptable with perfect drainage and sealed joints.",
             "مقبول فقط مع تصريف ممتاز وإحكام الفواصل."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No waterproofing layer", "بدون عزل مائي",
             "Accelerates corrosion and potholes; short service life.",
             "يسرّع الصدأ والحفر؛ عمر خدمي قصير."),
        ],
        height=300
    )

    render_system(
        "6) Expansion Joints & Drainage",
        "٦) فواصل التمدد والتصريف",
        [
            ("Use (Recommended)", "استخدم (موصى به)",
             "Mechanical expansion joints + drainage", "فواصل ميكانيكية + تصريف",
             "Accommodates thermal movement and reduces leakage to substructure.",
             "تستوعب الحركة الحرارية وتقلل التسرب للهيكل السفلي."),

            ("Conditional (Use with limits)", "مقيد (يستخدم بشروط)",
             "Pourable seal joints (limited movement)", "فواصل سكب (حركة محدودة)",
             "Only for small movements with strict surface prep.",
             "فقط للحركات الصغيرة مع تجهيز سطح صارم."),

            ("Blocked (Do not use)", "ممنوع (لا تستخدم)",
             "No joints / no drainage", "بدون فواصل أو تصريف",
             "Leads to severe cracking and long-term leakage damage.",
             "يسبب تشققات شديدة وتلف تسرب طويل الأمد."),
        ],
        height=300
    )


def run_project_advisor_ui(project_type: str):
    import streamlit as st
    import streamlit.components.v1 as components

    # ✅ إعدادات الألوان (Deep Oceanic Palette)
    PRIMARY_NAVY = "#0F4C75"  # أزرق محيطي داكن
    LIGHT_BLUE = "#3282B8"  # أزرق سماوي صافي
    SOFT_BG = "#F1F4F7"  # خلفية فاتحة للجداول
    TEXT_DARK = "#1B262C"  # كحلي مسود للنصوص

    # زر التصميم بتنسيق متناسق
    if not st.button("Generate Project Decisions\nإنشاء قرارات المشروع", key="btn_project_decisions"):
        return

    # ===== Renderer (المصمم الجديد للجداول) =====
    def render_system(title_en: str, title_ar: str, rows: list, height: int = 280):
        # تنسيق رأس الجدول باللون المحيطي والحدود السماوية
        header_style = f"background:{PRIMARY_NAVY}; color:white; font-weight:700; border-bottom:3px solid {LIGHT_BLUE};"

        table_html = f"""
        <div style="width:100%; overflow-x:auto; font-family: 'Segoe UI', sans-serif;">
          <div style="margin:10px 0 15px 0; padding-right:10px; border-right:4px solid {LIGHT_BLUE};">
            <div style="font-size:18px; font-weight:800; color:{PRIMARY_NAVY};">{title_en}</div>
            <div style="direction:rtl; text-align:right; font-size:16px; font-weight:700; color:{PRIMARY_NAVY};">{title_ar}</div>
          </div>

          <table style="width:100%; border-collapse:collapse; font-size:13px; background:white; border-radius:12px; overflow:hidden; box-shadow: 0 4px 15px rgba(15,76,117,0.1);">
            <thead>
              <tr>
                <th style="{header_style} padding:12px; border:1px solid #ddd; width:22%;">Decision<br><span style="font-weight:400; font-size:11px;">القرار</span></th>
                <th style="{header_style} padding:12px; border:1px solid #ddd; width:30%;">Material<br><span style="font-weight:400; font-size:11px;">المادة</span></th>
                <th style="{header_style} padding:12px; border:1px solid #ddd; width:48%;">Engineering Reason<br><span style="font-weight:400; font-size:11px;">التفسير الهندسي</span></th>
              </tr>
            </thead>
            <tbody>
        """

        for i, (dec_en, dec_ar, mat_en, mat_ar, r_en, r_ar) in enumerate(rows):
            # تلوين الصفوف بشكل تبادلي لسهولة القراءة
            row_bg = "background:white;" if i % 2 == 0 else f"background:{SOFT_BG};"

            table_html += f"""
              <tr style="{row_bg}">
                <td style="padding:12px; border:1px solid #ddd; vertical-align:top;">
                  <div style="color:{PRIMARY_NAVY}; font-weight:700;">{dec_en}</div>
                  <div style="direction:rtl; text-align:right; margin-top:4px; font-weight:600; color:{TEXT_DARK};">{dec_ar}</div>
                </td>
                <td style="padding:12px; border:1px solid #ddd; vertical-align:top;">
                  <div style="color:{LIGHT_BLUE}; font-weight:700;">{mat_en}</div>
                  <div style="direction:rtl; text-align:right; margin-top:4px; font-weight:600; color:{TEXT_DARK};">{mat_ar}</div>
                </td>
                <td style="padding:12px; border:1px solid #ddd; vertical-align:top;">
                  <div style="color:#555; line-height:1.4;">{r_en}</div>
                  <div style="direction:rtl; text-align:right; margin-top:6px; color:#444; line-height:1.4;">{r_ar}</div>
                </td>
              </tr>
            """

        table_html += """
            </tbody>
          </table>
        </div>
        """

        components.html(table_html, height=height, scrolling=True)
        # فاصل أنيق متدرج
        st.markdown(
            f"""<hr style="border:0; height:1px; background-image: linear-gradient(to right, transparent, {LIGHT_BLUE}, transparent); margin:20px 0;">""",
            unsafe_allow_html=True)

    # ===== Dispatch (توجيه المستشار حسب نوع المشروع) =====
    advisors = {
        "Bridge": run_bridge_advisor_ui,
        "Hospital": run_hospital_advisor_ui,
        "Residential": run_residential_advisor_ui,
        "School": run_school_advisor_ui,
        "Commercial": run_commercial_advisor_ui,
        "Restaurant": run_restaurant_advisor_ui,
        "Warehouse": run_warehouse_advisor_ui,
        "Parking": run_parking_advisor_ui,
        "Tunnel": run_tunnel_advisor_ui,
        "Industrial": run_industrial_advisor_ui,
    }

    if project_type in advisors:
        advisors[project_type](render_system)
    else:
        st.info("Advisor not implemented.\nالمستشار غير مفعّل لهذا المشروع حالياً.")



def run_flooring_ui(project_type: str, structural_system: str, datasets: dict):
    import re
    import streamlit as st

    # =========================
    # Helper: pick flooring materials df
    # =========================
    def _pick_floor_mats(datasets: dict):
        # جرّب أكثر مفتاح محتمل
        for k in [
            "flooring_materials_global_df",
            "flooring_materials_df",
            "flooring_materials_global",
            "flooring_materials",
        ]:
            df = datasets.get(k)
            if df is not None and hasattr(df, "empty") and not df.empty:
                return df
        return None

    # =========================
    # Helper: make Material_Name readable
    # =========================
    def _humanize_material_name(raw: str) -> str:
        if not raw:
            return ""

        s = str(raw).strip()

        # 1) Replace underscores with spaces
        s = s.replace("_", " ")

        # 2) Split CamelCase inside tokens (StandardR10 -> Standard R10)
        s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)

        # 3) Split letter+number (R10 -> R 10) and (60x120 stays ok)
        s = re.sub(r"([A-Za-z])(\d)", r"\1 \2", s)
        s = re.sub(r"(\d)([A-Za-z])", r"\1 \2", s)

        # 4) Clean multiple spaces
        s = re.sub(r"\s+", " ", s).strip()

        # 5) Optional small normalization
        s = s.replace(" Lvt", " LVT").replace(" Pvc", " PVC")

        return s

    st.subheader("🧩 إعدادات الأرضيات (Flooring Settings)")

    c1, c2 = st.columns(2)

    with c1:
        room_type = st.selectbox(
            "Room Type (نوع الغرفة)",
            ["office", "corridor", "bedroom", "living", "classroom", "bathroom", "kitchen", "lobby", "industrial", "storage", "general"],
            index=0,
            key="f_room_type",
        )

        humidity = st.selectbox(
            "Humidity (الرطوبة)",
            ["low", "medium", "high"],
            index=1,
            key="f_humidity",
        )

        acoustic = st.selectbox(
            "Acoustic Priority (العزل الصوتي)",
            ["low", "medium", "high"],
            index=1,
            key="f_acoustic",
        )

    with c2:
        fire_req = st.selectbox(
            "Fire Requirement (متطلبات الحريق)",
            ["low", "medium", "high"],
            index=1,
            key="f_fire",
        )

        budget = st.selectbox(
            "Budget Level (مستوى الميزانية)",
            ["low", "medium", "high"],
            index=1,
            key="f_budget",
        )

        level = st.selectbox(
            "Level (المستوى)",
            ["upper", "ground"],
            index=0,
            key="f_level",
        )

    st.markdown("---")

    if not st.button("🎯 توليد توصية الأرضيات", key="run_floor_btn"):
        return

    # ✅ المحرك الجديد (نفس منطق الجدران)
    from expert_system import infer_flooring

    wet_areas = room_type in ["bathroom", "kitchen"]

    profile = {
        "project_type": project_type,
        "structural_system": structural_system,
        "room_type": room_type,
        "humidity": humidity,
        "acoustic": acoustic,
        "fire_rating": fire_req,
        "budget": budget,
        "wet_areas": wet_areas,
        "level": level,
    }

    res = infer_flooring(profile)

    # ====== Engineering Check (Risk Flag) ======
    check = res.get("engineering_check", {}) or {}
    if check:
        risk = str(check.get("risk_level", "")).lower()
        if risk == "high":
            st.error("⛔ Engineering Risk: LOW CONFIDENCE")
        elif risk in ["warning", "medium"]:
            st.warning("⚠️ Engineering Notes: MEDIUM CONFIDENCE")
        else:
            st.success("✅ Engineering Confidence: HIGH")

        for flag in check.get("flags", []):
            st.write(f"- {flag}")

        recs = check.get("recommendations", [])
        if recs:
            st.markdown("**اقتراحات هندسية:**")
            for r in recs:
                st.write(f"- {r}")

    # ====== Blocked list ======
    blocked = (res.get("hard_rules") or {}).get("blocked", [])
    if blocked:
        with st.expander("🚫 مواد تم استبعادها (Blocked)"):
            for b in blocked[:30]:
                st.write(f"- {b.get('material','?')} — {b.get('reason','')}")

    # ====== Best ======
    best = res.get("best") or {}
    if not best:
        st.error("❌ لا توجد توصية مناسبة للأرضيات حسب المدخلات الحالية.")
        return

    # 1) خذ ID المادة من نتيجة المحرك
    material_id = best.get("material_id") or best.get("id") or best.get("material")  # آخر fallback

    # 2) جيب الاسم من ملف Flooring_Materials_Global حسب Material_ID/Material_Name
    mats_df = _pick_floor_mats(datasets)

    raw_name = ""
    if mats_df is not None and material_id:
        try:
            row = mats_df.loc[mats_df["Material_ID"].astype(str) == str(material_id)]
            if not row.empty and "Material_Name" in row.columns:
                raw_name = str(row.iloc[0]["Material_Name"])
        except Exception:
            pass

    # 3) اسم عرض “Readable”
    display_name = _humanize_material_name(raw_name) if raw_name else str(material_id)

    st.subheader("✅ التوصية الأفضل (Best Flooring System)")
    st.markdown(f"### 🥇 {display_name}")
    st.write(f"**Material ID:** {material_id}")
    st.write(f"**Score:** {best.get('score','N/A')}")

    why = best.get("why") or []
    if why:
        st.markdown("**لماذا؟**")
        for w in why:
            st.write(f"- {w}")

    warn = best.get("warnings") or []
    if warn:
        st.markdown("**تنبيهات:**")
        for w in warn:
            st.write(f"- {w}")

    # ====== Package ======
    pkg = best.get("package") or {}
    if pkg:
        st.markdown("### 📦 النظام الكامل (System Package)")
        st.write(f"**المادة الأساسية:** {pkg.get('base_material','')}")
        st.write(f"**المادة الرابطة:** {pkg.get('binder','')}")
        layers = pkg.get("layers") or []
        if layers:
            st.markdown("**الطبقات (Layers):**")
            for x in layers:
                st.write(f"- {x}")
        acc = pkg.get("accessories") or []
        if acc:
            st.markdown("**الإكسسوارات/الملحقات:**")
            for x in acc:
                st.write(f"- {x}")
        notes = pkg.get("notes") or []
        if notes:
            st.markdown("**ملاحظات:**")
            for x in notes:
                st.write(f"- {x}")

    # ====== Alternatives ======
    alts = res.get("alternatives") or []
    if alts:
        st.markdown("---")
        st.subheader("🔁 بدائل مقترحة (Alternatives)")
        for a in alts:
            mid = a.get("material_id") or a.get("id") or a.get("material")
            # حاول تجيب اسم البديل أيضاً
            alt_raw = ""
            if mats_df is not None and mid:
                try:
                    r2 = mats_df.loc[mats_df["Material_ID"].astype(str) == str(mid)]
                    if not r2.empty and "Material_Name" in r2.columns:
                        alt_raw = str(r2.iloc[0]["Material_Name"])
                except Exception:
                    pass
            alt_name = _humanize_material_name(alt_raw) if alt_raw else str(mid)

            st.write(f"**{alt_name}**  —  Score: {a.get('score','N/A')} (ID: {mid})")


def run_wall_ui(project_type: str, structural_system: str, datasets: dict = None):
    import streamlit as st

    st.subheader("🧱 إعدادات الجدران (Wall Settings)")

    # =========================
    # Inputs (New)
    # =========================
    c1, c2, c3 = st.columns(3)

    with c1:
        wall_zone = st.selectbox(
            "Wall Zone (موقع الجدار)",
            ["external", "internal"],
            index=1,
            key="wall_zone_new",
        )

        room_type = st.selectbox(
            "Room Type (نوع الغرفة)",
            ["bedroom", "living", "office", "kitchen", "bathroom", "corridor", "other"],
            index=2,
            key="room_type_new",
        )

    with c2:
        humidity = st.selectbox(
            "Humidity (الرطوبة)",
            ["low", "medium", "high"],
            index=1,
            key="humidity_new",
        )

        fire_rating = st.selectbox(
            "Fire Requirement (متطلبات الحريق)",
            ["low", "medium", "high"],
            index=1,
            key="fire_new",
        )

    with c3:
        acoustic = st.selectbox(
            "Acoustic Priority (العزل الصوتي)",
            ["low", "medium", "high"],
            index=2 if project_type in ["Hospital", "School"] else 1,
            key="acoustic_new",
        )

        budget = st.selectbox(
            "Budget Level (مستوى الميزانية)",
            ["low", "medium", "high"],
            index=1,
            key="budget_new",
        )

    # Wet areas derived (bathroom/kitchen غالباً)
    wet_areas = room_type in ["bathroom", "kitchen"]

    st.markdown("---")

    # =========================
    # DEBUG (اختياري)
    # =========================
    with st.expander("🔎 DEBUG (اختياري)"):
        st.write("project_type:", project_type)
        st.write("structural_system:", structural_system)
        st.write("wall_zone:", wall_zone)
        st.write("room_type:", room_type)
        st.write("wet_areas:", wet_areas)
        st.write("humidity:", humidity)
        st.write("fire_rating:", fire_rating)
        st.write("acoustic:", acoustic)
        st.write("budget:", budget)

        # datasets صار غير مطلوب للجدران الجديدة
        if datasets is not None:
            st.info("datasets موجودة لكن الجدران الجديدة لا تعتمد عليها (infer_walls يحمّل الداتا من dataset/ تلقائياً).")

    # =========================
    # Run Recommendation (NEW)
    # =========================
    if not st.button("🎯 توليد توصية الجدران", key="run_wall_decision_new"):
        return

    # ✅ استدعاء الدالة الجديدة
    # ملاحظة: حسب مشروعك قد يكون الاستيراد من src.expert_system أو expert_system
    try:
        from expert_system import infer_walls
    except Exception:
        from expert_system import infer_walls

    # نبني profile بالـ keys اللي يفهمها infer_walls
    profile = {
        "project_type": project_type,
        "structural_system": structural_system,  # مهم لتحديد (partition vs structural)
        "wall_zone": wall_zone,                  # internal/external
        "room_type": room_type,                  # bathroom/kitchen/...
        "wet_areas": wet_areas,
        "humidity": humidity,
        "fire_rating": fire_rating,
        "acoustic": acoustic,
        "budget": budget,
    }

    result = infer_walls(profile)

    # =========================
    # Render Results (NEW)
    # =========================
    ctx = result.get("context", {})
    st.info(f"🧠 تصنيف النظام: **{ctx.get('domain','?')}** — {ctx.get('domain_reason','')}")

    # Blocked
    hard = result.get("hard_rules", {})
    blocked = hard.get("blocked", []) if isinstance(hard, dict) else []
    if blocked:
        st.error("⛔ مواد/أنظمة ممنوعة حسب قواعد النظام")
        # نعرض أول 12 لتجنب الإطالة
        for item in blocked[:12]:
            if isinstance(item, dict):
                st.write(f"- **{item.get('material','?')}** — {item.get('reason','')}")
            else:
                st.write(f"- {item}")

    best = result.get("best")
    if not best:
        st.error("❌ لا توجد توصية مناسبة حسب القيود الحالية.")
        st.info("جرّب تغيير wall_zone أو room_type أو خفّف القيود (رطوبة/حريق).")
        return

    st.success("✅ التوصية الأفضل (Best Wall System)")
    st.markdown(f"### 🥇 {best.get('material','(بدون اسم)')}")
    st.write(f"**Score:** {best.get('score','N/A')}")

    why = best.get("why", [])
    if why:
        st.markdown("**لماذا؟**")
        for r in why:
            st.write(f"- {r}")

    warnings = best.get("warnings", [])
    if warnings:
        st.markdown("**تحذيرات:**")
        for w in warnings:
            st.warning(w)

    package = best.get("package", {})
    if package:
        st.markdown("**📦 System Package (النظام الكامل):**")
        st.write("**المادة الأساسية:**", package.get("base_material", ""))
        st.write("**المادة الرابطة:**", package.get("binder", ""))
        acc = package.get("accessories", [])
        if acc:
            st.write("**الإكسسوارات/الملحقات:**")
            for a in acc:
                st.write(f"- {a}")
        st.write("**العتبات (Lintels):**", package.get("lintels", ""))

        notes = package.get("notes", [])
        if notes:
            st.write("**ملاحظات تنفيذ:**")
            for n in notes:
                st.info(n)

    # Alternatives
    alts = result.get("alternatives", [])
    if alts:
        st.warning("🔁 بدائل مقترحة (Alternatives)")
        for a in alts:
            st.markdown(f"**{a.get('material','')}** — Score: {a.get('score','N/A')}")
            aw = a.get("warnings", [])
            if aw:
                for w in aw[:2]:
                    st.caption(f"⚠️ {w}")


def run_materials_browser_ui():
    """واجهة متصفح المواد materials_master.xlsx مع فيلترة ذكية وآمنة."""


    # 1️⃣ تحميل ملف المواد
    from pathlib import Path
    import pandas as pd

    data_dir = Path(__file__).resolve().parent.parent / "dataset"
    master_path = data_dir / "materials_master.xlsx"

    if not master_path.exists():
        st.error(f"❌ لم يتم العثور على ملف المواد master: {master_path}")
        return

    try:
        mat_df = pd.read_excel(master_path)
    except Exception as ex:
        st.error(f"خطأ أثناء قراءة ملف المواد:\n{ex}")
        return

    if mat_df.empty:
        st.error("❌ ملف materials_master.xlsx فارغ (لا توجد مواد).")
        return

    # 2️⃣ توحيد أسماء الأعمدة (إزالة الفراغات)
    mat_df.columns = [str(c).strip() for c in mat_df.columns]

    # 3️⃣ التأكد من وجود الأعمدة الأساسية
    # نحاول اكتشاف عمود Suitable_Elements أو بديل مشابه
    if "Suitable_Elements" not in mat_df.columns:
        # نحاول نبحث عن أي عمود يبدأ بـ suitable
        alt_col = None
        for c in mat_df.columns:
            if str(c).strip().lower().startswith("suitable"):
                alt_col = c
                break

        if alt_col is not None:
            mat_df["Suitable_Elements"] = mat_df[alt_col]
        else:
            # ننشئ عمود فارغ حتى لا يحدث KeyError
            mat_df["Suitable_Elements"] = ""

    # لو ما عندنا Main_Category أو Sub_Category ما نوقف البرنامج، بس نشتغل باللي موجود
    has_main_cat = "Main_Category" in mat_df.columns
    has_sub_cat = "Sub_Category" in mat_df.columns

    # 4️⃣ تجهيز قائمة العناصر المناسبة كـ list بدل string
    def _split_elements(val):
        if pd.isna(val):
            return []
        if isinstance(val, str):
            parts = [p.strip() for p in val.split("|")]
            return [p for p in parts if p]
        return []

    mat_df["_elements_list"] = mat_df["Suitable_Elements"].apply(_split_elements)

    # 5️⃣ فلاتر أعلى الصفحة
    col1, col2, col3 = st.columns(3)

    # 🔹 الفلتر 1: التصنيف الرئيسي
    if has_main_cat:
        main_opts = sorted(mat_df["Main_Category"].dropna().unique().tolist())
        with col1:
            selected_main = st.multiselect(
                "Main Category (التصنيف الرئيسي)",
                options=main_opts,
                default=main_opts,
            )
    else:
        selected_main = []
        with col1:
            st.caption("لا يوجد عمود Main_Category في الجدول")

    # نبدأ بالجدول كامل ثم نطبق الفلاتر
    filtered = mat_df.copy()

    if has_main_cat and selected_main:
        filtered = filtered[filtered["Main_Category"].isin(selected_main)]

    # 🔹 الفلتر 2: التصنيف الفرعي
    if has_sub_cat and not filtered.empty:
        sub_opts = sorted(filtered["Sub_Category"].dropna().unique().tolist())
        with col2:
            selected_sub = st.multiselect(
                "Sub-Category (التصنيف الفرعي)",
                options=sub_opts,
                default=sub_opts,
            )
    else:
        selected_sub = []
        with col2:
            st.caption("لا يوجد عمود Sub_Category أو لا توجد صفوف مطابقة.")

    if has_sub_cat and selected_sub:
        filtered = filtered[filtered["Sub_Category"].isin(selected_sub)]

    # 🔹 الفلتر 3: العناصر الإنشائية المناسبة (من Suitable_Elements)
    all_elems = set()
    for lst in filtered["_elements_list"]:
        for e in lst:
            all_elems.add(e)

    all_elems = sorted(all_elems)

    with col3:
        selected_elems = st.multiselect(
            "Suitable Elements (العناصر المناسبة)",
            options=all_elems,
        )

    if selected_elems:
        mask = filtered["_elements_list"].apply(
            lambda lst: any(e in lst for e in selected_elems)
        )
        filtered = filtered[mask]

    # 🔹 خيار ترتيب حسب الكلفة
    sort_by_cost = st.checkbox("رتّب حسب الكلفة (أرخص أولاً)", value=True)
    if sort_by_cost and "Cost_Index" in filtered.columns:
        filtered = filtered.sort_values("Cost_Index", ascending=True)

    st.markdown("###  المواد المطابقة (Matching Materials)")

    if filtered.empty:
        st.warning("لا توجد مواد مطابقة للمعايير الحالية.")
    else:
        # نخفي العمود المساعد
        cols_to_show = [c for c in filtered.columns if c != "_elements_list"]
        st.dataframe(filtered[cols_to_show], use_container_width=True)

import streamlit as st
from pathlib import Path
import pandas as pd

def run_project_recommendations_ui(project_type: str, datasets: dict):
    st.header("📌 توصيات النظام الذكي حسب نوع المشروع")
    st.caption("هذه الصفحة تعطيك توصيات شاملة (Systems-level) بدون الدخول في عنصر (عمود/بيم...).")

    # =========================================================
    # 1) قواعد منطقية (Rule Packs) حسب نوع المشروع
    # =========================================================
    PROJECT_PACKS = {
        "Hospital": {
            "priorities": ["Hygiene", "Durability", "Acoustics", "Maintenance"],
            "banned": {
                "flooring": ["Carpet", "Natural_Wood"],
            },
            "structure": {
                "recommended": [
                    {"name": "Concrete Skeleton + Flat Slabs", "why": "تسهّل مرور تمديدات MEP وتقلل التعارضات تحت السقف."},
                    {"name": "Steel (Atrium/Lobby only)", "why": "مناسب للبحور الكبيرة والبهو الواسع فقط."},
                ],
            },
            "walls_partitions": {
                "recommended": [
                    {"name": "Exterior: AAC Blocks / Insulated Panels", "why": "عزل حراري جيد ووزن أخف."},
                    {"name": "Interior: Multi-layer Drywall + Rockwool", "why": "عزل صوتي للممرات والغرف."},
                    {"name": "X-Ray Rooms: Lead-lined Boards", "why": "متطلبات إشعاعية."},
                ],
            },
            "ceilings": {
                "recommended": [
                    {"name": "Corridors/Rooms: 60×60 Metal/Mineral Tiles", "why": "قابل للفك للصيانة + تشطيبات مقاومة للبكتيريا."},
                    {"name": "OR/ICU: Seamless Gypsum + Special Paint", "why": "تقليل الفواصل التي تجمع الغبار."},
                ],
            },
            "insulation": {
                "recommended": [
                    {"name": "Acoustic: High density Rockwool", "why": "عزل صوتي للأجهزة والممرات."},
                    {"name": "Roof: PU Foam or XPS + Waterproofing Membrane", "why": "عزل حراري/مائي مزدوج."},
                ],
            },
            "flooring": {
                "recommended": [
                    {"name": "Homogeneous Vinyl (Heat-welded)", "why": "بدون فواصل + سهل التنظيف + رفع على الجدار (coving)."},
                    {"name": "OR: Conductive/Anti-static Vinyl", "why": "يحمي الأجهزة الحساسة ويقلل الشحنات."},
                    {"name": "Lobby: Terrazzo/Granite", "why": "تحمل حركة عالية."},
                ],
            },
            "finishes": {
                "recommended": [
                    {"name": "Anti-bacterial Acrylic / Epoxy Paint", "why": "قابل للغسيل المتكرر بمواد قوية."},
                    {"name": "Fire Rated Doors + HPL", "why": "صدمات + مقاومة حريق."},
                ],
            },
        },

        "School": {
            "priorities": ["Durability", "Safety", "Maintenance", "Cost"],
            "structure": {
                "recommended": [
                    {"name": "Concrete Frame (RC)", "why": "مناسب اقتصادياً ومتوافر غالباً، وصيانته بسيطة."},
                    {"name": "Steel (Workshops/Halls)", "why": "للقاعات الواسعة/الورش فقط."},
                ],
            },
            "walls_partitions": {
                "recommended": [
                    {"name": "Exterior: AAC or Concrete Block + Insulation", "why": "عزل حراري وتقليل كلفة التشغيل."},
                    {"name": "Interior: Masonry Blocks / Durable Drywall", "why": "تحمل ضربات الطلاب وصيانة أسهل."},
                ],
            },
            "ceilings": {
                "recommended": [
                    {"name": "Classrooms: Mineral Fiber Tiles 60×60", "why": "عزل صوتي وتحكم بالصدى + صيانة."},
                    {"name": "Corridors: Metal Tiles", "why": "تحمل أعلى."},
                ],
            },
            "insulation": {
                "recommended": [
                    {"name": "Roof: XPS + Membrane", "why": "لرفع الراحة الحرارية وتقليل استهلاك الكهرباء."},
                    {"name": "Acoustic (selected areas)", "why": "قاعات/مسرح/مختبرات."},
                ],
            },
            "flooring": {
                "recommended": [
                    {"name": "Corridors: Porcelain Heavy Duty R11", "why": "مقاومة انزلاق + تحمل حركة عالية."},
                    {"name": "Classrooms: Porcelain/High durability vinyl", "why": "صيانة سهلة."},
                    {"name": "Labs: Epoxy Flooring", "why": "مقاومة كيماويات."},
                ],
            },
            "finishes": {
                "recommended": [
                    {"name": "Washable Emulsion / Texture Paint", "why": "سهولة تنظيف."},
                    {"name": "Edge Protection / Wall Guards", "why": "تقليل التلف."},
                ],
            },
        },

        "Restaurant": {
            "priorities": ["Hygiene", "Moisture Resistance", "Fire Safety", "Maintenance"],
            "structure": {
                "recommended": [
                    {"name": "Concrete Frame (RC)", "why": "ثبات جيد ومقاومة حريق أفضل عادة."},
                    {"name": "Steel (fast construction)", "why": "مناسب إذا الهدف سرعة التنفيذ مع حماية حريق."},
                ],
            },
            "walls_partitions": {
                "recommended": [
                    {"name": "Kitchen Walls: Cement Board / Tiles", "why": "رطوبة وتنظيف شديد."},
                    {"name": "Dining: Drywall + Acoustic infill", "why": "تقليل الضوضاء."},
                ],
            },
            "ceilings": {
                "recommended": [
                    {"name": "Kitchen: Moisture-resistant ceiling systems", "why": "بخار/دهون."},
                    {"name": "Dining: Acoustic ceiling tiles", "why": "تحسين الراحة الصوتية."},
                ],
            },
            "insulation": {
                "recommended": [
                    {"name": "Roof: XPS + Membrane", "why": "حماية حرارية وتقليل حرارة المطبخ."},
                    {"name": "Wet Areas: Waterproofing system", "why": "حمامات/مطبخ."},
                ],
            },
            "flooring": {
                "recommended": [
                    {"name": "Kitchen: Anti-slip Porcelain R11/R12", "why": "سلامة + تنظيف."},
                    {"name": "Dining: Porcelain/Stone-look tiles", "why": "تحمل + شكل."},
                ],
            },
            "finishes": {
                "recommended": [
                    {"name": "Washable/Grease-resistant paints", "why": "دهون وتنظيف."},
                    {"name": "Fire-rated doors (kitchen)", "why": "سلامة حريق."},
                ],
            },
        },
    }

    pack = PROJECT_PACKS.get(project_type) or {
        "priorities": ["General"],
        "structure": {"recommended": [{"name": "Concrete Frame (RC)", "why": "افتراضي عام."}]},
        "walls_partitions": {"recommended": [{"name": "Masonry / Drywall", "why": "افتراضي عام."}]},
        "ceilings": {"recommended": [{"name": "Standard False Ceiling", "why": "افتراضي عام."}]},
        "insulation": {"recommended": [{"name": "Standard Waterproofing + Thermal", "why": "افتراضي عام."}]},
        "flooring": {"recommended": [{"name": "Porcelain / Vinyl", "why": "افتراضي عام."}]},
        "finishes": {"recommended": [{"name": "Washable Paints", "why": "افتراضي عام."}]},
    }

    # =========================================================
    # 2) عرض أولويات المشروع
    # =========================================================
    st.info(f"**Project Type:** {project_type}  |  **Priorities:** {', '.join(pack.get('priorities', []))}")

    # =========================================================
    # 3) مساعد: بطاقة فنية (Technical Card)
    # =========================================================
    def render_card(title: str, items: list, note: str = ""):
        st.subheader(title)
        for i, it in enumerate(items, start=1):
            st.markdown(f"**{i}) {it['name']}**")
            st.caption(f"سبب التوصية: {it.get('why','')}")
        if note:
            st.warning(note)

    # =========================================================
    # 4) عرض البطاقات الأساسية
    # =========================================================
    colA, colB = st.columns(2)

    with colA:
        render_card("🏗️ تقرير النظام الإنشائي (Structure System)", pack["structure"]["recommended"])
        render_card("🧱 الجدران والقواطع (Walls & Partitions)", pack["walls_partitions"]["recommended"])

    with colB:
        render_card("🧩 السقوف الثانوية (Ceilings)", pack["ceilings"]["recommended"])
        render_card("🛡️ أنظمة العزل (Insulation)", pack["insulation"]["recommended"])

    st.markdown("---")
    render_card("🧱 الأرضيات (Flooring)", pack["flooring"]["recommended"])

    st.markdown("---")
    render_card("🎨 التشطيبات والإنهاءات (Finishes)", pack["finishes"]["recommended"])

    # =========================================================
    # 5) (اختياري) ربط مبدئي مع materials_master.xlsx لعرض مواد فعلية
    #     - إذا الملف موجود داخل dataset/ نعرض Preview + فلترة بسيطة
    # =========================================================
    st.markdown("---")
    st.subheader("📚 مواد فعلية من قاعدة المواد (materials_master)")

    data_dir = Path(__file__).resolve().parent / "dataset"
    master_path = data_dir / "materials_master.xlsx"

    if not master_path.exists():
        st.error(f"❌ ملف المواد غير موجود: {master_path}")
        st.caption("شغّل build_extra_materials.py لتوليد materials_master.xlsx داخل dataset/")
        return

    try:
        mat_df = pd.read_excel(master_path)
    except Exception as e:
        st.error(f"فشل قراءة ملف المواد: {e}")
        return

    st.caption(f"Using master file: {master_path} | Rows={len(mat_df)} | Cols={len(mat_df.columns)}")

    # فلتر سريع "حسب الفئة" (لو موجود عمود Category/SubCategory/Element...)
    possible_cat_cols = ["Main_Category", "Category", "System_Category"]
    possible_sub_cols = ["Sub_Category", "SubCategory", "Material_Family"]
    possible_use_cols = ["Best_Use_Case", "Application_Area", "Suitable_Elements"]

    cat_col = next((c for c in possible_cat_cols if c in mat_df.columns), None)
    sub_col = next((c for c in possible_sub_cols if c in mat_df.columns), None)
    use_col = next((c for c in possible_use_cols if c in mat_df.columns), None)

    with st.expander("🔎 فلترة المواد حسب التصنيف (اختياري)", expanded=True):
        f1, f2, f3 = st.columns(3)

        if cat_col:
            cats = sorted([x for x in mat_df[cat_col].dropna().astype(str).unique()])
            selected_cats = f1.multiselect("Main Category", cats, default=cats[:3] if cats else [])
        else:
            selected_cats = []
            f1.info("لا يوجد عمود Category واضح بالملف.")

        if sub_col:
            subs = sorted([x for x in mat_df[sub_col].dropna().astype(str).unique()])
            selected_subs = f2.multiselect("Sub-Category", subs, default=subs[:5] if subs else [])
        else:
            selected_subs = []
            f2.info("لا يوجد عمود Sub-Category واضح بالملف.")

        keyword = f3.text_input("بحث بالكلمة (اختياري)", value="")

        filtered = mat_df.copy()
        if cat_col and selected_cats:
            filtered = filtered[filtered[cat_col].astype(str).isin(selected_cats)]
        if sub_col and selected_subs:
            filtered = filtered[filtered[sub_col].astype(str).isin(selected_subs)]
        if keyword.strip():
            # بحث بسيط في أي عمود نصي
            kw = keyword.strip().lower()
            text_cols = [c for c in filtered.columns if filtered[c].dtype == object]
            if text_cols:
                mask = False
                for c in text_cols:
                    mask = mask | filtered[c].astype(str).str.lower().str.contains(kw, na=False)
                filtered = filtered[mask]

        st.write("✅ المواد المطابقة:")
        st.dataframe(filtered.head(50), use_container_width=True)

    # =========================================================
    # 6) ملاحظة هندسية ذكية (مثال: مستشفى + عزل السطح)
    # =========================================================
    if project_type == "Hospital":
        st.markdown("---")
        st.subheader("🧾 مثال بطاقة فنية: عزل السطح (Smart Output Card)")
        st.markdown("""
**تقرير المواد: عزل السطح**
- **1) برايمر بيتوميني**: كمية تقديرية **0.5 كغم/م²**
- **2) لفائف عزل (Membrane)**: سماكة **4 مم** (مسلحة بوليستر)
- **3) عزل حراري XPS**: كثافة **35**
- **4) طبقة حماية**: موزايكو/حصى
- **التكلفة التقديرية**: **15 – 20 USD/m²**
- **نصيحة هندسية**: تنفيذ **وزرة للعزل** على الجدار بارتفاع **20 سم**.
        """)


def render_hospital_flooring_card():
    st.info("Hospital Flooring Card – coming soon")


# =========================
# Language System (AR/EN)
# =========================
UI = {
    # Sidebar
    "general_settings": {"en": "General Settings", "ar": "الإعدادات العامة"},
    "language": {"en": "Language", "ar": "اللغة"},
    "arabic": {"en": "Arabic", "ar": "العربية"},
    "english": {"en": "English", "ar": "الإنكليزية"},

    "project_type": {"en": "Project Type", "ar": "نوع المشروع"},
    "structural_system": {"en": "Structural System", "ar": "النظام الإنشائي"},
    "app_mode": {"en": "App Mode", "ar": "وضع التطبيق"},
    "structural_element": {"en": "Structural Element", "ar": "العنصر الإنشائي"},

    # Modes
    "mode_engineering": {"en": "Engineering Design", "ar": "التصميم الإنشائي"},
    "mode_browser": {"en": "Materials Browser", "ar": "متصفح المواد"},
    "mode_advisor": {"en": "Project Systems Advisor", "ar": "مستشار الأنظمة للمشروع"},

    # Main titles
    "engineering_title": {"en": "Engineering Design", "ar": "تصميم العناصر الإنشائية"},
    "selected_inputs": {"en": "Selected Inputs", "ar": "المدخلات المختارة"},
    "unknown_element": {"en": "Unknown element.", "ar": "⚠ عنصر غير معروف."},

    "browser_title": {"en": "Materials Browser", "ar": "متصفح المواد"},

    "advisor_title": {"en": "Project Systems Advisor", "ar": "مستشار الأنظمة للمشروع"},
    "advisor_desc": {
        "en": "This mode provides project-level decisions (structure, walls, roofs, flooring, insulation, finishes...) without detailed element design.",
        "ar": "هذا الوضع يعطيك توصيات شاملة حسب نوع المشروع (هيكل، جدران، أسقف، أرضيات، عزل، تشطيبات...) بدون الدخول بتفاصيل العناصر."
    },

    # Options (Project Types)
    "Hospital": {"en": "Hospital", "ar": "مستشفى"},
    "Residential": {"en": "Residential", "ar": "سكني"},
    "Industrial": {"en": "Industrial", "ar": "مصنع"},
    "School": {"en": "School", "ar": "مدرسة"},
    "Restaurant": {"en": "Restaurant", "ar": "مطعم"},
    "Bridge": {"en": "Bridge", "ar": "جسر"},
    "Tunnel": {"en": "Tunnel", "ar": "نفق"},
    "Warehouse": {"en": "Warehouse", "ar": "مخزن"},
    "Parking": {"en": "Parking", "ar": "موقف سيارات"},
    "Commercial": {"en": "Commercial", "ar": "تجاري"},

    # Structural system options
    "RC_Frame": {"en": "RC Frame", "ar": "إطار خرساني"},
    "Steel_Frame": {"en": "Steel Frame", "ar": "إطار فولاذي"},
    "Shear_Wall": {"en": "Shear Wall", "ar": "جدران قص"},
    "Dual_System": {"en": "Dual System", "ar": "نظام مزدوج"},

    # Elements
    "foundation": {"en": "Foundation", "ar": "أساسات"},
    "column": {"en": "Column", "ar": "عمود"},
    "beam": {"en": "Beam", "ar": "جسر/كمرة"},
    "slab": {"en": "Slab", "ar": "بلاطة"},
    "wall": {"en": "Wall", "ar": "جدار"},
    "roof": {"en": "Roof", "ar": "سقف"},
    "flooring": {"en": "Flooring", "ar": "أرضيات"},
}

def get_lang() -> str:
    if "lang" not in st.session_state:
        st.session_state["lang"] = "ar"  # default Arabic
    return st.session_state["lang"]

def tr(key: str) -> str:
    lang = get_lang()
    if key in UI and lang in UI[key]:
        return UI[key][lang]
    return key

def format_bilingual(key: str) -> str:
    """Show English + Arabic in one line when needed."""
    en = UI.get(key, {}).get("en", key)
    ar = UI.get(key, {}).get("ar", key)
    return f"{en} ({ar})"

def language_switcher_sidebar():
    if "lang" not in st.session_state:
        st.session_state["lang"] = "ar"

    if "sb_lang_radio" not in st.session_state:
        st.session_state["sb_lang_radio"] = st.session_state["lang"]

    def _apply_lang():
        st.session_state["lang"] = st.session_state["sb_lang_radio"]

    st.sidebar.radio(
        "اللغة / Language",
        options=["ar", "en"],
        format_func=lambda x: "العربية" if x == "ar" else "English",
        horizontal=True,
        key="sb_lang_radio",
        on_change=_apply_lang,
    )

import time
import base64
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

# عدّل هنا:
YOUR_NAME = "Eng Muqtada"
PROJECT_TITLE_EN = "Construction Material Expert System"
PROJECT_TITLE_AR = "نظام خبير لاختيار المواد الإنشائية"



def _img_to_base64(path: Path) -> str:
    data = path.read_bytes()
    return base64.b64encode(data).decode("utf-8")

def show_university_boot(duration_sec: float = 1.8):
    """
    University boot screen with SVG animations (no external files).
    Shows once per session.
    """
    if "boot_done" not in st.session_state:
        st.session_state["boot_done"] = False

    if st.session_state["boot_done"]:
        return

    logo_html = ""
    try:
        if UNIVERSITY_LOGO_PATH and Path(UNIVERSITY_LOGO_PATH).exists():
            b64 = _img_to_base64(Path(UNIVERSITY_LOGO_PATH))
            logo_html = f"""
            <img src="data:image/png;base64,{b64}"
                 style="width:74px;height:74px;border-radius:14px;object-fit:contain;
                        background:rgba(255,255,255,0.7);border:1px solid rgba(128,0,0,0.18);
                        box-shadow:0 8px 18px rgba(0,0,0,0.10);"/>
            """
        else:

            logo_html = """
            <div style="width:74px;height:74px;border-radius:14px;display:flex;align-items:center;justify-content:center;
                        background:rgba(255,255,255,0.75);border:1px solid rgba(128,0,0,0.18);
                        box-shadow:0 8px 18px rgba(0,0,0,0.10);font-size:22px;">🏛️</div>
            """
    except Exception:
        logo_html = """
        <div style="width:74px;height:74px;border-radius:14px;display:flex;align-items:center;justify-content:center;
                    background:rgba(255,255,255,0.75);border:1px solid rgba(128,0,0,0.18);
                    box-shadow:0 8px 18px rgba(0,0,0,0.10);font-size:22px;">🏛️</div>
        """

    box = st.empty()

    css = """
    <style>
      .boot-wrap{width:100%;display:flex;justify-content:center;align-items:center;padding:24px 0 12px 0;}
      .card{
        width:min(1040px, 96%);
        border-radius:22px;
        padding:20px 22px 18px 22px;
        background: rgba(255,255,255,0.72);
        border:1px solid rgba(128,0,0,0.14);
        box-shadow: 0 22px 48px rgba(0,0,0,0.10);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        position:relative;
        overflow:hidden;
      }

      /* subtle maroon gradient ribbon */
      .ribbon{
        position:absolute; inset:auto -20% -65% -20%;
        height:260px;
        background: radial-gradient(circle at 30% 20%, rgba(128,0,0,0.22), rgba(128,0,0,0.02) 60%);
        transform: rotate(-6deg);
        pointer-events:none;
      }

      .top{display:flex;align-items:center;justify-content:space-between;gap:14px;}
      .left{display:flex;align-items:center;gap:14px;}
      .uni{
        line-height:1.2;
        font-family: Arial, sans-serif;
      }
      .uni .en{font-weight:800;color:#111827;font-size:16px;}
      .uni .dept{color:#374151;font-size:12.5px;margin-top:3px;}
      .uni .ar{direction:rtl;text-align:right;font-family:"Amiri",serif;color:#111827;font-size:14px;margin-top:4px;}

      .badge{
        font-family: Arial, sans-serif;
        font-size:12px;
        padding:7px 12px;
        border-radius:999px;
        background: rgba(128,0,0,0.10);
        border:1px solid rgba(128,0,0,0.14);
        color:#7f1d1d;
        font-weight:800;
        white-space:nowrap;
      }

      .mid{display:flex;gap:18px;align-items:center;margin-top:14px;}
      .title{
        font-family: Arial, sans-serif;
        font-size:20px;
        font-weight:900;
        color:#0f172a;
      }
      .subtitle{color:#334155;font-family:Arial,sans-serif;font-size:13px;margin-top:5px;}
      .name{
        margin-top:8px;
        font-family: Arial, sans-serif;
        font-size:12.5px;
        color:#475569;
      }
      .name b{color:#0f172a;}

      .progress{
        margin-top:14px;
        height:10px;border-radius:999px;
        background: rgba(2,6,23,0.06);
        border:1px solid rgba(128,0,0,0.10);
        overflow:hidden;
      }
      .fill{
        height:100%;
        width:0%;
        border-radius:999px;
        background: linear-gradient(90deg, rgba(128,0,0,0.85), rgba(128,0,0,0.35));
        animation: load 1.8s ease-in-out forwards;
      }
      @keyframes load{
        0%{width:10%;}
        60%{width:75%;}
        100%{width:100%;}
      }

      .status{
        display:flex;justify-content:space-between;align-items:center;margin-top:10px;
        font-family: Arial, sans-serif;font-size:12px;color:#475569;
      }
      .ok{color:#7f1d1d;font-weight:900;}

      /* SVG animation helpers */
      .svgbox{width:310px;max-width:38vw;}
      .pulse{animation:pulse 1.4s ease-in-out infinite;}
      @keyframes pulse{0%,100%{transform:scale(1);opacity:0.9}50%{transform:scale(1.05);opacity:1}}
      .dash{stroke-dasharray: 6 10; animation: dash 2.4s linear infinite;}
      @keyframes dash{to{stroke-dashoffset:-64;}}
      .blink{animation: blink 1.1s infinite;}
      @keyframes blink{0%,65%,100%{opacity:.25}40%{opacity:1}}
    </style>
    """

    # رسومات: (1) شبكة هندسية خفيفة + (2) نبض AI + (3) مبنى/عمود بسيط
    svg = """
    <svg class="svgbox" viewBox="0 0 520 260" xmlns="http://www.w3.org/2000/svg">
      <!-- background grid -->
      <defs>
        <pattern id="grid" width="26" height="26" patternUnits="userSpaceOnUse">
          <path d="M 26 0 L 0 0 0 26" fill="none" stroke="rgba(128,0,0,0.10)" stroke-width="1"/>
        </pattern>
      </defs>
      <rect x="0" y="0" width="520" height="260" fill="url(#grid)"/>

      <!-- structural frame -->
      <g fill="none" stroke="rgba(15,23,42,0.35)" stroke-width="3" stroke-linecap="round">
        <path d="M80 210 L80 90 L170 90 L170 210" />
        <path d="M170 210 L170 120 L260 120 L260 210" />
        <path d="M260 210 L260 70 L350 70 L350 210" />
      </g>

      <!-- beam dashed analysis line -->
      <path class="dash" d="M65 55 C140 25, 210 95, 290 60 S430 85, 470 45"
            fill="none" stroke="rgba(128,0,0,0.55)" stroke-width="3"/>

      <!-- AI pulse node -->
      <g transform="translate(410 170)">
        <circle class="pulse" cx="0" cy="0" r="28" fill="rgba(128,0,0,0.12)" stroke="rgba(128,0,0,0.35)" stroke-width="2"/>
        <circle cx="0" cy="0" r="8" fill="rgba(128,0,0,0.80)"/>
        <circle class="blink" cx="0" cy="0" r="18" fill="none" stroke="rgba(128,0,0,0.35)" stroke-width="2"/>
      </g>

      <!-- small labels -->
      <text x="18" y="30" font-family="Arial" font-size="12" fill="rgba(15,23,42,0.55)">Structural Sketch</text>
      <text x="18" y="48" font-family="Amiri" font-size="13" fill="rgba(15,23,42,0.60)">مخطط إنشائي</text>
    </svg>
    """

    html = f"""
    {css}
    <div class="boot-wrap">
      <div class="card">
        <div class="ribbon"></div>

        <div class="top">
          <div class="left">
            {logo_html}
            <div class="uni">
              <div class="en">Southern Technical University</div>
              <div class="dept">Department of Civil &amp; Construction Engineering</div>
              <div class="ar">الجامعة التقنية الجنوبية • قسم هندسة البناء والإنشاءات</div>
            </div>
          </div>
          <div class="badge">University Boot</div>
        </div>

        <div class="mid">
          <div style="flex:1;">
            <div class="title">{PROJECT_TITLE_EN}</div>
            <div class="subtitle" style="direction:rtl;text-align:right;font-family:Amiri,serif;color:#0f172a;">
              {PROJECT_TITLE_AR}
            </div>
            <div class="name">Prepared by: <b>{YOUR_NAME}</b> • Initializing expert modules…</div>

            <div class="progress"><div class="fill"></div></div>

            <div class="status">
              <div>Loading: Rules • Materials • UI • Advisor</div>
              <div class="ok">READY</div>
            </div>
          </div>

          <div>
            {svg}
          </div>
        </div>
      </div>
    </div>
    """

    with box:
        components.html(html, height=290, scrolling=False)

    time.sleep(duration_sec)
    box.empty()
    st.session_state["boot_done"] = True
    st.rerun()


import streamlit as st
import streamlit.components.v1 as components

def _bot_message_pack(project_type: str, struct_system: str, mode_key: str, lang: str = "ar") -> dict:
    """
    Returns: {"title": "...", "lines": ["...", "...", ...]}
    """
    # أسماء بسيطة للعرض
    mode_map_en = {
        "mode_engineering": "Engineering Design",
        "mode_browser": "Materials Browser",
        "mode_advisor": "Project Systems Advisor",
    }
    mode_map_ar = {
        "mode_engineering": "المهندس المصمم",
        "mode_browser": "متصفح المواد",
        "mode_advisor": "مستشار أنظمة المشاريع",
    }

    m_en = mode_map_en.get(mode_key, mode_key)
    m_ar = mode_map_ar.get(mode_key, mode_key)

    # رسائل حسب المشروع (مختصر + مفيد)
    hint_en = {
        "Hospital": "Hospital projects prioritize hygiene, fire safety, and durable finishes.",
        "Bridge": "Bridge projects prioritize durability, corrosion resistance, and movement systems.",
        "Industrial": "Industrial projects prioritize impact resistance, logistics, and fire protection.",
        "School": "Schools prioritize safety, acoustics, and high-traffic durable materials.",
        "Residential": "Residential projects prioritize comfort, cost efficiency, and thermal performance.",
        "Commercial": "Commercial projects prioritize aesthetics, durability, and maintainability.",
    }.get(project_type, "I will guide you to select the best materials based on your current context.")

    hint_ar = {
        "Hospital": "المستشفى يركز على التعقيم، مقاومة الحريق، وديمومة التشطيبات.",
        "Bridge": "الجسر يركز على الديمومة، مقاومة التآكل، وأنظمة الحركة.",
        "Industrial": "المصنع يركز على مقاومة الصدمات واللوجستيات والحريق.",
        "School": "المدرسة تركز على السلامة والعزل الصوتي وديمومة الاستخدام العالي.",
        "Residential": "السكني يركز على الراحة وتقليل الكلفة والأداء الحراري.",
        "Commercial": "التجاري يركز على الشكل والديمومة وسهولة الصيانة.",
    }.get(project_type, "سأرشدك لاختيار أفضل المواد حسب سياق مشروعك الحالي.")

    # مثال “تعارض” بسيط (بدون ميزانية) — فقط إشارة ذكية لوضع المتصفح/التصميم
    conflict_en = ""
    conflict_ar = ""
    if mode_key == "mode_browser":
        conflict_en = "Tip: Use this mode to validate available materials and compare properties quickly."
        conflict_ar = "نصيحة: هذا الوضع مفيد لمراجعة المواد ومقارنة الخصائص بسرعة."
    elif mode_key == "mode_engineering":
        conflict_en = "Tip: Enter element inputs carefully; I will generate ranked recommendations with reasons."
        conflict_ar = "نصيحة: أدخل محددات العنصر بدقة؛ سأعطيك توصيات مرتبة مع الأسباب."
    elif mode_key == "mode_advisor":
        conflict_en = "Tip: This mode gives project-level decisions: recommended, conditional, and blocked options."
        conflict_ar = "نصيحة: هذا الوضع يعطي قرارات للمشروع: موصى به، مقيد، وممنوع."

    if lang == "en":
        return {
            "title": "Smart Engineering Assistant",
            "lines": [
                f"Hello Engineer! I’m your assistant.",
                f"Project: {project_type} | System: {struct_system}",
                f"Mode: {m_en}",
                hint_en,
                conflict_en,
                "Click me anytime for guidance.",
            ]
        }
    else:
        return {
            "title": "المساعد الهندسي الذكي",
            "lines": [
                "مرحباً مهندس! أنا مساعدك الذكي.",
                f"المشروع: {project_type} | النظام: {struct_system}",
                f"الوضع الحالي: {m_ar}",
                hint_ar,
                conflict_ar,
                "اضغط عليّ بأي وقت للمساعدة.",
            ]
        }

# ===========================================================
import streamlit as st

def apply_deep_oceanic_theme():
    # ✅ Deep Oceanic Palette (تركيبة البحرية العميقة)
    PRIMARY = "#0F4C75"        # أزرق محيطي داكن (للأزرار والعناوين)
    PRIMARY_HOVER = "#1B262C"  # كحلي مسود عند التمرير
    GOLD  = "#3282B8"          # أزرق سماوي صافي (للحدود والتمييز)
    BG    = "#E1E8EE"          # رمادي مائل للأزرق (الخلفية الأساسية)
    CARD  = "#FFFFFF"          # أبيض نقي للبطاقات لزيادة التباين
    TEXT  = "#0B0E14"          # كحلي مسود للنصوص

    st.markdown(f"""
    <style>
      :root {{
        --g: {PRIMARY};
        --g2: {PRIMARY_HOVER};
        --gold: {GOLD};
        --bg: {BG};
        --card: {CARD};
        --text: {TEXT};
        --radius: 14px;
      }}

      /* ===== Global background ===== */
      html, body, [data-testid="stAppViewContainer"], .stApp {{
        background: var(--bg) !important;
        color: var(--text) !important;
      }}

      /* ===== Separators (st.markdown("---")) ===== */
      hr {{
        border: none !important;
        height: 2px !important;
        background: var(--gold) !important;
        opacity: 0.5;
        margin: 14px 0 !important;
      }}

      /* ===== Sidebar frame ===== */
      section[data-testid="stSidebar"] {{
        background: #D1D9E0 !important; /* درجة أغمق قليلاً من الخلفية */
        border-right: 2px solid var(--gold) !important;
      }}

      /* ===== Main Titles / Text default ===== */
      h1, h2, h3, h4 {{
        color: var(--g) !important;
        font-weight: 800 !important;
      }}

      /* ===== Buttons ===== */
      .stButton > button,
      div[data-testid="stButton"] > button,
      button[kind="primary"],
      button[kind="secondary"] {{
        background: var(--g) !important;
        color: #FFFFFF !important;
        border: 2px solid var(--gold) !important;
        border-radius: var(--radius) !important;
        font-weight: 900 !important;
        transition: 0.3s all ease;
      }}
      .stButton > button:hover,
      div[data-testid="stButton"] > button:hover {{
        background: var(--g2) !important;
        box-shadow: 0 4px 12px rgba(15, 76, 117, 0.3) !important;
      }}

      /* ===== Inputs / Selects (BaseWeb) ===== */
      div[data-baseweb="select"] > div,
      div[data-baseweb="input"] > div,
      div[data-baseweb="textarea"] > div {{
        background: var(--card) !important;
        border-radius: var(--radius) !important;
        border: 2px solid rgba(50, 130, 184, 0.4) !important;
      }}

      /* ✅ Select text + chosen value */
      div[data-baseweb="select"] span,
      div[data-baseweb="select"] div {{
        color: var(--g) !important;
        font-weight: 800 !important;
      }}

      /* Labels */
      label {{
        color: var(--text) !important;
        font-weight: 800 !important;
      }}

      /* Radio group container */
      div[role="radiogroup"] {{
        background: var(--card) !important;
        border: 2px solid rgba(50, 130, 184, 0.3) !important;
        border-radius: var(--radius) !important;
        padding: 10px 12px !important;
      }}

      /* ===== Custom Sidebar Cards ===== */
      .sb-card {{
        background: var(--card);
        border: 2px solid var(--gold);
        border-radius: 14px;
        padding: 12px 12px;
        margin: 10px 0 12px 0;
      }}
      .sb-head {{
        background: var(--g);
        color: #fff;
        font-weight: 900;
        text-align: center;
        padding: 10px 12px;
        border-radius: 12px;
        margin-bottom: 10px;
      }}

      /* ===== Main Title Card (center) ===== */
      .main-title-card {{
        width: 100%;
        background: var(--g);
        color: #fff;
        border: 2px solid var(--gold);
        border-radius: 14px;
        padding: 18px 18px;
        text-align: center;
        margin: 10px 0 16px 0;
      }}
      .main-title-card .t2 {{
        font-size: 18px;
        font-weight: 800;
        margin-top: 6px;
        color: #E1E8EE;
      }}

      /* ===== Generic Content Cards ===== */
      .content-card {{
        background: var(--card);
        border: 2px solid rgba(50, 130, 184, 0.2);
        border-radius: 14px;
        padding: 14px 14px;
        margin: 10px 0 12px 0;
      }}

      /* Accent color for Radio checks */
      input[type="radio"] {{
        accent-color: var(--g) !important;
      }}
    </style>
    """, unsafe_allow_html=True)
# ===========================================================
def render_smart_floating_bot(project_type: str, struct_system: str, mode_key: str, lang: str = "ar"):
    """
    نسخة المهندس الذكي - دمج الهندسة مع الذكاء الاصطناعي
    الشكل: روبوت بخوذة هندسية وواجهة رقمية نيون
    """
    import streamlit.components.v1 as components

    pack = _bot_message_pack(project_type, struct_system, mode_key, lang)
    title = pack["title"]
    lines = [ln for ln in pack["lines"] if ln]
    js_lines = "[" + ",".join([repr(x) for x in lines]) + "]"

    # ✅ تنسيق الألوان: أزرق هندسي عميق + أخضر تقني خفيف
    PRIMARY_NAVY = "#0F4C75"
    CYAN_TECH    = "#3282B8"
    GOLD_LIGHT   = "#BBE1FA"

    RIGHT_PX = 18
    BOTTOM_PX = 12
    FAB_SIZE = 68 # تكبير بسيط لإبراز التفاصيل الهندسية
    OPEN_W = 340
    OPEN_H = 410

    html = f"""
    <style>
      body {{ margin: 0; background: transparent; overflow: visible; font-family: 'Segoe UI', sans-serif; }}

      /* الفقاعة العائمة (المهندس السيبراني) */
      .bot-fab {{
        position: absolute;
        right: 0px; bottom: 0px;
        width: {FAB_SIZE}px; height: {FAB_SIZE}px;
        border-radius: 18px;
        background: {PRIMARY_NAVY};
        border: 2px solid {CYAN_TECH};
        box-shadow: 0 8px 20px rgba(0,0,0,0.3), inset 0 0 15px {CYAN_TECH}44;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; z-index: 999999;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
      }}
      .bot-fab:hover {{ transform: translateY(-5px) scale(1.05); shadow: 0 12px 25px {CYAN_TECH}66; }}

      /* الدرج الزجاجي */
      .bot-drawer {{
        position: absolute;
        right: 0px; bottom: {FAB_SIZE + 15}px;
        width: {OPEN_W}px;
        background: rgba(248, 250, 252, 0.9);
        backdrop-filter: blur(12px);
        border: 1.5px solid {CYAN_TECH};
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(15, 76, 117, 0.25);
        display: none; overflow: hidden;
        animation: slideIn 0.3s ease-out;
      }}
      @keyframes slideIn {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
      .bot-drawer.open {{ display: block; }}

      .bot-header {{
        background: {PRIMARY_NAVY};
        color: white; padding: 12px 15px;
        display: flex; align-items: center; justify-content: space-between;
        border-bottom: 2px solid {CYAN_TECH};
      }}
      .bot-title {{ font-weight: 800; font-size: 12.5px; letter-spacing: 0.2px; }}

      .bot-body {{
        padding: 15px; font-size: 12px; color: #1B262C;
        background-image: radial-gradient({CYAN_TECH}33 0.5px, transparent 0.5px);
        background-size: 18px 18px;
      }}
      .bot-bubble {{
        background: #FFFFFF; border-radius: 12px;
        padding: 12px; margin-bottom: 10px;
        border: 1px solid {CYAN_TECH}22;
        line-height: 1.6; font-weight: 500;
      }}

      /* أنيميشن الأجزاء الهندسية */
      .helmet-top {{ animation: float 3s ease-in-out infinite; }}
      @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-1.5px); }} }}
      .eye-glow {{ animation: pulse-eye 2s infinite; }}
      @keyframes pulse-eye {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
    </style>

    <div class="bot-drawer" id="botDrawer">
      <div class="bot-header">
        <div class="bot-title">🛠️ {title}</div>
        <button id="botClose" style="background:none; border:none; color:white; font-size:20px; cursor:pointer;">×</button>
      </div>
      <div class="bot-body">
        <div class="bot-bubble">
          <div id="botTyping"></div>
        </div>
        <div style="font-size:9px; color:{PRIMARY_NAVY}; text-align:center; opacity:0.7; font-weight:bold; letter-spacing:1px;">
          ENGINEERING AI UNIT v3.0
        </div>
      </div>
    </div>

    <div class="bot-fab" id="botFab">
      <svg width="42" height="42" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path class="helmet-top" d="M14 28c0-10 8-18 18-18s18 8 18 18v4H14v-4Z" fill="{CYAN_TECH}" opacity="0.9"/>
        <rect x="12" y="32" width="40" height="4" rx="2" fill="{GOLD_LIGHT}"/>
        <rect x="18" y="36" width="28" height="18" rx="4" fill="#1B262C" stroke="{CYAN_TECH}" stroke-width="1.5"/>
        <rect class="eye-glow" x="23" y="42" width="6" height="6" rx="1" fill="{GOLD_LIGHT}"/>
        <rect class="eye-glow" x="35" y="42" width="6" height="6" rx="1" fill="{GOLD_LIGHT}"/>
        <circle cx="32" cy="18" r="2" fill="white" opacity="0.5"/>
        <path d="M14 36v10c0 4 3 7 7 7h22c4 0 7-3 7-7V36" stroke="{CYAN_TECH}" stroke-width="2"/>
      </svg>
    </div>

    <script>
      const frame = window.frameElement;
      function setFrameClosed() {{
        frame.style.position = "fixed";
        frame.style.right = "{RIGHT_PX}px"; frame.style.bottom = "{BOTTOM_PX}px";
        frame.style.width = "{FAB_SIZE + 20}px"; frame.style.height = "{FAB_SIZE + 20}px";
        frame.style.zIndex = "999999";
      }}
      function setFrameOpen() {{
        frame.style.width = "{OPEN_W}px"; frame.style.height = "{OPEN_H}px";
      }}

      setFrameClosed();
      const drawer = document.getElementById("botDrawer");
      const fab = document.getElementById("botFab");
      const closeBtn = document.getElementById("botClose");
      const typingEl = document.getElementById("botTyping");

      const lines = {js_lines};
      let isOpen = false;

      fab.addEventListener("click", () => {{
        if (!isOpen) {{
          setFrameOpen();
          drawer.classList.add("open");
          isOpen = true;
          startTyping(lines);
        }} else {{ closeDrawer(); }}
      }});

      function closeDrawer() {{
        drawer.classList.remove("open");
        isOpen = false;
        setTimeout(setFrameClosed, 300);
      }}

      closeBtn.addEventListener("click", (e) => {{ e.stopPropagation(); closeDrawer(); }});

      async function startTyping(linesArr) {{
        typingEl.textContent = "";
        for (let i = 0; i < linesArr.length; i++) {{
          const line = String(linesArr[i] || "");
          for (let j = 0; j < line.length; j++) {{
            typingEl.textContent += line[j];
            await new Promise(r => setTimeout(r, 14));
          }}
          if (i !== linesArr.length - 1) typingEl.textContent += "\\n\\n";
          await new Promise(r => setTimeout(r, 150));
        }}
      }}
    </script>
    """
    components.html(html, height=1, scrolling=False)

import pandas as pd

def safe_for_streamlit(df: pd.DataFrame) -> pd.DataFrame:
    """Make dataframe Arrow-friendly for st.dataframe/st.table."""
    if df is None or df.empty:
        return df

    out = df.copy()

    # Convert problematic object columns to string to avoid mixed types
    for col in out.columns:
        if out[col].dtype == "object":
            out[col] = out[col].astype(str)

    return out



def main():
    import streamlit as st

    st.set_page_config(
        page_title="Construction Material Expert System",
        layout="wide",
    )

    # ✅ 1) Theme first
    apply_deep_oceanic_theme()

    # Boot (optional)
    show_university_boot(duration_sec=8)

    # Header
    render_header()


    # Sidebar Language Switcher
    language_switcher_sidebar()

    # ✅ 2) Load datasets once (ONLY this inside spinner)
    with st.spinner("Loading datasets... (يتم الآن تحميل قواعد ومواد المشروع)"):
        datasets = get_datasets()

    # ===========================================================
    # ✅ Dashboard Card (Main Page) — minimal and clean
    # ===========================================================




    # Dashboard buttons (changes mode without touching logic)
    c1, c2, c3 = st.columns(3)
    if c1.button("Start Consultation\nبدء الاستشارة", use_container_width=True):
        st.session_state["sb_mode_key"] = "mode_engineering"
        st.rerun()

    if c2.button("Knowledge Base\nقاعدة المعرفة", use_container_width=True):
        st.session_state["sb_mode_key"] = "mode_browser"
        st.rerun()

    if c3.button("Project Advisor\nمستشار المشاريع", use_container_width=True):
        st.session_state["sb_mode_key"] = "mode_advisor"
        st.rerun()

    st.markdown("<hr class='gold-hr'/>", unsafe_allow_html=True)

    # ===========================================================
    # Sidebar (Control Panel)
    # ===========================================================
    st.sidebar.markdown(
        "<div class='sb-card'><div class='sb-head'>لوحة التحكم</div></div>",
        unsafe_allow_html=True
    )

    PROJECT_TYPES = [
        "Hospital", "Residential", "Industrial", "School", "Restaurant",
        "Bridge", "Tunnel", "Warehouse", "Parking", "Commercial",
    ]

    STRUCT_SYSTEMS = ["RC_Frame", "Steel_Frame", "Shear_Wall", "Dual_System"]
    MODES = ["mode_engineering", "mode_browser", "mode_advisor"]

    # ✅ Project card
    st.sidebar.markdown("<div class='sb-card'><div class='sb-head'>Project</div>", unsafe_allow_html=True)

    project_type = st.sidebar.selectbox(
        format_bilingual("project_type"),
        PROJECT_TYPES,
        index=0,
        format_func=lambda x: format_bilingual(x),
        key="sb_project_type",
    )

    struct_system = st.sidebar.selectbox(
        format_bilingual("structural_system"),
        STRUCT_SYSTEMS,
        index=0,
        format_func=lambda x: format_bilingual(x),
        key="sb_struct_system",
    )

    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    # ✅ App Mode card
    st.sidebar.markdown("<div class='sb-card'><div class='sb-head'>App Mode</div>", unsafe_allow_html=True)

    # IMPORTANT: default if not set
    if "sb_mode_key" not in st.session_state:
        st.session_state["sb_mode_key"] = "mode_engineering"

    mode_key = st.sidebar.radio(
        format_bilingual("app_mode"),
        MODES,
        index=MODES.index(st.session_state["sb_mode_key"]) if st.session_state["sb_mode_key"] in MODES else 0,
        format_func=lambda k: format_bilingual(k),
        key="sb_mode_key",
    )

    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    st.sidebar.markdown("<hr class='gold-hr'/>", unsafe_allow_html=True)

    render_smart_floating_bot(project_type, struct_system, mode_key, get_lang())


    # ===========================================================
    # MAIN CONTENT
    # ===========================================================
    if mode_key == "mode_engineering":
        st.markdown(f"## 🏗️ {format_bilingual('engineering_title')}")

        ELEMENTS = ["foundation", "column", "beam", "slab", "wall", "roof", "flooring"]

        element = st.sidebar.selectbox(
            format_bilingual("structural_element"),
            ELEMENTS,
            index=0,
            format_func=lambda x: format_bilingual(x),
            key="sb_element",
        )

        st.markdown(f"### 🧾 {format_bilingual('selected_inputs')}")
        st.write(f"- **{tr('project_type')}:** {format_bilingual(project_type)}")
        st.write(f"- **{tr('structural_system')}:** {format_bilingual(struct_system)}")
        st.write(f"- **{tr('structural_element')}:** {format_bilingual(element)}")
        st.markdown("<hr class='gold-hr'/>", unsafe_allow_html=True)

        if element == "foundation":
            run_foundation_ui(project_type, struct_system, datasets)
        elif element == "column":
            run_column_ui(project_type, struct_system, datasets)
        elif element == "beam":
            run_beam_ui(project_type, struct_system, datasets)
        elif element == "slab":
            run_slab_ui(project_type, struct_system, datasets)
        elif element == "wall":
            run_wall_ui(project_type, struct_system, datasets)
        elif element == "roof":
            st.info("Roof module is not available yet. (وحدة السقف غير مفعّلة حالياً)")
        elif element == "flooring":
            run_flooring_ui(project_type, struct_system, datasets)
        else:
            st.warning(tr("unknown_element"))

    elif mode_key == "mode_browser":
        st.markdown(f"## 📚 {format_bilingual('browser_title')}")
        run_materials_browser_ui()

    elif mode_key == "mode_advisor":
        st.markdown(f"## {format_bilingual('advisor_title')}")
        st.markdown(tr("advisor_desc"))
        st.markdown("<hr class='gold-hr'/>", unsafe_allow_html=True)
        run_project_advisor_ui(project_type)


if __name__ == "__main__":
    main()

