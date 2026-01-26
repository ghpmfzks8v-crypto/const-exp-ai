#   CONSTRUCTION MATERIAL EXPERT SYSTEM
#   Foundations + Columns + Materials (Concrete / Rebar / WP)
#   Version: Safe 3-stage Matching (Exact → Relaxed → Scoring)
# ===========================================================

import pandas as pd
from typing import Optional, Dict, Any
from pathlib import Path
from referencing.exceptions import NoInternalID

# ============================
# PATHS (Stable Absolute Paths)
# ============================

SRC_DIR = Path(__file__).resolve().parent         # .../construction-expert-system/src
PROJECT_DIR = SRC_DIR.parent                      # .../construction-expert-system
DATASET_DIR = PROJECT_DIR / "dataset"             # .../construction-expert-system/dataset

FOUNDATIONS_RULES_PATH        = DATASET_DIR / "Foundations_Rules_Global_MultiCode.xlsx"
COLUMNS_RULES_PATH            = DATASET_DIR / "Columns_Rules_Global_MultiCode.xlsx"
BEAMS_RULES_PATH              = DATASET_DIR / "Beams_Rules_ACI_Global.xlsx"
SLABS_RULES_PATH              = DATASET_DIR / "Slabs_Rules_ACI_Global.xlsx"
WALLS_RULES_PATH              = DATASET_DIR / "Walls_Rules_ACI_Global.xlsx"
RETAINING_RULES_PATH          = DATASET_DIR / "Retaining_Walls_Rules_Global.xlsx"
ROOFING_RULES_PATH            = DATASET_DIR / "Roofing_Systems_Rules_ACI_Global.xlsx"
FLOORING_RULES_PATH           = DATASET_DIR / "Flooring_Rules_ACI_Global.xlsx"

CONCRETE_MATERIALS_PATH       = DATASET_DIR / "Concrete_Materials.xlsx"
STEEL_REBAR_MATERIALS_PATH    = DATASET_DIR / "Steel_Rebar_Materials.xlsx"
WATERPROOFING_MATERIALS_PATH  = DATASET_DIR / "Waterproofing_Materials.xlsx"
ROOFING_MATERIALS_PATH        = DATASET_DIR / "Roofing_Materials_Global.xlsx"
FLOORING_MATERIALS_PATH       = DATASET_DIR / "Flooring_Materials_Global.xlsx"


def get_material_display_name(row: pd.Series) -> str:
    """
    ترجع اسم المادة بشكل مفهوم:
    - تحاول تبحث عن اسم إنجليزي ثم عربي.
    - لا تعتمد على Material_ID (الرمز).
    """
    # أعمدة محتملة لاسم المادة في كل الداتا سيت
    name_candidates_en = [
        "Material_Name",
        "Mix_Name",
        "Material_EN",
        "Name_EN",
        "System_Name",
    ]
    name_candidates_ar = [
        "Material_AR",
        "Name_AR",
    ]

    name_en = ""
    name_ar = ""

    for col in name_candidates_en:
        if col in row and str(row[col]).strip():
            name_en = str(row[col]).strip()
            break

    for col in name_candidates_ar:
        if col in row and str(row[col]).strip():
            name_ar = str(row[col]).strip()
            break

    if name_en and name_ar:
        return f"{name_en} ({name_ar})"
    elif name_en:
        return name_en
    elif name_ar:
        return name_ar
    else:
        return "Unknown material (مادة غير معرّفة)"
# ============================
#   Utilities
# ============================


# ============================================================
# Pretty printers for materials (عرض منسّق للمواد)
# ============================================================

def pretty_print_concrete(df: Optional[pd.DataFrame]):
    """عرض أفضل خلطات خرسانة مع اسم الخلطة والخواص الأساسية."""
    if df is None or df.empty:
        print("No matching concrete. (لا توجد خرسانة مطابقة)\n")
        return

    top = df.head(3).copy()
    print("\nTop Concrete Mixes (أفضل خلطات الخرسانة):\n")
    for i, (_, row) in enumerate(top.iterrows(), start=1):
        mix_name = row.get("Mix_Name") or row.get("Mix") or row.get("Material_Name") or ""
        mat_id   = row.get("Material_ID", "")
        fc       = row.get("Strength_MPa", "?")
        cem      = row.get("Cement_Type", "?")
        exp      = row.get("Exposure_Class") or row.get("Exposure_Class_ACI") or row.get("exp_key", "-")
        cost     = row.get("Cost_Index", "N/A")
        score    = row.get("concrete_score", "N/A")

        print(f"#{i} ----------------------------------")
        if mix_name:
            print(f"Mix (خلطة الخرسانة): {mix_name}")
        print(f"Material ID (رمز الخلطة): {mat_id}")
        print(f"Strength f'c (مقاومة الضغط MPa): {fc}")
        print(f"Cement Type (نوع السمنت): {cem}")
        print(f"Exposure Class (درجة التعرض): {exp}")
        print(f"Cost Index (مؤشر الكلفة): {cost}")
        print(f"Score (درجة المطابقة): {score}")
        print()


def pretty_print_rebar(df: Optional[pd.DataFrame]):
    """عرض حديد التسليح المقترح بشكل منسّق."""
    if df is None or df.empty:
        print("No matching rebar. (لا يوجد حديد تسليح مطابق)\n")
        return

    top = df.head(3).copy()
    print("\nTop Rebar Options (أفضل خيارات حديد التسليح):\n")
    for i, (_, row) in enumerate(top.iterrows(), start=1):
        rebar_id = row.get("Rebar_ID", "")
        grade    = row.get("Steel_Grade", "")
        fy       = row.get("Yield_Strength_MPa", "?")
        coat     = row.get("Coating_Type", "?")
        corr     = row.get("Corrosion_Resistance_Level", "?")
        seis     = row.get("Seismic_Suitability", "?")
        best_use = row.get("Best_Use_Case", "")
        cost     = row.get("Cost_Index", "N/A")
        score    = row.get("rebar_score", "N/A")

        print(f"#{i} ----------------------------------")
        print(f"Rebar (حديد التسليح): {rebar_id}  | Grade (الدرجة): {grade}")
        print(f"Yield Strength fy (إجهاد الخضوع MPa): {fy}")
        print(f"Coating (الطلاء): {coat} | Corrosion (مقاومة التآكل): {corr}")
        print(f"Seismic Suitability (الملاءمة الزلزالية): {seis}")
        if best_use:
            print(f"Best Use Case (أفضل استخدام): {best_use}")
        print(f"Cost Index (مؤشر الكلفة): {cost}")
        print(f"Score (درجة المطابقة): {score}")
        print()


def pretty_print_waterproofing(df: Optional[pd.DataFrame]):
    """عرض مواد العزل المائي (Foundations + Roof)."""
    if df is None or df.empty:
        print("No matching waterproofing. (لا توجد مواد عزل مطابقة)\n")
        return

    top = df.head(3).copy()
    print("\nTop Waterproofing Systems (أفضل أنظمة العزل المائي):\n")
    for i, (_, row) in enumerate(top.iterrows(), start=1):
        mat_id  = row.get("Material_ID", "")
        system  = row.get("System_Category", "")
        product = row.get("Product_Name", "") or row.get("System_Name", "")
        best_use = row.get("Best_Use_Case", "")
        score   = row.get("final_score", "N/A")

        print(f"#{i} ----------------------------------")
        if product:
            print(f"System (النظام): {product}")
        print(f"Material ID (رمز المادة): {mat_id}")
        print(f"Category (التصنيف): {system}")
        if best_use:
            print(f"Best Use Case (أفضل استخدام): {best_use}")
        print(f"Score (درجة المطابقة): {score}")
        print()


def pretty_print_flooring(df: Optional[pd.DataFrame]):
    """عرض مواد تشطيب الأرضيات باسم المادة بدلاً من الرمز فقط."""
    if df is None or df.empty:
        print("No matching flooring materials. (لم يتم العثور على مواد مطابقة)\n")
        return

    top = df.head(3).copy()
    print("\nTop Flooring Materials (أفضل مواد تشطيب الأرضيات):\n")
    for i, (_, row) in enumerate(top.iterrows(), start=1):
        mat_id = row.get("Material_ID", "")
        # نحاول أكثر من اسم حتى نضمن ظهور اسم المادة
        name = (
            row.get("Material_EN")
            or row.get("Material_AR")
            or row.get("Material_Name")
            or row.get("Finish_Name")
            or ""
        )
        traffic = row.get("Traffic_Class", "")
        slip    = row.get("Slip_Resistance_Class", "")
        best_use = row.get("Best_Use_Case", "")
        score  = row.get("flooring_score", "N/A")

        print(f"#{i} ----------------------------------")
        if name:
            print(f"Material (المادة): {name}")
        print(f"Material ID (رمز المادة): {mat_id}")
        if traffic:
            print(f"Traffic Class (فئة الحركة): {traffic}")
        if slip:
            print(f"Slip Resistance (مقاومة الانزلاق): {slip}")
        if best_use:
            print(f"Best Use Case (أفضل استخدام): {best_use}")
        print(f"Flooring score (درجة المطابقة): {score}")
        print()

# ------------------------------
# Excel loader with pickle cache
# ------------------------------
import pandas as pd
from pathlib import Path

# ------------------------------
# Excel loader with simple cache
# ------------------------------
def load_excel_with_cache(excel_path):
    """
    يحمّل ملف Excel مع كاش بسيط:
    - إذا وجد ملف .pkl بجانبه → يقرأه (سريع)
    - إذا لم يوجد → يقرأ Excel ثم يحفظ .pkl لاستخدامه في المرات القادمة
    """
    excel_path = Path(excel_path)
    cache_path = excel_path.with_suffix(".pkl")

    # لو ملف الكاش موجود
    if cache_path.exists():
        try:
            df = pd.read_pickle(cache_path)
            print(f"⚡ Loaded from cache: {cache_path.name} (rows={len(df)})")
            return df
        except Exception as e:
            print(f"⚠ Error reading cache {cache_path.name}: {e}")

    # لو ماكو كاش → نقرأ من Excel
    try:
        df = pd.read_excel(excel_path)
        print(f"📄 Loaded from Excel: {excel_path.name} (rows={len(df)})")
    except Exception as e:
        print(f"⚠ Error reading Excel {excel_path}: {e}")
        return None

    # نحفظ كـ pickle للمرات القادمة
    try:
        df.to_pickle(cache_path)
        print(f"💾 Cached to: {cache_path.name}")
    except Exception as e:
        print(f"⚠ Error writing cache {cache_path.name}: {e}")

    return df


def load_all_datasets():
    """
    تجمع كل جداول القواعد والمواد في قاموس واحد.
    تعتمد على المسارات المعرفة مسبقاً في الملف:
    FOUNDATIONS_RULES_PATH, COLUMNS_RULES_PATH, BEAMS_RULES_PATH, ...
    وتستخدم كاش pickle لتسريع التشغيلات التالية.
    """
    datasets = {}

    # =============================
    # RULES (القواعد الهندسية)
    # =============================
    datasets["foundations_rules"] = load_excel_with_cache(FOUNDATIONS_RULES_PATH)
    datasets["columns_rules"]     = load_excel_with_cache(COLUMNS_RULES_PATH)
    datasets["beams_rules"]       = load_excel_with_cache(BEAMS_RULES_PATH)
    datasets["slabs_rules"]       = load_excel_with_cache(SLABS_RULES_PATH)
    datasets["walls_rules"]       = load_excel_with_cache(WALLS_RULES_PATH)
    datasets["retaining_rules"]   = load_excel_with_cache(RETAINING_RULES_PATH)
    datasets["roofing_rules"]     = load_excel_with_cache(ROOFING_RULES_PATH)
    datasets["flooring_rules"]    = load_excel_with_cache(FLOORING_RULES_PATH)


    datasets["foundation_rules_df"] = datasets["foundations_rules"]
    datasets["column_rules_df"]     = datasets["columns_rules"]
    datasets["beam_rules_df"]       = datasets["beams_rules"]
    datasets["slab_rules_df"]       = datasets["slabs_rules"]
    datasets["wall_rules_df"]       = datasets["walls_rules"]
    datasets["roof_rules_df"]       = datasets["roofing_rules"]
    datasets["flooring_rules_df"]   = datasets["flooring_rules"]

    # =============================
    # MATERIALS (جداول المواد)
    # =============================
    datasets["concrete_df"]           = load_excel_with_cache(CONCRETE_MATERIALS_PATH)
    datasets["rebar_df"]              = load_excel_with_cache(STEEL_REBAR_MATERIALS_PATH)
    datasets["waterproofing_df"]      = load_excel_with_cache(WATERPROOFING_MATERIALS_PATH)
    datasets["roofing_materials_df"]  = load_excel_with_cache(ROOFING_MATERIALS_PATH)
    datasets["flooring_materials_df"] = load_excel_with_cache(FLOORING_MATERIALS_PATH)

    return datasets

# ==========================
# Ask Function (الدالة الموحدة للمدخلات)
# ==========================
def ask(prompt_en: str):
    ar = translations.get(prompt_en.lower(), "")
    if ar:
        return input(f"{prompt_en} ({ar}): ")
    return input(f"{prompt_en}: ")


# ==========================
# Translation Dictionary (قاموس الترجمة)
# ==========================
translations = {
    "soil type": "نوع التربة",
    "groundwater level": "مستوى المياه الجوفية",
    "load level": "مستوى الحمل",
    "project type": "نوع المشروع",
    "usage type": "نوع الاستخدام",
    "traffic level": "مستوى الحركة",
    "water exposure": "التعرض للماء",
    "foundation type": "نوع الأساس",
    "column type": "نوع العمود",
    "beam span": "طول البحر",
    "slab type": "نوع البلاطة",
    "wall type": "نوع الجدار",
    "roof type": "نوع السقف",
    "flooring type": "نوع الأرضية",
}

# عبارات خاصة بالكمرات (كانت مضافة لاحقاً)
translations.update(
    {
        "beam role": "دور الكمرة",
        "span range (m)": "مدى البحر (متر)",
        "load type": "نوع الحمل",
        "moment level": "مستوى العزم",
        "shear level": "مستوى القص",
        "seismic zone level (for beams)": "منطقة الزلازل (للكمرات)",
        "environment type": "نوع البيئة",
        "minimum concrete strength required (mpa)": "أدنى مقاومة خرسانة مطلوبة (MPa)",
    }
)


def choose_from_menu(title_en: str, options: dict, options_ar: dict = None):
    """
    دالة اختيار من قائمة — الآن تدعم 3 براميترات:
    - title_en: عنوان القائمة
    - options: الخيارات بالإنجليزي
    - options_ar: ترجمة الخيارات بالعربي (اختياري)
    """

    # ترجمة عنوان القائمة
    ar_title = translations.get(title_en.lower(), "")
    full_title = f"{title_en} ({ar_title})" if ar_title else title_en

    print(f"\n--- {full_title} ---")

    # عرض الخيارات
    for key, value in options.items():
        if options_ar and value in options_ar:
            print(f"{key} - {value} ({options_ar[value]})")
        else:
            print(f"{key} - {value}")

    # أخذ المدخل
    choice = input("Enter number: ")

    while choice not in options:
        print("Invalid choice, try again.")
        choice = input("Enter number: ")

    return options[choice]



# ============================================
#   ARABIC LABELS FOR MENUS & OUTPUT
# ============================================

PROJECT_TYPE_AR = {
    "Hospital":   "مستشفى",
    "Residential":"سكني",
    "Industrial": "صناعي",
    "School":     "مدرسة",
    "Bridge":     "جسر",
    "Tunnel":     "نفق",
    "Warehouse":  "مستودع",
    "Parking":    "موقف سيارات",
    "Commercial": "تجاري",
}

STRUCT_SYSTEM_AR = {
    "RC_Frame":    "هيكل خرساني",
    "Steel_Frame": "هيكل فولاذي",
    "Shear_Wall":  "نظام جدران قص",
    "Dual_System": "نظام ثنائي (إطار + جدران)",
}

ELEMENT_AR = {
    "foundation":     "أساسات",
    "column":         "أعمدة",
    "beam":           "كمرات / جوائز",
    "slab":           "بلاطات / سقوف",
    "wall":           "جدران",
    "roof":           "سقف / سطح علوي",
    "flooring":       "تشطيبات أرضيات",

}


def try_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def norm(s: Any) -> str:
    """تطبيع النص للمقارنة (lower + underscore)."""
    return str(s).strip().lower().replace(" ", "_")


# ============================
#  Helper: Severity orders (Foundations)
# ============================

SEISMIC_ORDER = {
    "low": 0,
    "moderate": 1,
    "medium": 1,
    "high": 2,
    "very_high": 3,
}

AGGRESSIVE_ORDER = {
    "normal": 0,
    "medium_sulfate": 1,
    "high_sulfate": 2,
    "marine": 3,
    "marine_environment": 3,
}


# ============================
#  Filter rules (generic)
# ============================

def filter_rules(
    df: pd.DataFrame,
    criteria: Dict[str, Any],
    columns_to_use
) -> pd.DataFrame:
    """فلترة القواعد بناءً على الأعمدة المحددة."""
    data = df.copy()
    for col in columns_to_use:
        if col not in data.columns:
            continue
        target = criteria.get(col)
        if target is None or target == "":
            continue
        tnorm = norm(target)
        data = data[data[col].apply(lambda x: norm(x) == tnorm)]
    return data


# ============================
#  Stage 3: Scoring rules (Foundations)
# ============================

def score_foundation_rule(row: pd.Series, criteria: Dict[str, Any]) -> float:
    """حساب Score لقاعدة أساس مع احترام السلامة."""
    score = 0.0

    # 1) السلامة البيئية – لا نسمح بأن تكون القاعدة أخف من المطلوب
    # Seismic
    target_seis = norm(criteria.get("Seismic_Zone_Level", "low"))
    rule_seis   = norm(row.get("Seismic_Zone_Level", "low"))
    ts = SEISMIC_ORDER.get(target_seis, 0)
    rs = SEISMIC_ORDER.get(rule_seis, 0)
    if rs < ts:
        return -1e9  # مرفوض (أقل من المطلوب)
    score += (rs - ts) * 2.0  # كلما كان أعلى قليلاً يزيد الأمان

    # Aggressiveness / Sulfate
    target_ag = norm(criteria.get("Aggressiveness_Class", "normal"))
    rule_ag   = norm(row.get("Aggressiveness_Class", "normal"))
    ta = AGGRESSIVE_ORDER.get(target_ag, 0)
    ra = AGGRESSIVE_ORDER.get(rule_ag, 0)
    if ra < ta:
        return -1e9
    score += (ra - ta) * 2.0

    # 2) Bearing capacity تقريبية (كلما اقتربت من المطلوب كان أفضل)
    target_bc = try_float(criteria.get("Bearing_Capacity_kPa", 0.0))
    rule_bc   = try_float(row.get("Bearing_Capacity_kPa", 0.0))
    if target_bc > 0:
        diff = abs(rule_bc - target_bc)
        score -= diff / 50.0  # penalty بسيطة

    # 3) Min concrete strength
    min_fc = try_float(row.get("Min_Concrete_Strength_MPa", 20.0))
    req_fc = try_float(criteria.get("Min_Concrete_Strength_MPa", 20.0))
    if req_fc > 0 and min_fc < req_fc:
        return -1e9
    score += (min_fc - req_fc) * 0.5  # زيادة بسيطة ليست مشكلة

    # 4) Cost level (كلما كان أقل أفضل)
    cost = norm(row.get("Cost_Level", "medium"))
    if cost == "low":
        score += 3
    elif cost == "medium":
        score += 1
    elif cost == "high":
        score -= 1

    # 5) Importance_Level يمكن أن نكافئ "Very_High"
    imp = norm(row.get("Importance_Level", "normal"))
    if "very_high" in imp:
        score += 2

    return score


# ============================
#  Foundation rule selection
# ============================

def find_best_foundation_rule_safe(
    found_df: pd.DataFrame,
    project_type: str,
    struct_system: str,
    soil: str,
    gwt: str,
    seismic: str,
    exc_risk: str,
    aggressiveness: str,
    min_fc_req: float
) -> Optional[pd.Series]:
    """
    اختيار أفضل قاعدة أساس بثلاث مراحل:
    1) Exact = كل القيود (Hard + Soft)
    2) Relaxed = فقط القيود الصلبة (تربة، مياه جوفية، زلازل، كيمياء، مخاطر حفر)
    3) Scoring = أفضل قاعدة لا تخرق السلامة.
    """

    if found_df is None or len(found_df) == 0:
        return None

    crit = {
        "Project_Type": project_type,
        "Structural_System": struct_system,
        "Soil_Type": soil,
        "Groundwater_Level": gwt,
        "Seismic_Zone_Level": seismic,
        "Excavation_Risk_Level": exc_risk,
        "Aggressiveness_Class": aggressiveness,
        "Min_Concrete_Strength_MPa": min_fc_req,
    }

    # Hard / Soft
    hard_cols = [
        "Soil_Type",
        "Groundwater_Level",
        "Seismic_Zone_Level",
        "Aggressiveness_Class",
        "Excavation_Risk_Level",
    ]
    soft_cols = [
        "Project_Type",
        "Structural_System",
    ]

    # ---- Stage 1: Exact match (Hard + Soft)
    s1 = filter_rules(found_df, crit, hard_cols + soft_cols)
    if len(s1) > 0:
        return s1.iloc[0]

    # ---- Stage 2: Relaxed (Hard only)
    s2 = filter_rules(found_df, crit, hard_cols)
    if len(s2) > 0:
        s2 = s2.copy()
        s2["tmp_score"] = s2["Min_Concrete_Strength_MPa"].apply(
            lambda v: -abs(try_float(v) - (min_fc_req or try_float(v)))
        )
        s2 = s2.sort_values("tmp_score", ascending=False)
        return s2.iloc[0]

    # ---- Stage 3: Scoring على كل الجدول مع ضمان السلامة
    scores = []
    for _, row in found_df.iterrows():
        sc = score_foundation_rule(row, crit)
        scores.append(sc)

    found_df = found_df.copy()
    found_df["score_tmp"] = scores
    found_df = found_df[found_df["score_tmp"] > -1e8]
    if len(found_df) == 0:
        return None

    found_df = found_df.sort_values("score_tmp", ascending=False)
    return found_df.iloc[0]

# ============================
#  MATERIAL SELECTION (Concrete / Rebar / WP)
# ============================

def select_concrete_for_rule(
    conc_df: Optional[pd.DataFrame],
    rule_row: Optional[pd.Series],
    top_n: int = 3,
) -> Optional[pd.DataFrame]:
    """
    اختيار خرسانة مناسبة من جدول Concrete_Materials
    مع مراعاة:
    - Min_Concrete_Strength_MPa
    - Preferred_Concrete_Strength_MPa
    - Exposure_Class / Exposure_Class_ACI (مثل XC1, XC2, XS3 ...)
    """

    if conc_df is None or conc_df.empty or rule_row is None:
        return None

    df = conc_df.copy()

    # -----------------------------
    # 1) إجبارياً: مقاومة الضغط الدنيا
    # -----------------------------
    try:
        min_fc  = float(rule_row.get("Min_Concrete_Strength_MPa", 0) or 0)
        pref_fc = float(rule_row.get("Preferred_Concrete_Strength_MPa", min_fc) or min_fc)
    except Exception:
        min_fc = 0.0
        pref_fc = 0.0

    if "Strength_MPa" in df.columns:
        df = df[df["Strength_MPa"].astype(float) >= min_fc]

    if df.empty:
        return None

    # -----------------------------
    # 2) مفتاح التعرض (XC1 / XC2 / XS3 ...)
    # -----------------------------
    rule_exp = (
        str(rule_row.get("Exposure_Class_ACI", "")).strip()
        or str(rule_row.get("Exposure_Class", "")).strip()
    )

    def exp_key(v: Any) -> str:
        s = str(v).strip()
        if not s:
            return ""
        # مثال: XC1_Normal_Interior → XC1
        return s.split("_")[0]

    rule_exp_key = exp_key(rule_exp)

    if "Exposure_Class" in df.columns:
        df["exp_key"] = df["Exposure_Class"].apply(exp_key)
    else:
        df["exp_key"] = ""

    # -----------------------------
    # 3) حساب السكور
    # -----------------------------
    scores = []
    for _, r in df.iterrows():
        s = 0.0

        # قوة الخرسانة قريبة من المفضلة
        try:
            fc = float(r.get("Strength_MPa", min_fc) or min_fc)
        except Exception:
            fc = min_fc

        # كل ما قربت من f'c المفضل كان أفضل
        s -= abs(fc - pref_fc) * 0.2  # تقريبا كل 5 MPa فرق تعطي -1

        # مطابقة التعرض
        rk = rule_exp_key  # مثل XC2 أو XS3
        ck = r.get("exp_key", "")  # مثل XC2 أو XC1

        if not rk:
            # ما عندي معلومات تعرض في القاعدة، ما أقيّم
            pass
        # نفس الكلاس بالضبط (XC2 مع XC2 أو XS3 مع XS3)
        elif ck == rk:
            s += 4.0

        # حالة تعرّض كربنة XC (XC1..XC4)
        elif rk.startswith("XC"):
            if ck.startswith("XC"):
                # نفس العائلة XC لكن درجة مختلفة (مثلاً XC2 مع XC3)
                s += 1.0
            else:
                # القاعدة XC والمكس XS / XD / شيء آخر غريب
                s -= 3.0

        # حالة تعرّض بحرية / كلوريدات (XS.. أو XD..)
        elif rk.startswith("XS") or rk.startswith("XD"):
            if ck.startswith("XS") or ck.startswith("XD"):
                # نفس عائلة الكلوريدات
                s += 3.0
            elif ck.startswith("XC2") or ck.startswith("XC3") or ck.startswith("XC4"):
                # ما عندي XS في الداتا، أختار على الأقل خرسانة خارجية قوية XC2/3/4
                s += 1.5
            elif ck.startswith("XC1"):
                # خرسانة داخلية خفيفة لبيئة بحرية → عقوبة كبيرة
                s -= 6.0
            else:
                s -= 4.0
        else:
            # أي mismatch آخر
            s -= 3.0

        scores.append(s)

    df["concrete_score"] = scores
    df = df.sort_values("concrete_score", ascending=False)
    return df.head(top_n)

def select_rebar_for_rule(
    rebar_df: Optional[pd.DataFrame],
    rule: Optional[pd.Series],
    top_n: int = 3
) -> Optional[pd.DataFrame]:
    """اختيار حديد التسليح المناسب للأساسات أو الأعمدة."""
    if rebar_df is None or rule is None or len(rebar_df) == 0:
        return None

    data = rebar_df.copy()

    seismic = norm(rule.get("Seismic_Zone_Level", "low"))
    aggressive = norm(rule.get("Aggressiveness_Class", "normal"))

    scores = []
    for _, row in data.iterrows():
        sc = 0.0

        # درجة الفولاذ
        fy = try_float(row.get("Yield_Strength_MPa", 400))
        if fy >= 420:
            sc += 3.0

        # تآكل
        corr = norm(row.get("Corrosion_Resistance_Level", "medium"))
        if aggressive != "normal":
            if "high" in corr:
                sc += 4.0
            elif "medium" in corr:
                sc += 2.0

        # زلازل
        seis_suit = norm(row.get("Seismic_Suitability", "normal"))
        if "high" in seismic or "very_high" in seismic:
            if "high" in seis_suit or "very_high" in seis_suit:
                sc += 4.0

        cost = try_float(row.get("Cost_Index", 3.0))
        sc += (5 - cost) * 1.0

        scores.append(sc)

    data = data.copy()
    data["rebar_score"] = scores
    data = data.sort_values("rebar_score", ascending=False)
    return data.head(top_n)


# ===========================================================
#   ROOFING MATERIALS SELECTION
# ===========================================================

def _safe_str(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def score_roof_material(mat: pd.Series, roof_rule: pd.Series) -> float:
    """
    منطق هندسي تقريبي لاختيار أفضل مادة تغطية للسقف:
    - يفضّل مواد مناسبة للبيئة (Marine / Normal / Industrial ...)
    - يطابق نوع السقف (Flat / Pitched)
    - يطابق نوع النظام (RC_Slab_Roof مع أغشية عزل، Steel Roof مع Metal Panels ...)
    - يفضّل مواد ذات حريق ومتانة أعلى للمشاريع المهمة (Hospital, School, Commercial, Industrial)
    """

    sc = 0.0

    # -------- 1) البيئة (Environment) --------
    rule_env = _safe_str(roof_rule.get("Environment_Type")).lower()
    mat_env  = _safe_str(
        mat.get("Suitable_Environment", mat.get("Environment_Type"))
    ).lower()

    if rule_env and mat_env:
        if rule_env in mat_env or mat_env in rule_env:
            sc += 4.0  # تطابق مباشر
        elif "marine" in rule_env and "marine" not in mat_env:
            return -1e9  # لا نقبل مادة غير مقاومة للبحر
        elif "industrial" in rule_env and "industrial" not in mat_env:
            sc -= 3.0
        else:
            sc += 1.0  # مقبول لكن ليس مثالياً

    # -------- 2) شكل السقف / الميل (Flat vs Pitched) --------
    slope_rule = _safe_str(
        roof_rule.get("Slope_Class")
        or roof_rule.get("Roof_Slope")
        or roof_rule.get("Slope_Range")
    ).lower()

    roof_form = _safe_str(
        mat.get("Roof_Form")
        or mat.get("Suitable_Roof_Type")
        or mat.get("System_Form")
    ).lower()

    if slope_rule and roof_form:
        is_flat_rule = "flat" in slope_rule or "0-2" in slope_rule
        is_pitched_rule = "pitched" in slope_rule or ">" in slope_rule or "2-5" in slope_rule

        is_flat_mat = "flat" in roof_form
        is_pitched_mat = "pitched" in roof_form

        if (is_flat_rule and is_flat_mat) or (is_pitched_rule and is_pitched_mat):
            sc += 3.0
        else:
            sc -= 1.0  # مش مثالي لكنه مو خطأ قاتل

    # -------- 3) توافق النظام الإنشائي --------
    sys_rule = _safe_str(
        roof_rule.get("Roof_System_Type")
        or roof_rule.get("Structural_System")
    ).lower()

    cat = _safe_str(
        mat.get("System_Category")
        or mat.get("Material_Type")
    ).lower()

    # أسقف خرسانية مسطحة → نفضّل أغشية بيتومين / TPO / PVC / EPDM / Liquid / BUR
    if any(x in sys_rule for x in ["rc_slab", "rc_slab_roof", "rc_frame", "flat"]):
        if any(x in cat for x in ["bitumen", "membrane", "tpo", "pvc", "epdm", "single_ply", "liquid", "bur"]):
            sc += 3.0

    # أسقف معدنية / Steel Frame → نفضّل Metal Roofing
    if any(x in sys_rule for x in ["steel", "metal"]):
        if "metal" in cat or "standing_seam" in cat:
            sc += 3.0

    # -------- 4) أهمية المبنى + مقاومة الحريق --------
    proj = _safe_str(roof_rule.get("Project_Type")).lower()
    fire = _safe_str(mat.get("Fire_Resistance_Level")).lower()

    high_importance = proj in ["hospital", "school", "industrial", "commercial"]
    if fire:
        if any(x in fire for x in ["high", "2h", "3h"]):
            sc += 2.0 if high_importance else 1.0
        elif any(x in fire for x in ["medium", "1h"]):
            sc += 1.0 if high_importance else 0.5
        else:
            if high_importance:
                sc -= 2.0

    # -------- 5) المتانة / العمر (Durability) --------
    dur = _safe_str(mat.get("Durability_Level")).lower()
    if dur == "high":
        sc += 1.5
    elif dur == "medium":
        sc += 0.5

    return sc


def select_roof_materials(
    roof_df: Optional[pd.DataFrame],
    roof_rule: pd.Series,
    top_n: int = 3
) -> Optional[pd.DataFrame]:
    """
    يختار أفضل مواد تغطية سقف بناءً على قاعدة الـ Roof المختارة.
    """
    if roof_df is None or roof_df.empty or roof_rule is None:
        return None

    scores = [score_roof_material(row, roof_rule) for _, row in roof_df.iterrows()]
    df = roof_df.copy()
    df["roof_material_score"] = scores
    df = df[df["roof_material_score"] > -1e8].sort_values(
        "roof_material_score", ascending=False
    )

    if df.empty:
        return None

    if top_n is not None and top_n > 0:
        return df.head(top_n)
    return df


def select_foundation_waterproofing(
    best_rule: Optional[pd.Series],
    wp_df: Optional[pd.DataFrame],
    top_n: int = 3
) -> Optional[pd.DataFrame]:
    """
    اختيار أنظمة العزل المائي للأساسات (نسخة محسّنة مع قواعد كيميائية).
    """
    import re

    if best_rule is None or wp_df is None or len(wp_df) == 0:
        return None

    data = wp_df.copy()

    # 0) فلترة منطقة الاستخدام
    if "Application_Area" in data.columns:
        def is_foundation_area(v):
            if pd.isna(v):
                return False
            txt = str(v).lower()
            return any(x in txt for x in ["basement", "foundation", "raft", "buried", "substructure"])
        data = data[data["Application_Area"].apply(is_foundation_area)]
    if len(data) == 0:
        return None

    wp_spec = best_rule.get("Waterproofing_System", "")
    groundwater = norm(best_rule.get("Groundwater_Level", "low"))
    aggressiveness = norm(best_rule.get("Aggressiveness_Class", "normal"))

    # 2) Type filter
    if wp_spec and not pd.isna(wp_spec):
        spec_str = str(wp_spec).lower()
        possible_types = [
            "pvc", "bentonite", "sbs", "app", "bituminous",
            "crystalline", "epdm", "tpo", "polyurea", "cementitious"
        ]
        target_keywords = [k for k in possible_types if k in spec_str]

        if target_keywords:
            search_col = (data["Material_Name"].fillna("") + " " +
                          data["System_Category"].fillna("")).str.lower()
            mask = pd.Series(False, index=data.index)
            for k in target_keywords:
                mask |= search_col.str.contains(k, na=False)
            data = data[mask]

    if len(data) == 0:
        return None

    # 3) Exclude risks
    if "Water_Pressure" in data.columns:
        wp_col = data["Water_Pressure"].astype(str).str.lower()
        if "high" in groundwater or "very_high" in groundwater:
            data = data[~wp_col.str.contains("dampness|no_pressure", regex=True, na=False)]
        else:
            data = data[~wp_col.str.contains("no_pressure", na=False)]
    if len(data) == 0:
        return None

    is_chem_aggr = any(k in aggressiveness for k in ["sulfate", "marine", "saline"])
    if is_chem_aggr and "System_Category" in data.columns:
        sys_cat = data["System_Category"].astype(str).str.lower()
        data = data[~sys_cat.str.contains("bentonite", na=False)]
    if len(data) == 0:
        return None

    # 4) Scoring
    scores = []
    for _, row in data.iterrows():
        sc = 0.0

        life_val = 5.0
        life_str = str(row.get("Life_Span_Years", ""))
        try:
            nums = re.findall(r'\d+', life_str)
            if nums:
                vals = [float(n) for n in nums]
                life_val = sum(vals) / len(vals)
        except Exception:
            pass
        sc += min(life_val, 50) * 0.5

        cost_val = try_float(row.get("Cost_Index", 3.0))
        sc += (5 - cost_val) * 3.0

        name_cat = (str(row.get("Material_Name", "")) + " " +
                    str(row.get("System_Category", ""))).lower()

        if ("high" in groundwater or "very_high" in groundwater) and ("pvc" in name_cat or "tpo" in name_cat):
            sc += 15.0
        if is_chem_aggr and "crystalline" in name_cat:
            sc += 10.0

        scores.append(sc)

    data = data.copy()
    data["final_score"] = scores
    data = data.sort_values("final_score", ascending=False)
    return data.head(top_n)

# ===========================================================
#   FLOORING MATERIALS SELECTION (finishes, not structure)
# ===========================================================

def _get_first_available(row: pd.Series, candidates) -> str:
    """
    يأخذ أول عمود موجود من قائمة أسماء محتملة.
    هذا مفيد لأن ملف Flooring_Materials_Global.xlsx قد يحتوي أسماء مختلفة قليلاً.
    """
    for c in candidates:
        if c in row.index:
            v = row.get(c, "")
            if pd.isna(v):
                continue
            return str(v).strip()
    return ""


# ===========================================================
#   COLUMN RULES HELPERS
# ===========================================================

COL_SEISMIC_ORDER = {
    "low": 1,
    "moderate": 2,
    "high": 3,
    "very_high": 4,
}

AXIAL_ORDER = {"low": 1, "medium": 2, "high": 3}
MOMENT_ORDER = {"low": 1, "medium": 2, "high": 3}
IMPORTANCE_ORDER = {"normal": 1, "high": 2, "very_high": 3}


def _norm(s):
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return str(s).strip().lower()


def _order_val(map_dict, v):
    return map_dict.get(_norm(v), 0)


def score_column_rule(rule_row: pd.Series, crit: Dict[str, Any]) -> float:
    """
    مقياس ذكي لاختيار أفضل قاعدة عمود:

    - لا نسمح بقاعدة زلازل أقل من المطلوب (Hard Constraint)
    - لا نسمح بقوة خرسانة أقل من ما طلبه المستخدم
    """
    # 1) seismic - شرط أمان
    target_seis = crit.get("Seismic_Zone_Level")
    rule_seis = rule_row.get("Seismic_Zone_Level")




    ts = _order_val(COL_SEISMIC_ORDER, target_seis)
    rs = _order_val(COL_SEISMIC_ORDER, rule_seis)

    if rs < ts:
        return -1e9  # مرفوض أمانياً

    score = 0.0

    # --- 0) Structural System HARD: لا نسمح بخلط أنظمة مختلفة
    sys_rule = _c_norm(rule_row.get("Structural_System"))
    sys_user = _c_norm(crit.get("Structural_System"))
    if sys_user and sys_rule and sys_rule != sys_user:
        return -1e9  # رفض تام إذا النظام مختلف (RC vs Steel vs Shear_Wall ...)

    # لو القاعدة مصممة لسيزميك أعلى → كويس
    if rs > ts:
        score += 2.0

    # 2) Axial load
    target_ax = crit.get("Axial_Load_Level")
    rule_ax = rule_row.get("Axial_Load_Level")
    ta = _order_val(AXIAL_ORDER, target_ax)
    ra = _order_val(AXIAL_ORDER, rule_ax)

    if ra < ta:
        score -= 5.0
    else:
        score += (ra - ta) * 1.0

    # 3) Moment level
    target_m = crit.get("Moment_Level")
    rule_m = rule_row.get("Moment_Level")
    tm = _order_val(MOMENT_ORDER, target_m)
    rm = _order_val(MOMENT_ORDER, rule_m)
    if rm < tm:
        score -= 3.0
    else:
        score += (rm - tm) * 0.5

    # 4) Importance level
    imp = rule_row.get("Importance_Level")
    score += _order_val(IMPORTANCE_ORDER, imp) * 1.5

    # 5) Concrete strength
    try:
        fc_min  = float(rule_row.get("Min_Concrete_Strength_MPa", 0) or 0)
        fc_pref = float(rule_row.get("Preferred_Concrete_Strength_MPa", fc_min) or fc_min)
        user_fc = float(crit.get("Min_Concrete_Strength_MPa", fc_min) or fc_min)
    except Exception:
        fc_min = fc_pref = user_fc = 0.0

    # لو القاعدة أقل من اللي طلبه المستخدم → رفض
    if user_fc and fc_min < user_fc:
        return -1e9

    # نكافئ القاعدة اللي قريبة من طلب المستخدم بدون مبالغة
    score += max(0.0, 5.0 - abs(fc_pref - user_fc) * 0.2)

    return score






def choose_best_column_rule(col_df: pd.DataFrame, crit: Dict[str, Any]) -> Optional[pd.Series]:
    """
    منطق شبيه بالأساسات:
    1) Exact: نحاول نطابق Hard + Soft
    2) Relaxed: نخفف فقط Soft
    3) Scoring: نختار الأفضل
    """
    if col_df is None or col_df.empty:
        return None

    hard_cols = [
        "Seismic_Zone_Level",
    ]
    soft_cols = [
        "Project_Type",
        "Structural_System",
        "Column_Role",
        "Story_Level",
        "Axial_Load_Level",
        "Moment_Level",
    ]

    def _filter(df, crit, keys):
        mask = pd.Series(True, index=df.index)
        for k in keys:
            if k not in df.columns:
                continue
            val = crit.get(k)
            if val is None or val == "":
                continue
            col_vals = df[k].astype(str).str.strip().str.lower()
            mask &= (col_vals == str(val).strip().lower())
        return df[mask]

    # 1) exact
    s1 = _filter(col_df, crit, hard_cols + soft_cols)
    if not s1.empty:
        scores = [score_column_rule(row, crit) for _, row in s1.iterrows()]
        s1 = s1.assign(score=scores)
        s1 = s1.sort_values("score", ascending=False)
        return s1.iloc[0]

    # 2) relaxed (hard only)
    s2 = _filter(col_df, crit, hard_cols)
    if not s2.empty:
        scores = [score_column_rule(row, crit) for _, row in s2.iterrows()]
        s2 = s2.assign(score=scores)
        s2 = s2.sort_values("score", ascending=False)
        return s2.iloc[0]

    # لا توجد قاعدة آمنة
    return None

# ============================
#  BEAM RULES (Exact → Relaxed → Scoring)
# ============================

BEAM_SEISMIC_ORDER = {
    "Low": 1,
    "Moderate": 2,
    "High": 3,
    "Very_High": 4,
}

BEAM_LOAD_ORDER = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}

BEAM_SHEAR_ORDER = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}

BEAM_IMPORTANCE_ORDER = {
    "Normal": 1,
    "High": 2,
    "Very_High": 3,
}


def _b_norm(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _b_order_val(map_dict, v):
    return map_dict.get(_b_norm(v), 0)


def score_beam_rule(rule_row: pd.Series, crit: dict) -> float:
    """
    مقياس ذكي للكمرات:
    - Hard:
        * Seismic_Zone_Level: لا نسمح أن تكون القاعدة أخف من المطلوب
        * Min_Concrete_Strength_MPa: لا نسمح بقيمة أقل من طلب المستخدم
    - Soft:
        * Moment_Level / Shear_Level
        * Importance_Level
    """
    score = 0.0

    # 1) Seismic (Hard)
    target_seis = crit.get("Seismic_Zone_Level")
    rule_seis = rule_row.get("Seismic_Zone_Level")

    ts = _b_order_val(BEAM_SEISMIC_ORDER, target_seis)
    rs = _b_order_val(BEAM_SEISMIC_ORDER, rule_seis)

    if rs < ts:
        return -1e9  # مرفوض أمانياً

    if rs > ts:
        score += 2.0  # زلازل أعلى شوية = أمان أكثر

    # 2) Moment (Soft)
    target_m = crit.get("Moment_Level")
    rule_m = rule_row.get("Moment_Level")
    tm = _b_order_val(BEAM_LOAD_ORDER, target_m)
    rm = _b_order_val(BEAM_LOAD_ORDER, rule_m)
    if rm < tm:
        score -= 3.0
    else:
        score += (rm - tm) * 0.5

    # 3) Shear (Soft)
    target_sh = crit.get("Shear_Level")
    rule_sh = rule_row.get("Shear_Level")
    tsh = _b_order_val(BEAM_SHEAR_ORDER, target_sh)
    rsh = _b_order_val(BEAM_SHEAR_ORDER, rule_sh)
    if rsh < tsh:
        score -= 3.0
    else:
        score += (rsh - tsh) * 0.5

    # 4) Importance
    imp = rule_row.get("Importance_Level")
    score += _b_order_val(BEAM_IMPORTANCE_ORDER, imp) * 1.0

    # 5) Concrete strength (Hard + Soft)
    try:
        fc_min  = float(rule_row.get("Min_Concrete_Strength_MPa", 0) or 0)
        fc_pref = float(rule_row.get("Preferred_Concrete_Strength_MPa", fc_min) or fc_min)
        user_fc = float(crit.get("Min_Concrete_Strength_MPa", fc_min) or fc_min)
    except Exception:
        fc_min = fc_pref = user_fc = 0.0

    if fc_min < user_fc:
        return -1e9  # لا نسمح بقيمة أقل من طلب المستخدم

    # نكافئ القاعدة القريبة من طلب المستخدم
    score += max(0.0, 5.0 - abs(fc_pref - user_fc) * 0.2)

    return score


def choose_best_beam_rule(beam_df: pd.DataFrame, crit: dict) -> Optional[pd.Series]:
    """
    اختيار أفضل قاعدة كمرات بثلاث مراحل:
    1) Exact: Hard + Soft
    2) Relaxed: Hard فقط
    3) Scoring: على كل الجدول مع الحفاظ على الأمان
    """
    if beam_df is None or beam_df.empty:
        return None

    hard_cols = ["Seismic_Zone_Level"]
    soft_cols = [
        "Project_Type",
        "Structural_System",
        "Beam_Role",
        "Span_Range_m",
        "Load_Type",
        "Moment_Level",
        "Shear_Level",
        "Environment_Type",
    ]

    def _filter(df: pd.DataFrame, keys) -> pd.DataFrame:
        mask = pd.Series(True, index=df.index)
        for k in keys:
            if k not in df.columns:
                continue
            val = crit.get(k)
            if val is None or val == "":
                continue
            col_vals = df[k].astype(str).str.strip()
            mask &= (col_vals == str(val).strip())
        return df[mask]

    # 1) Exact
    s1 = _filter(beam_df, hard_cols + soft_cols)
    if not s1.empty:
        scores = [score_beam_rule(row, crit) for _, row in s1.iterrows()]
        s1 = s1.assign(score=scores)
        s1 = s1[s1["score"] > -1e8].sort_values("score", ascending=False)
        if not s1.empty:
            return s1.iloc[0]

    # 2) Relaxed (Hard فقط)
    s2 = _filter(beam_df, hard_cols)
    if not s2.empty:
        scores = [score_beam_rule(row, crit) for _, row in s2.iterrows()]
        s2 = s2.assign(score=scores)
        s2 = s2[s2["score"] > -1e8].sort_values("score", ascending=False)
        if not s2.empty:
            return s2.iloc[0]

    # 3) Full scoring
    scores = [score_beam_rule(row, crit) for _, row in beam_df.iterrows()]
    tmp = beam_df.copy()
    tmp["score"] = scores
    tmp = tmp[tmp["score"] > -1e8].sort_values("score", ascending=False)
    if tmp.empty:
        return None
    return tmp.iloc[0]


# ============================
#  SLAB RULES (Exact → Relaxed → Scoring)
# ============================

SLAB_SEISMIC_ORDER = {
    "Low": 1,
    "Moderate": 2,
    "High": 3,
    "Very_High": 4,
}

SLAB_LOAD_ORDER = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}

SLAB_IMPORTANCE_ORDER = {
    "Normal": 1,
    "High": 2,
    "Very_High": 3,
}


def _s_norm(v: Any) -> str:
    """Normalize value for slab ranking."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _s_order_val(map_dict: dict, v: Any) -> int:
    """Get numeric order from mapping dict."""
    return map_dict.get(_s_norm(v), 0)


def score_slab_rule(rule_row: pd.Series, crit: dict) -> float:
    """
    مقياس ذكي لاختيار أفضل قاعدة للسقوف (SLABS) مع الحفاظ على شروط الأمان.
    """
    score = 0.0

    # 1) Seismic (HARD – لا نسمح بأقل من المطلوب)
    target_seis = crit.get("Seismic_Zone_Level")
    rule_seis   = rule_row.get("Seismic_Zone_Level")

    ts = _s_order_val(SLAB_SEISMIC_ORDER, target_seis)
    rs = _s_order_val(SLAB_SEISMIC_ORDER, rule_seis)

    if rs < ts:
        return -1e9  # مرفوض أمانياً

    if rs > ts:
        score += 2.0   # زلازل أعلى قليلاً = أمان أكثر

    # 2) Load level (Soft)
    target_load = crit.get("Load_Level")
    # بعض الجداول قد تستخدم Load_Type بدلاً من Load_Level
    rule_load   = rule_row.get("Load_Level") or rule_row.get("Load_Type")
    tl = _s_order_val(SLAB_LOAD_ORDER, target_load)
    rl = _s_order_val(SLAB_LOAD_ORDER, rule_load)
    if rl < tl:
        score -= 3.0
    else:
        score += (rl - tl) * 0.5

    # 3) Importance (Soft)
    imp = rule_row.get("Importance_Level")
    score += _s_order_val(SLAB_IMPORTANCE_ORDER, imp) * 1.0

    # 4) Concrete strength (HARD + SOFT)
    try:
        fc_min  = float(rule_row.get("Min_Concrete_Strength_MPa", 0) or 0)
        fc_pref = float(rule_row.get("Preferred_Concrete_Strength_MPa", fc_min) or fc_min)
        user_fc = float(crit.get("Min_Concrete_Strength_MPa", fc_min) or fc_min)
    except Exception:
        fc_min = fc_pref = user_fc = 0.0

    # أمان: لا نختار قاعدة أقل من طلب المستخدم
    if fc_min < user_fc:
        return -1e9

    # نكافئ القاعدة القريبة من طلب المستخدم بدون مبالغة
    score += max(0.0, 5.0 - abs(fc_pref - user_fc) * 0.2)

    return score


def choose_best_slab_rule(slab_df: pd.DataFrame, crit: dict) -> Optional[pd.Series]:
    """
    اختيار أفضل قاعدة سقف بثلاث مراحل:
    1) Exact  : Hard + Soft
    2) Relaxed: Hard فقط
    3) Scoring: على كامل الجدول مع الحفاظ على الأمان
    """
    if slab_df is None or slab_df.empty:
        return None

    hard_cols = ["Seismic_Zone_Level"]
    soft_cols = [
        "Project_Type",
        "Structural_System",
        "Slab_Type",
        "Span_Range_m",
        "Load_Level",
        "Environment_Type",
    ]

    def _filter(df: pd.DataFrame, keys) -> pd.DataFrame:
        mask = pd.Series(True, index=df.index)
        for k in keys:
            if k not in df.columns:
                continue
            val = crit.get(k)
            if val is None or val == "":
                continue
            col_vals = df[k].astype(str).str.strip()
            mask &= (col_vals == str(val).strip())
        return df[mask]

    # 1) Exact (Hard + Soft)
    s1 = _filter(slab_df, hard_cols + soft_cols)
    if not s1.empty:
        scores = [score_slab_rule(row, crit) for _, row in s1.iterrows()]
        s1 = s1.assign(score=scores)
        s1 = s1[s1["score"] > -1e8].sort_values("score", ascending=False)
        if not s1.empty:
            return s1.iloc[0]

    # 2) Relaxed (Hard فقط)
    s2 = _filter(slab_df, hard_cols)
    if not s2.empty:
        scores = [score_slab_rule(row, crit) for _, row in s2.iterrows()]
        s2 = s2.assign(score=scores)
        s2 = s2[s2["score"] > -1e8].sort_values("score", ascending=False)
        if not s2.empty:
            return s2.iloc[0]

    # 3) Full scoring على كل الجدول
    scores = [score_slab_rule(row, crit) for _, row in slab_df.iterrows()]
    tmp = slab_df.copy()
    tmp["score"] = scores
    tmp = tmp[tmp["score"] > -1e8].sort_values("score", ascending=False)
    if tmp.empty:
        return None
    return tmp.iloc[0]

# ===========================================================
#   GLOBAL ENGINEERING CONSISTENCY CHECKS
#   فحص عام للتركيبات غير المنطقية هندسياً قبل استخدام القواعد
# ===========================================================

def check_global_consistency(
    project_type: str,
    structural_system: str,
    element_type: str,
    extra: Dict[str, Any],
) -> tuple:
    """
    ترجع:
      (True,  "")  → كل شيء منطقي، كمّل عادي
      (False, msg) → السيناريو غير مقبول هندسياً، اطبع msg وتوقف

    extra: قاموس يختلف حسب العنصر، مثلاً للسقف:
      {
        "Roof_Type": ...,
        "Roof_Slope": ...,
        "Load_Level": ...,
        "Seismic_Zone_Level": ...,
        "Environment_Type": ...,
      }
    """
    pt  = (project_type or "").strip()
    sys = (structural_system or "").strip()
    elem = (element_type or "").strip().lower()

    # نقرأ الأشياء المشتركة لو موجودة
    seismic = extra.get("Seismic_Zone_Level")
    env     = extra.get("Environment_Type")
    load    = extra.get("Load_Level")

    # -----------------------------
    # 1) مثال قوي: Steel_Frame + Podium_Slab + Marine + High/Very_High
    # -----------------------------
    if (
        sys == "Steel_Frame"
        and elem in ["roof", "slab"]
    ):
        roof_type = extra.get("Roof_Type") or extra.get("Slab_Type")
        if (
            roof_type == "Podium_Slab"
            and seismic in ["High", "Very_High"]
            and env == "Marine"
        ):
            msg = (
                "⚠ هذا السيناريو غير عملي إنشائياً ضمن نطاق النظام الخبير:\n"
                "• النظام الإنشائي Steel_Frame يفضَّل معه أسقف خفيفة في المناطق ذات الزلازل العالية.\n"
                "• Podium_Slab عنصر خرساني ثقيل مع بيئة بحرية + زلازل عالية → يزيد المخاطر والتكاليف.\n"
                "→ جرّب أحد الحلول:\n"
                "  - تغيير النظام الإنشائي إلى RC_Frame، أو\n"
                "  - استخدام Roof_Type أخف (Flat_Roof خرساني خفيف أو نظام معدني)، أو\n"
                "  - تخفيف متطلبات الزلازل/البيئة (إن كان ذلك مسموحاً في كود التصميم)."
            )
            return False, msg

    # -----------------------------
    # 2) مكان جاهز لإضافة قواعد أخرى لاحقاً
    #    مثلاً: Span كبير جداً + Slab Type غير مناسب، أو
    #           Retaining_Wall في Soil غير منطقية، إلخ...
    # -----------------------------

    return True, ""

# ===========================================================
#   FOUNDATION MODULE
# ===========================================================

def run_foundation_module(
    project_type: str,
    structural_system: str,
    found_df: pd.DataFrame,
    conc_df: Optional[pd.DataFrame],
    rebar_df: Optional[pd.DataFrame],
    wp_df: Optional[pd.DataFrame],
    soil_type: str,
    groundwater: str,
    seismic: str,
    excavation_risk: str,
    aggressiveness: str,
    user_fc: Optional[float] = None,
):
    """
    وحدة الأساسات:
    - تسأل عن: نوع التربة، المياه الجوفية، الزلازل، خطورة الحفر، عدوانية التربة، و f'c المطلوب
    - تستخدم find_best_foundation_rule_safe لاختيار أفضل قاعدة (Exact → Relaxed → Scoring)
    - ثم تقترح: خرسانة + حديد تسليح + عزل/ووتر بروف للأساسات
    """

    if found_df is None or found_df.empty:
        print("\n⚠ No FOUNDATION rules dataset loaded.\n")
        return

    print("\n=== FOUNDATION DESIGN MODULE (وحدة تصميم الأساسات) ===")

    # 1) Soil type
    soil_options = {
        "1": "Clay",
        "2": "Sand",
        "3": "Gravel",
        "4": "Rock",
        "5": "Mixed_Soil",
        "6": "Soft_Clay",
    }
    soil = choose_from_menu("Soil Type (نوع التربة)", soil_options)

    # 2) Groundwater level
    gwt_options = {
        "1": "Low",
        "2": "Medium",
        "3": "High",
        "4": "Very_High",
    }
    gwt = choose_from_menu("Groundwater Level (منسوب المياه الجوفية)", gwt_options)

    # 3) Seismic zone
    seismic_options = {
        "1": "Low",
        "2": "Moderate",
        "3": "High",
        "4": "Very_High",
    }
    seismic = choose_from_menu("Seismic Zone Level (مستوى منطقة الزلازل)", seismic_options)

    # 4) Excavation risk
    exc_options = {
        "1": "Low",
        "2": "Medium",
        "3": "High",
        "4": "Very_High",
    }
    exc_risk = choose_from_menu("Excavation Risk Level (خطورة الحفر)", exc_options)

    # 5) Soil aggressiveness (chemical)
    aggr_options = {
        "1": "Normal",
        "2": "Medium_Sulfate",
        "3": "High_Sulfate",
        "4": "Marine_Environment",
    }
    aggressiveness = choose_from_menu("Soil Aggressiveness (عدوانية التربة كيميائياً)", aggr_options)

    # 6) Minimum concrete strength (user may override)
    user_fc_in = input(
        "\nMinimum concrete strength required (MPa) "
        "[press Enter to use code value] "
        "(أدنى مقاومة خرسانة مطلوبة - اتركه فارغاً لقيمة الكود): "
    ).strip()
    min_fc_req = try_float(user_fc_in, 0.0)

    # ======= ENGINEERING RULE SELECTION =======
    best_rule = find_best_foundation_rule_safe(
        found_df,
        project_type,
        structural_system,
        soil,
        gwt,
        seismic,
        exc_risk,
        aggressiveness,
        min_fc_req,
    )

    print("\n=== FOUNDATION ENGINEERING DECISION (القرار الهندسي للأساسات) ===")
    if best_rule is None:
        print("❌ No matching design rule found (even after safe relaxation).")
        print("   (لم يتم العثور على قاعدة تصميم مناسبة حتى بعد التخفيف الآمن للقيود)\n")
        return

    # طباعة الـ Series الخام (جميع الأعمدة) — مفيدة للمراجعة الهندسية
    print(best_rule)

    reason = best_rule.get("Reason_Description", "")
    print(f"\nExplanation (الشرح): {reason}\n")

    # ======= MATERIALS SELECTION =======
    conc_sel = select_concrete_for_rule(conc_df, best_rule, top_n=3)
    rebar_sel = select_rebar_for_rule(rebar_df, best_rule, top_n=3)
    wp_sel   = select_foundation_waterproofing(best_rule, wp_df, top_n=3)

    # خرسانة الأساسات
    print("=== Recommended Concrete for Foundations (الخرسانة المقترحة للأساسات) ===")
    pretty_print_concrete(conc_sel)

    # حديد تسليح الأساسات
    print("\n=== Recommended Rebar for Foundations (حديد التسليح المقترح للأساسات) ===")
    pretty_print_rebar(rebar_sel)

    # العزل المائي للأساسات
    print("\n=== Recommended Waterproofing for Foundations (مواد العزل المقترحة للأساسات) ===")
    pretty_print_waterproofing(wp_sel)

    print("\n" + "=" * 70 + "\n")


# ===========================================================
#   BEAM MODULE
# ===========================================================
def run_beam_module(
    project_type: str,
    struct_system: str,
    beam_df: pd.DataFrame,
    conc_df: Optional[pd.DataFrame],
    rebar_df: Optional[pd.DataFrame],
):
# ✅ أولاً: لو النظام إنشائي معدني → نوقف خرسانة وحديد
    if struct_system == "Steel_Frame":
        print("\n" + "=" * 70)
        print("=== STEEL BEAM DESIGN (تصميم الكمرات الفولاذية) ===")
        print("=" * 70)
        print(f"Project Type: {project_type}")
        print(f"Structural System: {struct_system} (نظام معدني)\n")

        print("✅ الكمرات هنا تُنفَّذ كمقاطع فولاذية (Steel Sections)")
        print("❌ خلطات الخرسانة غير مطلوبة هنا.")
        print("❌ حديد التسليح (Rebar) غير مستخدم للكمرات المعدنية.\n")

        print("📐 ملاحظات تصميمية للكمرات الفولاذية:")
        print("- اختيار المقطع من جداول AISC Shapes (W, I, H, Box, Channel ...)")
        print("- التصميم حسب كود AISC 360 LRFD/ASD")
        print("- يعتمد التصميم على:")
        print("  • العزم الأقصى Mu (Moment)")
        print("  • قوى القص Vu (Shear)")
        print("  • طول البحر الفعّال (Span Length)")
        print("  • حالة التثبيت الجانبي (Lateral Bracing)")
        print("  • متطلبات الزلازل (Seismic Detailing) إن وجدت\n")

        print("📎 ملاحظة:")
        print("الحجم النهائي للمقطع الفولاذي يتم اختياره من التحليل الإنشائي،")
        print("ثم مطابقة القوى مع مقاومة المقطع حسب جداول AISC.")
        print("=" * 70)
        return  # ⬅ مهم جداً: نخرج من الدالة ولا نكمّل إلى منطق الخرسانة/الحديد")

    # 👇 بعد هذا الشرط دع باقي كود الكمرات كما هو بالملف (بدون تغيير)
    # باقي منطق الكمرات الخرسانية...
    print("\n" + "=" * 60)
    print("BEAM MODULE (موديول الكمرات)")
    print("=" * 60)

    if beam_df is None or beam_df.empty:
        print("\n⚠ No BEAM rules dataset loaded.\n")
        return

    # ============================================================
    # 1) User Inputs (مدخلات المستخدم)
    # ============================================================

    role_options = {
        "1": "Floor_Beam",
        "2": "Primary_Beam",
        "3": "Secondary_Beam",
        "4": "Edge_Beam",
        "5": "Cantilever_Beam",
    }
    beam_role = choose_from_menu("Beam Role (دور الكمرة)", role_options)

    span_options = {
        "1": "3-5m",
        "2": "5-7m",
        "3": "7-10m",
    }
    span_range = choose_from_menu("Span Range (m) (مدى البحر متر)", span_options)

    load_options = {
        "1": "Uniform",
        "2": "Point",
        "3": "Combined",
    }
    load_type = choose_from_menu("Load Type (نوع الحمل)", load_options)

    moment_options = {
        "1": "Low",
        "2": "Medium",
        "3": "High",
    }
    moment_level = choose_from_menu("Moment Level (مستوى العزم)", moment_options)

    shear_options = {
        "1": "Low",
        "2": "Medium",
        "3": "High",
    }
    shear_level = choose_from_menu("Shear Level (مستوى القص)", shear_options)

    seis_options = {
        "1": "Low",
        "2": "Moderate",
        "3": "High",
        "4": "Very_High",
    }
    seismic_level = choose_from_menu("SEISMIC ZONE LEVEL (for beams) (منطقة الزلازل للكمرات)", seis_options)

    env_options = {
        "1": "Normal",
        "2": "XC2",
        "3": "Marine",
    }
    env_type = choose_from_menu("Environment Type (نوع البيئة)", env_options)

    # Minimum f'c من المستخدم (اختياري)
    fc_in = ask("Minimum Concrete Strength Required (MPa) (أدنى مقاومة خرسانة مطلوبة MPa)")
    user_fc = try_float(fc_in, 0.0)

    # ============================================================
    # 2) Decision Logic
    # ============================================================

    crit = {
        "Project_Type": project_type,
        "Structural_System": struct_system,
        "Beam_Role": beam_role,
        "Span_Range_m": span_range,
        "Load_Type": load_type,
        "Moment_Level": moment_level,
        "Shear_Level": shear_level,
        "Seismic_Zone_Level": seismic_level,
        "Environment_Type": env_type,
    }

    if user_fc > 0:
        crit["Min_Concrete_Strength_MPa"] = user_fc

    best_rule = choose_best_beam_rule(beam_df, crit)

    if best_rule is None:
        print("\n❌ No matching beam design rule found under current constraints.")
        print("   (لم يتم العثور على قاعدة تصميم كمرة مطابقة ضمن الشروط الحالية)\n")
        return

    # ============================================================
    # 3) Output (المخرجات) - عرض القرار الهندسي بشكل منسق
    # ============================================================

    # قيم رئيسية من القاعدة
    rule_id      = best_rule.get("Rule_ID", "N/A")
    proj_type    = best_rule.get("Project_Type", project_type)
    struct_sys   = best_rule.get("Structural_System", struct_system)
    role         = best_rule.get("Beam_Role", beam_role)
    span_rule    = best_rule.get("Span_Range_m", span_range)
    load_rule    = best_rule.get("Load_Type", load_type)
    moment_rule  = best_rule.get("Moment_Level", moment_level)
    shear_rule   = best_rule.get("Shear_Level", shear_level)
    seis_rule    = best_rule.get("Seismic_Zone_Level", seismic_level)
    env_rule     = best_rule.get("Environment_Type", env_type)
    exp_class    = best_rule.get("Exposure_Class_ACI", best_rule.get("Exposure_Class", "N/A"))
    rec_type     = best_rule.get("Recommended_Beam_Type", "RC_Beam")

    min_fc_rule  = best_rule.get("Min_Concrete_Strength_MPa", "N/A")
    pref_fc      = best_rule.get("Preferred_Concrete_Strength_MPa", "N/A")
    min_grade    = best_rule.get("Min_Steel_Grade", "N/A")
    shear_imp    = best_rule.get("Shear_Importance_Level", "N/A")
    defl_ctrl    = best_rule.get("Deflection_Control_Level", "N/A")
    importance   = best_rule.get("Importance_Level", "N/A")
    depth_range  = best_rule.get("Recommended_Depth_Range_mm", "N/A")
    fire_hours   = best_rule.get("Fire_Rating_Hours", "N/A")
    best_use     = best_rule.get("Best_Use_Case", "")
    reason       = best_rule.get("Reason_Description", "")

    print("\n" + "=" * 60)
    print("BEAM ENGINEERING DECISION (القرار الهندسي للكمرة)")
    print("=" * 60)
    print(f"Rule_ID (رقم القاعدة): {rule_id}")
    print(f"Project Type (نوع المشروع): {proj_type}")
    print(f"Structural System (النظام الإنشائي): {struct_sys}")
    print(f"Beam Role (دور الكمرة): {role}")
    print(f"Span Range (مدى البحر): {span_rule}")
    print(f"Load Type (نوع الحمل): {load_rule}")
    print(f"Moment Level (مستوى العزم): {moment_rule}")
    print(f"Shear Level (مستوى القص): {shear_rule}")
    print(f"Seismic Zone Level (مستوى الزلازل): {seis_rule}")
    print(f"Environment Type (نوع البيئة): {env_rule}")
    print(f"Exposure Class ACI (درجة التعرض): {exp_class}")
    print(f"Recommended Beam Type (نوع الكمرة المقترح): {rec_type}")
    print(f"Min f'c (MPa) (أدنى مقاومة خرسانة): {min_fc_rule}")
    print(f"Preferred f'c (MPa) (المقاومة المفضلة): {pref_fc}")
    print(f"Min Steel Grade (أقل درجة حديد): {min_grade}")
    print(f"Shear Importance Level (أهمية مقاومة القص): {shear_imp}")
    print(f"Deflection Control Level (مستوى التحكم بالهبوط): {defl_ctrl}")
    print(f"Importance Level (درجة الأهمية): {importance}")
    print(f"Recommended Depth Range (mm) (مدى العمق المقترح): {depth_range}")
    print(f"Fire Rating (hours) (زمن مقاومة الحريق): {fire_hours}")
    if best_use:
        print(f"Best Use Case (أفضل استخدام): {best_use}")

    # لو المستخدم أدخل f'c بنفسه
    if user_fc > 0:
        print(f"\nUser-specified Min f'c (من المستخدم): {user_fc} MPa")

    print("\nExplanation (الشرح):")
    print(reason)
    print()

    # ============================================================
    # 4) Materials (المواد) – استخدام الـ pretty printers
    # ============================================================

    # خرسانة الكمرات
    print("\n=== Recommended Concrete for Beams (الخرسانة المقترحة للكمرات) ===")
    conc_sel = select_concrete_for_rule(conc_df, best_rule, top_n=3)
    pretty_print_concrete(conc_sel)

    # حديد تسليح الكمرات
    print("\n=== Recommended Rebar for Beams (حديد التسليح المقترح للكمرات) ===")
    rebar_sel = select_rebar_for_rule(rebar_df, best_rule, top_n=3)
    pretty_print_rebar(rebar_sel)

    print("=" * 60 + "\n")


# ===========================================================
#   RETAINING WALL RULES (Scoring-based)
# ===========================================================

RETAIN_SEISMIC_ORDER = {
    "Low": 1,
    "Moderate": 2,
    "High": 3,
    "Very_High": 4,
}

RETAIN_LOAD_ORDER = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}

RETAIN_IMPORTANCE_ORDER = {
    "Normal": 1,
    "High": 2,
    "Very_High": 3,
}


def _rw_norm(v: Any) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _rw_order_val(map_dict: dict, v: Any) -> int:
    return map_dict.get(_rw_norm(v), 0)


def score_retaining_rule(rule_row: pd.Series, crit: dict) -> float:
    """
    مقياس للجدران الساندة:
    - Hard: Seismic, Min_Concrete_Strength
    - Soft: Height_Class / Load_Level / Importance.
    """
    score = 0.0

    # Seismic (HARD)
    target_seis = crit.get("Seismic_Zone_Level")
    rule_seis   = rule_row.get("Seismic_Zone_Level")
    ts = _rw_order_val(RETAIN_SEISMIC_ORDER, target_seis)
    rs = _rw_order_val(RETAIN_SEISMIC_ORDER, rule_seis)
    if rs < ts:
        return -1e9
    if rs > ts:
        score += 2.0

    # Load (Soft – غالباً يعكس ضغط الردم)
    target_load = crit.get("Load_Level")
    rule_load   = rule_row.get("Load_Level")
    tl = _rw_order_val(RETAIN_LOAD_ORDER, target_load)
    rl = _rw_order_val(RETAIN_LOAD_ORDER, rule_load)
    if rl < tl:
        score -= 3.0
    else:
        score += (rl - tl) * 0.5

    # Importance
    imp = rule_row.get("Importance_Level")
    score += _rw_order_val(RETAIN_IMPORTANCE_ORDER, imp) * 1.0

    # Concrete strength
    try:
        fc_min  = float(rule_row.get("Min_Concrete_Strength_MPa", 0) or 0)
        fc_pref = float(rule_row.get("Preferred_Concrete_Strength_MPa", fc_min) or fc_min)
        user_fc = float(crit.get("Min_Concrete_Strength_MPa", fc_min) or fc_min)
    except Exception:
        fc_min = fc_pref = user_fc = 0.0

    if fc_min < user_fc:
        return -1e9

    score += max(0.0, 5.0 - abs(fc_pref - user_fc) * 0.2)

    return score


def choose_best_retaining_rule(ret_df: pd.DataFrame, crit: dict) -> Optional[pd.Series]:
    """
    فلترة تقريبية + Scoring:
    - نحاول نطابق Project_Type / Structural_System / Wall_Function / Height_Class إن وجدت.
    """
    if ret_df is None or ret_df.empty:
        return None

    # نحاول نستخدم هذه الأعمدة لو موجودة
    soft_cols = [
        "Project_Type",
        "Structural_System",
        "Wall_Function",   # مثلاً: Bridge_Abutment / Basement / Garden
        "Height_Class",    # مثلاً: Low / Medium / High
        "Backfill_Type",   # إن وجدت
    ]

    subset = ret_df.copy()
    for col in soft_cols:
        if col not in subset.columns:
            continue
        val = crit.get(col)
        if not val:
            continue
        subset = subset[subset[col].astype(str).str.strip() == str(val).strip()]

    # لو صار subset فارغ → نرجع للجدول كامل
    if subset.empty:
        subset = ret_df

    scores = [score_retaining_rule(r, crit) for _, r in subset.iterrows()]
    subset = subset.assign(score=scores)
    subset = subset[subset["score"] > -1e8].sort_values("score", ascending=False)

    if subset.empty:
        return None
    return subset.iloc[0]



# ===========================================================
#   SLAB MODULE (basic – similar to beams, تستخدم نفس scoring)
# ===========================================================

def run_slab_module(
    project_type: str,
    struct_system: str,
    slab_df: pd.DataFrame,
    conc_df: Optional[pd.DataFrame],
    rebar_df: Optional[pd.DataFrame],
):
    """
    وحدة السلاب: تعتمد على score_slab_rule + فلترة بسيطة.
    """
    if slab_df is None or slab_df.empty:
        print("\n⚠ No SLAB rules dataset loaded.\n")
        return

    print("\n=== SLAB DESIGN MODULE ===")

    slab_type_options = {
        "1": "One_Way_Slab",
        "2": "Two_Way_Slab",
        "3": "Flat_Slab",
    }
    slab_type = choose_from_menu("Slab Type", slab_type_options)

    span_options = {
        "1": "3-5m",
        "2": "5-7m",
        "3": "7-10m",
    }
    span_range = choose_from_menu("Span Range (m)", span_options)

    load_level_options = {
        "1": "Low",
        "2": "Medium",
        "3": "High",
    }
    load_level = choose_from_menu("Load Level", load_level_options)

    seis_options = {
        "1": "Low",
        "2": "Moderate",
        "3": "High",
        "4": "Very_High",
    }
    seismic_level = choose_from_menu("Seismic Zone Level (for slabs)", seis_options)

    env_options = {
        "1": "Normal",
        "2": "XC2",
        "3": "Marine",
    }
    env_type = choose_from_menu("Environment Type", env_options)

    fc_in = input(
        "\nMinimum concrete strength required (MPa) [press Enter to use code value]: "
    ).strip()
    user_fc = try_float(fc_in, 0.0)

    # ===== فحص الاتساق الهندسي العام قبل القواعد =====
    ok, msg = check_global_consistency(
        project_type=project_type,
        structural_system=struct_system,
        element_type="slab",
        extra={
            "Slab_Type": slab_type,
            "Span_Range_m": span_range,
            "Load_Level": load_level,
            "Seismic_Zone_Level": seismic_level,
            "Environment_Type": env_type,
        },
    )

    if not ok:
        print("\n" + msg + "\n")
        return
    # ===== نهاية الفحص العام =====


    crit = {
        "Project_Type": project_type,
        "Structural_System": struct_system,
        "Slab_Type": slab_type,
        "Span_Range_m": span_range,
        "Load_Level": load_level,
        "Seismic_Zone_Level": seismic_level,
        "Environment_Type": env_type,
    }
    if user_fc > 0:
        crit["Min_Concrete_Strength_MPa"] = user_fc

    # فلترة أولية على المشروع/النظام/نوع السقف
    subset = slab_df.copy()
    for col in ["Project_Type", "Structural_System", "Slab_Type"]:
        val = crit.get(col)
        if col in subset.columns and val:
            subset = subset[
                subset[col].astype(str).str.strip() == str(val).strip()
            ]

    if subset.empty:
        subset = slab_df

    scores = [score_slab_rule(r, crit) for _, r in subset.iterrows()]
    subset = subset.assign(score=scores)
    subset = subset[subset["score"] > -1e8].sort_values("score", ascending=False)

    if subset.empty:
        print(
            "\n❌ No matching slab design rule found with current safety constraints.\n"
        )
        return

    best_rule = subset.iloc[0]

    print("\n=== SLAB ENGINEERING DECISION ===")
    print(best_rule)
    print("\nExplanation:", best_rule.get("Reason_Description", ""))

    conc_sel = select_concrete_for_rule(conc_df, best_rule, top_n=3)
    rebar_sel = select_rebar_for_rule(rebar_df, best_rule, top_n=3)

    print("\n=== Recommended Concrete for Slabs ===")
    if conc_sel is not None and not conc_sel.empty:
        print(conc_sel)
    else:
        print("No matching concrete materials.")

    print("\n=== Recommended Rebar for Slabs ===")
    if rebar_sel is not None and not rebar_sel.empty:
        print(rebar_sel)
    else:
        print("No matching rebar materials.")



# ===========================================================
#   COLUMN RULES (Exact → Relaxed → Scoring)
# ===========================================================

COLUMN_SEISMIC_ORDER = {
    "Low": 1,
    "Moderate": 2,
    "High": 3,
    "Very_High": 4,
}

COLUMN_LOAD_ORDER = {
    "Light": 1,
    "Medium": 2,
    "Heavy": 3,
}

COLUMN_IMPORTANCE_ORDER = {
    "Normal": 1,
    "High": 2,
    "Very_High": 3,
}


def _c_norm(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _c_order(map_dict, v):
    return map_dict.get(_c_norm(v), 0)


def score_column_rule(rule_row: pd.Series, crit: dict) -> float:
    """
    نظام اختيار الأعمدة حسب ACI 318 +
    أعلى دقة في الزلازل، الحمل، التعرض، ارتفاع المبنى.
    """
    score = 0.0

    # --- Seismic HARD ---
    ts = _c_order(COLUMN_SEISMIC_ORDER, crit.get("Seismic_Zone_Level"))
    rs = _c_order(COLUMN_SEISMIC_ORDER, rule_row.get("Seismic_Zone_Level"))

    if rs < ts:
        return -1e9  # مرفوض إنشائياً

    if rs > ts:
        score += 2.0

    # --- Load SOFT ---
    tl = _c_order(COLUMN_LOAD_ORDER, crit.get("Load_Level"))
    rl = _c_order(COLUMN_LOAD_ORDER, rule_row.get("Load_Level"))

    if rl < tl:
        score -= 3
    else:
        score += (rl - tl) * 0.7

    # --- Height class ---
    if str(rule_row.get("Height_Class")).strip() == str(crit.get("Height_Class")).strip():
        score += 2.0

    # --- Exposure ---
    exp_rule = _c_norm(rule_row.get("Exposure_Class"))
    exp_user = _c_norm(crit.get("Exposure_Class"))
    if exp_rule == exp_user:
        score += 1.5

    # --- Concrete strength HARD + SOFT ---
    try:
        fc_min  = float(rule_row.get("Min_Concrete_Strength_MPa", 0) or 0)
        fc_pref = float(rule_row.get("Preferred_Concrete_Strength_MPa", fc_min))
        user_fc = float(crit.get("Min_Concrete_Strength_MPa", fc_min))
    except Exception:
        fc_min = fc_pref = user_fc = 0

    if fc_min < user_fc:
        return -1e9

    score += max(0, 5 - abs(fc_pref - user_fc) * 0.2)

    # --- Importance Level ---
    score += _c_order(COLUMN_IMPORTANCE_ORDER, rule_row.get("Importance_Level")) * 1.0

    return score


def choose_best_column_rule(col_df: pd.DataFrame, crit: dict) -> Optional[pd.Series]:
    """
    النظام المكون من 3 مراحل:
    1️⃣ Exact match
    2️⃣ Relaxed match
    3️⃣ Full scoring
    """
    if col_df is None or col_df.empty:
        return None

    hard = ["Seismic_Zone_Level"]
    soft = [
        "Project_Type",
        "Structural_System",
        "Column_Position",
        "Load_Level",
        "Height_Class",      # أو Slenderness_Level حسب داتاسيتك
        "Exposure_Class",
    ]

    def _filter(df, cols):
        mask = pd.Series(True, index=df.index)
        for k in cols:
            if k not in df.columns:
                continue
            v = crit.get(k)
            if not v:
                continue
            mask &= (df[k].astype(str).str.strip() == str(v).strip())
        return df[mask]

    # 1) Exact
    s1 = _filter(col_df, hard + soft)
    if not s1.empty:
        s1 = s1.copy()
        s1["score"] = [score_column_rule(r, crit) for _, r in s1.iterrows()]
        s1 = s1[s1["score"] > -1e8].sort_values("score", ascending=False)
        if not s1.empty:
            return s1.iloc[0]

    # 2) Relaxed
    s2 = _filter(col_df, hard)
    if not s2.empty:
        s2 = s2.copy()
        s2["score"] = [score_column_rule(r, crit) for _, r in s2.iterrows()]
        s2 = s2[s2["score"] > -1e8].sort_values("score", ascending=False)
        if not s2.empty:
            return s2.iloc[0]

    # 3) Full scoring
    scores = [score_column_rule(r, crit) for _, r in col_df.iterrows()]
    tmp = col_df.copy()
    tmp["score"] = scores
    tmp = tmp[tmp["score"] > -1e8].sort_values("score", ascending=False)
    return tmp.iloc[0] if not tmp.empty else None
# ===========================================================
#   ran coluom module
# ===========================================================
def run_column_module(
    project_type: str,
    structural_system: str,
    col_df: pd.DataFrame,
    conc_df: Optional[pd.DataFrame],
    rebar_df: Optional[pd.DataFrame],
    # هذه القيم تأتي من الواجهة (Streamlit)
    height_class: str = "Low_Rise",     # Low_Rise / Medium_Rise / High_Rise
    load_level: str = "Medium",         # Light / Medium / Heavy
    col_position: str = "Interior",     # Interior / Edge / Corner
    seismic: str = "Moderate",          # Low / Moderate / High / Very_High
    exposure: str = "XC2",              # XC1 / XC2 / XC3 / XC4
    user_fc: Optional[float] = None,    # MPa (يمكن تركها None)
):
    """
    COLUMN MODULE (وحدة تصميم الأعمدة)
    - نسخة مخصّصة للواجهة (لا تستخدم input())
    - تعتمد بالكامل على البارامترات القادمة من Streamlit
    """

    # ==========================================================
    # 0) حالة النظام المعدني Steel_Frame → أعمدة فولاذية فقط
    # ==========================================================
    if structural_system == "Steel_Frame":
        print("\n" + "=" * 70)
        print("=== STEEL COLUMN DESIGN (تصميم الأعمدة الفولاذية) ===")
        print("=" * 70)

        print(f"Project Type (نوع المشروع): {project_type}")
        print(f"Structural System (النظام الإنشائي): {structural_system}")
        print("Element (العنصر): COLUMN (عمود)\n")

        print("✅ The column is designed as a *STEEL SECTION*.")
        print("❌ Concrete mixes are NOT applicable for a pure steel frame.")
        print("❌ Reinforcement bars (rebar) are NOT applicable here.\n")

        print("📐 Engineering Guidance (توجيه هندسي عام):")
        print("- Use AISC 360 for steel column design.")
        print("- Select a suitable steel section (W / H / I / Box).")
        print("- Design based on:")
        print("  • Axial load (القوة المحورية)")
        print("  • Bending moments (العزوم)")
        print("  • Slenderness / buckling (النحافة والانبعاج)")
        print("  • Seismic requirements (متطلبات الزلازل إن وجدت)")
        print("\n📎 Note:")
        print("Use the AISC Shapes table + results from structural analysis")
        print("to choose the final steel section dimensions.\n")

        print("=" * 70)
        return  # ⚠ مهم: نخرج من الدالة ولا نختار خرسانة أو حديد

    # ==========================================================
    # 1) التحقق من وجود قواعد الأعمدة
    # ==========================================================
    if col_df is None or col_df.empty:
        print("\n⚠ No COLUMN rules dataset loaded. (لا توجد قواعد تصميم للأعمدة)\n")
        return

    print("\n" + "=" * 70)
    print("=== COLUMN DESIGN MODULE (وحدة تصميم الأعمدة) ===")
    print("=" * 70)

    # ==========================================================
    # 2) بناء معايير الاختيار من مدخلات الواجهة
    # ==========================================================
    criteria = {
        "Project_Type":       project_type,
        "Structural_System":  structural_system,
        "Height_Class":       height_class,
        "Load_Level":         load_level,
        "Column_Position":    col_position,
        "Seismic_Zone_Level": seismic,
        "Exposure_Class":     exposure,
    }

    # لو المستخدم حدد f'c أكبر من صفر نضيفها كشرط
    if user_fc is not None and user_fc > 0:
        criteria["Min_Concrete_Strength_MPa"] = user_fc

    # ==========================================================
    # 3) اختيار أفضل قاعدة تصميم للأعمدة
    # ==========================================================
    best_rule = choose_best_column_rule(col_df, criteria)

    if best_rule is None:
        print("\n❌ No matching column design rule found.")
        print("   (لا توجد قاعدة تصميم أعمدة مطابقة للمعايير المدخلة)\n")
        return

    # ==========================================================
    # 4) طباعة القرار الهندسي للأعمدة بشكل منسّق
    # ==========================================================
    print("\n" + "=" * 70)
    print("=== COLUMN ENGINEERING DECISION (القرار الهندسي للعمود) ===")
    print("=" * 70)

    def _g(key: str, default=""):
        return best_rule.get(key, default)

    print(f"Rule ID (رقم القاعدة): {_g('Rule_ID')}")
    print(f"Project Type (نوع المشروع): {_g('Project_Type')}")
    print(f"Structural System (النظام الإنشائي): {_g('Structural_System')}")
    print(f"Height Class (تصنيف ارتفاع المبنى): {_g('Height_Class')}")
    print(f"Load Level (مستوى الحمل): {_g('Load_Level')}")
    print(f"Column Position (موضع العمود): {_g('Column_Position')}")
    print(f"Seismic Zone Level (مستوى منطقة الزلازل): {_g('Seismic_Zone_Level')}")
    print(f"Exposure Class (درجة التعرض البيئي): {_g('Exposure_Class')}")
    print(f"Min f'c (MPa) (أدنى مقاومة خرسانة مطلوبة): {_g('Min_Concrete_Strength_MPa')}")
    print(f"Preferred f'c (MPa) (المقاومة الخرسانية المفضلة): {_g('Preferred_Concrete_Strength_MPa')}")
    print(f"Min Steel Grade (أقل درجة حديد تسليح): {_g('Min_Steel_Grade')}")
    print(f"Fire Rating (ساعات مقاومة الحريق): {_g('Fire_Rating_Hours')}")
    print(f"Importance Level (درجة الأهمية): {_g('Importance_Level')}")
    print(f"Primary Design Code (الكود الأساسي): {_g('Primary_Design_Code')}")
    print(f"Secondary Design Code (الكود الثانوي): {_g('Secondary_Design_Code')}")

    print("\nBest Use Case (أفضل استخدام):")
    print(_g("Best_Use_Case", ""))

    print("\nExplanation (شرح القرار):")
    print(_g("Reason_Description", ""))

    # ==========================================================
    # 5) اختيار المواد (فقط للأنظمة الخرسانية)
    # ==========================================================
    rc_like_systems = {"RC_Frame", "Dual_System", "Shear_Wall"}

    if structural_system in rc_like_systems:
        # ---- الخرسانة ----
        print("\n=== Recommended Concrete for Columns (الخرسانة المقترحة للأعمدة) ===")
        conc_sel = None
        if conc_df is not None:
            conc_sel = select_concrete_for_rule(conc_df, best_rule, top_n=3)
        pretty_print_concrete(conc_sel)

        # ---- حديد التسليح ----
        print("\n=== Recommended Rebar for Columns (حديد التسليح المقترح للأعمدة) ===")
        rebar_sel = None
        if rebar_df is not None:
            rebar_sel = select_rebar_for_rule(rebar_df, best_rule, top_n=3)
        pretty_print_rebar(rebar_sel)

    else:
        # لأي نظام آخر غير معرف
        print("\n⚠ No material module configured for this structural system.")
        print("   (لا يوجد موديول مواد لهذا النظام الإنشائي حالياً.)")



# ===========================================================
#   MAIN CONTROLLER
# ===========================================================

def run_expert_system(datasets: Dict[str, pd.DataFrame]):

    # نقرأ الداتا من القاموس الجاهز

    found_df = datasets.get("foundations_rules")
    columns_df = datasets.get("columns_rules")
    beams_df = datasets.get("beams_rules")
    slabs_df = datasets.get("slabs_rules")
    walls_df = datasets.get("walls_rules")
    retaining_df = datasets.get("retaining_rules")

    roofing_df = datasets.get("roofing_rules")
    flooring_df = datasets.get("flooring_rules")

    conc_df = datasets.get("concrete_materials")
    rebar_df = datasets.get("rebar_materials")
    wp_df = datasets.get("waterproofing_materials")

    roofing_mat_df = datasets.get("roofing_materials")
    flooring_mat_df = datasets.get("flooring_materials")




    # --- Project Type ---
    project_options = {
        "1": "Hospital",
        "2": "Residential",
        "3": "Industrial",
        "4": "School",
        "5": "Bridge",
        "6": "Tunnel",
        "7": "Warehouse",
        "8": "Parking",
        "9": "Commercial",
    }
    project = choose_from_menu(
        "Project Type (نوع المشروع)",
        project_options,
        PROJECT_TYPE_AR
    )

    # --- Structural System ---
    system_options = {
        "1": "RC_Frame",
        "2": "Steel_Frame",
        "3": "Shear_Wall",
        "4": "Dual_System",
    }
    system = choose_from_menu(
        "Structural System (النظام الإنشائي)",
        system_options,
        STRUCT_SYSTEM_AR
    )

    # --- Structural Element ---
    element_options = {
        "1": "foundation",
        "2": "column",
        "3": "beam",
        "4": "slab",
        "5": "wall",
        "6": "roof",
        "7": "flooring",
        # "8": "retaining_wall",
    }
    element = choose_from_menu(
        "Structural Element (العنصر الإنشائي)",
        element_options,
        ELEMENT_AR
    )

    # -------- DISPATCH --------
    if element == "foundation":
        run_foundation_module(
            project, system,
            found_df,
            conc_df,
            rebar_df,
            wp_df,
        )

    elif element == "column":
        run_column_module(project, system, datasets)

    elif element == "beam":
        run_beam_module(
            project, system,
            beams_df,
            conc_df,
            rebar_df,
        )

    elif element == "slab":
        run_slab_module(
            project, system,
            slabs_df,
            conc_df,
            rebar_df,
        )


# ===========================================================
#   DATA LOADER + MAIN LOOP
# ===========================================================

from pathlib import Path

# كاش للداتا حتى لا نحمّلها كل مرة (اختياري لكنه مفيد)
DATASETS_CACHE: Optional[Dict[str, pd.DataFrame]] = None


def main_loop():
    print("🚀 Loading all datasets once ... (تحميل جميع بيانات المشروع مرة واحدة)")
    datasets = load_all_datasets()
    print("✅ All datasets loaded. (تم تحميل جميع البيانات)\n")

    while True:
        run_expert_system(datasets)
        again = input("\nRun another scenario? (y/n) (تشغيل سيناريو آخر؟ y/n): ").strip().lower()
        if again != "y":
            print("\nExiting expert system. (إنهاء النظام الخبير)\n")
            break
# ===========================================================
#  PROJECT PROFILES (منطق عالي المستوى لنوع المشروع)
# ===========================================================
PROJECT_TYPE_PROFILES = {
    "Default": {
        "title_en": "General Building",
        "title_ar": "مبنى عام",
        "structural_systems": [
            "RC Frame (إطار خرساني) للمشاريع العامة",
            "Steel Frame (إطار معدني) للمساحات الكبيرة والمصانع",
            "Dual System (نظام مزدوج) للمناطق الزلزالية"
        ],
        "walls_partitions": [
            "Concrete Block (بلوك إسمنتي) للجدران",
            "AAC Blocks (بلوك خفيف عازل) لتقليل الوزن والعزل",
            "Drywall (جبس بورد) للقواطع الداخلية"
        ],
        "ceilings": [
            "Gypsum board ceiling (سقف جبس بورد مستعار)",
            "Mineral tiles 60x60 (بلاطات 60×60) للصيانة"
        ],
        "flooring": [
            "Porcelain/Ceramic (بورسلين/سيراميك) للأماكن العامة",
            "Epoxy (إيبوكسي) للمناطق الصناعية",
            "Vinyl (فينيل) للممرات عالية الحركة"
        ],
        "insulation": [
            "Roof waterproofing membrane (لفائف عزل السطح)",
            "XPS thermal insulation (ألواح XPS للعزل الحراري)",
            "Rockwool sound insulation (صوف صخري لعزل الصوت)"
        ],
        "finishes": [
            "Washable paint (دهان قابل للغسل)",
            "HPL/Wall protection (حماية جدران بالممرات عند الحاجة)"
        ],
        "engineering_notes": [
            "هذه توصيات عامة وليست بديلاً عن التصميم وفق الكود."
        ],
    },

    "Hospital": {
        "title_en": "Hospital",
        "title_ar": "مستشفى",
        "structural_systems": [
            "RC Frame + Flat Slab (خرساني + بلاطات لا كمرية) لتمديدات MEP",
            "Steel option for atrium/lobbies (معدني للبهو الواسع عند الحاجة)"
        ],
        "walls_partitions": [
            "Exterior: AAC Blocks / insulated systems (خارجي: بلوك AAC أو نظام معزول)",
            "Interior: Multi-layer Drywall + Rockwool (قواطع: جبس متعدد + صوف صخري)",
            "X-Ray rooms: Lead-lined boards (غرف أشعة: ألواح مبطنة بالرصاص)"
        ],
        "ceilings": [
            "Corridors: 60x60 hygienic tiles (ممرات: بلاطات صحية قابلة للفك)",
            "OR/ICU: seamless gypsum + special paint (عمليات/عناية: جبس مصمت بدون فواصل)"
        ],
        "flooring": [
            "No carpets/wood (منع السجاد والخشب الطبيعي)",
            "Patient rooms: Homogeneous Vinyl welded (فينيل متجانس بلحام حراري)",
            "OR: Anti-static Vinyl (فينيل مضاد للكهرباء الساكنة)",
            "Lobby: Granite/Terrazzo (جرانيت/تيرازو)"
        ],
        "insulation": [
            "Sound insulation priority (الأولوية لعزل الصوت)",
            "Roof: Membrane + XPS/PU (عزل سطح مزدوج)"
        ],
        "finishes": [
            "Anti-bacterial washable paints (دهانات مضادة للبكتيريا)",
            "Impact protection rails (مصدات/درابزين حماية للجدران)"
        ],
        "engineering_notes": [
            "الأولوية: النظافة + المتانة + سهولة الصيانة."
        ],
    },

    "School": {
        "title_en": "School",
        "title_ar": "مدرسة",
        "structural_systems": [
            "RC Frame (إطار خرساني) اقتصادي وسهل التنفيذ",
            "Shear walls optional (جدران قص عند الحاجة الزلزالية)"
        ],
        "walls_partitions": [
            "Concrete block (بلوك إسمنتي) خارجي",
            "Drywall محدود في الصفوف حسب المتانة (جبس بورد عند الحاجة)"
        ],
        "ceilings": [
            "60x60 tiles for maintenance (بلاطات للصيانة)",
            "Gypsum in offices (جبس للمكاتب)"
        ],
        "flooring": [
            "Porcelain/Ceramic high durability (بورسلين عالي التحمل)",
            "Anti-slip in toilets (مقاوم انزلاق للحمامات)"
        ],
        "insulation": [
            "Thermal insulation (عزل حراري) حسب المناخ",
            "Roof waterproofing (عزل سطح)"
        ],
        "finishes": [
            "Washable paint (دهان قابل للغسل)",
            "Corner guards (حماية زوايا بالممرات)"
        ],
        "engineering_notes": [
            "الأولوية: المتانة + سهولة الصيانة + كلفة اقتصادية."
        ],
    },

    "Restaurant": {
        "title_en": "Restaurant",
        "title_ar": "مطعم",
        "structural_systems": [
            "RC Frame (إطار خرساني)",
            "Steel for large open dining hall (معدني لقاعات واسعة)"
        ],
        "walls_partitions": [
            "Kitchen areas: moisture-resistant boards (مناطق المطبخ: مقاوم رطوبة)",
            "Fire-rated partitions where needed (قواطع مقاومة للحريق عند الحاجة)"
        ],
        "ceilings": [
            "Easy-to-clean ceilings (أسقف سهلة التنظيف)",
            "Access panels for MEP (فتحات صيانة)"
        ],
        "flooring": [
            "Kitchen: Anti-slip + chemical resistant (مطبخ: مقاوم انزلاق ومواد كيميائية)",
            "Dining: Porcelain/Terrazzo (صالة: بورسلين/تيرازو)"
        ],
        "insulation": [
            "Grease/waterproof protection in kitchen zones (عزل مناطق الشحوم والرطوبة)",
            "Roof system حسب التعرض (حسب التعرض البيئي)"
        ],
        "finishes": [
            "Washable paints (دهانات قابلة للغسل)",
            "HPL/tiles near wet zones (تكسيات قرب مناطق الرطوبة)"
        ],
        "engineering_notes": [
            "الأولوية: مقاومة الانزلاق + النظافة + مقاومة الرطوبة."
        ],
    },

    "Residential": {
        "title_en": "Residential Building",
        "title_ar": "سكني",
        "structural_systems": [
            "RC Frame (إطار خرساني) الأكثر شيوعاً",
            "Dual System للمناطق الزلزالية (حسب الكود)"
        ],
        "walls_partitions": [
            "Exterior: AAC/Block with insulation (خارجي: بلوك + عزل)",
            "Interior: Drywall/Brick (داخلي: جبس/طابوق حسب الرغبة)"
        ],
        "ceilings": [
            "Gypsum false ceiling (سقف مستعار جبس)",
            "Direct plaster finish (لياسة مباشرة)"
        ],
        "flooring": [
            "Living: Porcelain/ceramic (بورسلين/سيراميك)",
            "Bedrooms: HDF/wood options (HDF/بدائل خشب)",
            "Bathrooms: Anti-slip ceramic (سيراميك مقاوم انزلاق)"
        ],
        "insulation": [
            "Roof waterproofing + thermal insulation (عزل سطح + حراري)",
            "Wet areas waterproofing (عزل حمامات)"
        ],
        "finishes": [
            "Standard paint + washable in kitchens (دهان عادي + قابل للغسل بالمطبخ)",
            "Facade options حسب الميزانية (حسب الميزانية)"
        ],
        "engineering_notes": [
            "الأولوية: راحة المستخدم + عزل حراري + كلفة متوسطة."
        ],
    },

    "Industrial": {
        "title_en": "Industrial Facility",
        "title_ar": "منشأة صناعية",
        "structural_systems": [
            "Steel Frame (هيكل معدني) للمساحات الواسعة",
            "RC in heavy equipment zones (خرساني لمناطق المعدات الثقيلة)"
        ],
        "walls_partitions": [
            "Sandwich panels / metal cladding (ساندوتش بانل/كسوة معدنية)",
            "Fire-rated walls where required (جدران مقاومة حريق عند الحاجة)"
        ],
        "ceilings": [
            "Usually exposed سقف مكشوف (عادة سقف مكشوف)",
            "Local suspended ceilings في المكاتب فقط"
        ],
        "flooring": [
            "Epoxy heavy duty (إيبوكسي صناعي عالي التحمل)",
            "Hardener concrete topping (تقسية سطح الخرسانة)"
        ],
        "insulation": [
            "Roof thermal insulation (عزل حراري للسقف)",
            "Chemical resistant systems حسب البيئة (حسب المواد الكيميائية)"
        ],
        "finishes": [
            "Durable coatings (دهانات صناعية)",
            "Anti-corrosion systems (مقاومة تآكل)"
        ],
        "engineering_notes": [
            "الأولوية: التحمل + مقاومة كيماوية + سلامة حريق."
        ],
    },

    "Warehouse": {
        "title_en": "Warehouse",
        "title_ar": "مخزن",
        "structural_systems": [
            "Steel Frame (هيكل معدني)",
            "RC option for heavy storage racks (خرساني للأحمال العالية)"
        ],
        "walls_partitions": [
            "Sandwich panels (ساندوتش بانل)",
            "Block walls near impact zones (بلوك بمناطق الصدمات)"
        ],
        "ceilings": [
            "Exposed سقف مكشوف غالباً",
        ],
        "flooring": [
            "Hardener concrete / Epoxy (خرسانة مقساة/إيبوكسي)",
        ],
        "insulation": [
            "Roof waterproofing (عزل سطح)",
            "Thermal insulation حسب التخزين (حسب نوع التخزين)"
        ],
        "finishes": [
            "Minimal finishes (تشطيبات بسيطة)",
        ],
        "engineering_notes": [
            "الأولوية: اقتصاد + سرعة تنفيذ + تحمل حركة رافعات."
        ],
    },

    "Parking": {
        "title_en": "Parking Structure",
        "title_ar": "موقف سيارات",
        "structural_systems": [
            "RC Frame (خرساني) شائع جداً",
            "Precast option (مسبق الصب) لتسريع التنفيذ"
        ],
        "walls_partitions": [
            "Ventilated blocks/screens (جدران تهوية/شاشات)",
        ],
        "ceilings": [
            "Exposed concrete (خرسانة ظاهرة) + coatings",
        ],
        "flooring": [
            "Anti-slip + abrasion resistant (مقاوم انزلاق واهتراء)",
            "Epoxy/Pu deck coatings (طلاءات إيبوكسي/PU)"
        ],
        "insulation": [
            "Waterproofing for top deck (عزل سطح الطابق العلوي)",
            "Joint sealing (عزل فواصل)"
        ],
        "finishes": [
            "Protective coatings + markings (دهانات حماية + تخطيط أرضي)"
        ],
        "engineering_notes": [
            "الأولوية: مقاومة اهتراء + أملاح + عزل فواصل."
        ],
    },

    "Commercial": {
        "title_en": "Commercial Building",
        "title_ar": "تجاري",
        "structural_systems": [
            "RC Frame (خرساني)",
            "Steel for large spans/shops (معدني للبحور الكبيرة)"
        ],
        "walls_partitions": [
            "Facade systems حسب المعمار (حسب التصميم المعماري)",
            "Interior partitions flexible (قواطع داخلية مرنة)"
        ],
        "ceilings": [
            "False ceilings for MEP (أسقف مستعارة لتمديدات الخدمات)"
        ],
        "flooring": [
            "High traffic porcelain/terrazzo (بورسلين/تيرازو عالي الحركة)",
            "Epoxy in back-of-house (إيبوكسي بمناطق الخدمة)"
        ],
        "insulation": [
            "Roof waterproofing + thermal (عزل سطح + حراري)",
            "Facade insulation حسب الواجهة (حسب الواجهة)"
        ],
        "finishes": [
            "Durable finishes + easy maintenance (تشطيبات متينة)"
        ],
        "engineering_notes": [
            "الأولوية: تحمل حركة عالية + صيانة سهلة."
        ],
    },

    "Bridge": {
        "title_en": "Bridge",
        "title_ar": "جسر",
        "structural_systems": [
            "Pre-stressed concrete (خرسانة مسبقة الإجهاد)",
            "Steel girders (جسور حديدية) حسب البحر"
        ],
        "walls_partitions": [],
        "ceilings": [],
        "flooring": [],
        "insulation": [
            "Waterproofing deck membrane (عزل سطح الجسر)",
        ],
        "finishes": [
            "Protective coatings (دهانات حماية)",
        ],
        "engineering_notes": [
            "هذا القسم توصيات عامة — تصميم الجسور يحتاج تحليل متخصص وفق الكود."
        ],
    },

    "Tunnel": {
        "title_en": "Tunnel",
        "title_ar": "نفق",
        "structural_systems": [
            "RC lining (بطانة خرسانية مسلحة)",
            "Precast segments (قطاعات مسبقة الصب)"
        ],
        "walls_partitions": [],
        "ceilings": [],
        "flooring": [],
        "insulation": [
            "High performance waterproofing (عزل عالي الأداء)",
            "Drainage systems (تصريف)"
        ],
        "finishes": [
            "Fire protection coatings (حماية حريق)",
        ],
        "engineering_notes": [
            "الأولوية: العزل + التصريف + مقاومة الحريق."
        ],
    },
}
def get_project_profile(project_type: str) -> dict | None:
    """
    يرجع بروفايل المشروع (أنظمة + مواد مقترحة)
    - إذا نوع المشروع غير معرّف: يرجع None (حتى الواجهة تعرض رسالة واضحة)
    """
    return PROJECT_TYPE_PROFILES.get(project_type)

# =========================
# WALLS EXPERT MODULE (Hybrid: PKL hard-rules + Excel KB)
# Place this at the END of: src/expert_system.py
# =========================



from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
import pickle

# Pandas optional but recommended (you already use Excel elsewhere likely)
try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None  # will raise later if Excel is used without pandas


# ---------- Paths (project-root safe) ----------
_THIS_FILE = Path(__file__).resolve()
BASE_DIR = _THIS_FILE.parents[1]          # .../construction-expert-system
DATASET_DIR = BASE_DIR / "dataset"

WALLS_RULES_PKL = DATASET_DIR / "Walls_Rules_ACI_Global.pkl"
WALLS_PARTITIONS_XLSX = DATASET_DIR / "walls_partitions_materials.xlsx"


# ---------- In-memory cache (loads once) ----------
_WALLS_CACHE: Dict[str, Any] = {
    "rules": None,
    "materials_df": None,
}


# ---------- Small helpers ----------
def _norm(x: Any) -> str:
    return str(x).strip().lower().replace(" ", "_")

def _pick(profile: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """Pick first existing key from profile (supports alternative key names)."""
    for k in keys:
        if k in profile and profile[k] is not None and str(profile[k]).strip() != "":
            return profile[k]
    return default

def _safe_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, tuple):
        return list(x)
    return [x]


# =========================
# 1) Loaders
# =========================

def load_walls_rules() -> Any:
    """
    Loads PKL rules once. We don't assume exact structure;
    later we normalize rules into a list of dicts when applying.
    """
    if _WALLS_CACHE["rules"] is None:
        if not WALLS_RULES_PKL.exists():
            raise FileNotFoundError(f"Walls rules PKL not found: {WALLS_RULES_PKL}")
        with open(WALLS_RULES_PKL, "rb") as f:
            _WALLS_CACHE["rules"] = pickle.load(f)
    return _WALLS_CACHE["rules"]

def load_walls_materials_df():
    """Loads Excel KB once."""
    if _WALLS_CACHE["materials_df"] is None:
        if pd is None:
            raise RuntimeError("pandas is required to read Excel files for walls KB.")
        if not WALLS_PARTITIONS_XLSX.exists():
            raise FileNotFoundError(f"Walls materials Excel not found: {WALLS_PARTITIONS_XLSX}")
        _WALLS_CACHE["materials_df"] = pd.read_excel(WALLS_PARTITIONS_XLSX)
    return _WALLS_CACHE["materials_df"]


# =========================
# 2) Core logic
# =========================

def classify_wall_context(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decide whether walls are structural/load-bearing or partitions based on structural system.
    Also read wall zone and room type.
    """
    structural_system = _norm(_pick(profile, ["structural_system", "system", "structure_system", "system_type"], "frame"))
    wall_zone = _norm(_pick(profile, ["wall_zone", "zone", "wall_location", "location"], "internal"))  # internal/external
    room_type = _norm(_pick(profile, ["room_type", "space_type", "room", "space"], ""))               # bathroom/kitchen/bedroom/office/...

    # Domain decision
    if structural_system in ("load_bearing", "bearing_walls", "loadbearing", "shear_wall", "shear_walls", "core", "dual"):
        domain = "structural"
        domain_reason = "النظام الإنشائي يعتمد على الجدران (حاملة/قص) → نطبق قوانين صارمة للجدران الإنشائية."
    else:
        domain = "partition"
        domain_reason = "النظام هيكلي (أعمدة/كمرات) → الجدران قواطع/قشرة معمارية (Partitions)."

    # Wet areas helper
    wet = room_type in ("bathroom", "kitchen", "wet", "wc", "toilet") or bool(profile.get("wet_areas", False))

    return {
        "structural_system": structural_system,
        "wall_zone": wall_zone,
        "room_type": room_type,
        "wet": wet,
        "domain": domain,
        "domain_reason": domain_reason
    }

# =========================================================
# FLOORING — Expert Module (Logic + Scoring + Package)
# =========================================================

def _floor_tags(name: str) -> set:
    n = str(name).lower().replace(" ", "_")
    tags = set()

    # ceramics & stones
    if "porcelain" in n or "بورسلين" in n:
        tags.add("porcelain")
    if "ceramic" in n or "سيراميك" in n:
        tags.add("ceramic")
    if "granite" in n or "جرانيت" in n:
        tags.add("granite")
    if "marble" in n or "رخام" in n:
        tags.add("marble")
    if "terrazzo" in n or "تيرازو" in n:
        tags.add("terrazzo")

    # wood family
    if "hardwood" in n or "خشب_طبيعي" in n:
        tags.add("hardwood")
    if "engineered" in n or "hdf" in n or "laminate" in n or "باركيه" in n:
        tags.add("engineered_wood")

    # resilient
    if "vinyl" in n or "lvt" in n or "pvc" in n or "فينيل" in n:
        tags.add("vinyl")
    if "epoxy" in n or "ايبوكسي" in n:
        tags.add("epoxy")
    if "carpet" in n or "moquette" in n or "موكيت" in n:
        tags.add("carpet")

    # anti-slip hints
    if "r11" in n or "r12" in n or "anti_slip" in n or "anti-slip" in n:
        tags.add("anti_slip")

    # polished hint
    if "polished" in n or "لامع" in n:
        tags.add("polished")

    # families
    if tags & {"ceramic", "porcelain", "granite", "marble", "terrazzo"}:
        tags.add("hard_surface")
    if tags & {"hardwood", "engineered_wood", "carpet"}:
        tags.add("soft_surface")
    if tags & {"vinyl", "epoxy"}:
        tags.add("resilient_surface")

    return tags


def _space_class(room_type: str) -> str:
    r = str(room_type).lower()
    if r in ["bathroom", "kitchen", "wc", "toilet", "pool", "laundry"]:
        return "wet"
    if r in ["corridor", "hall", "lobby", "entrance"]:
        return "circulation"
    if r in ["office", "meeting", "conference", "classroom"]:
        return "work"
    if r in ["bedroom", "living", "family", "home_cinema"]:
        return "residential"
    if r in ["parking", "warehouse", "workshop", "industrial", "storage", "mechanical"]:
        return "industrial"
    return "general"


def _infer_traffic(project_type: str, room_type: str) -> str:
    p = str(project_type).lower()
    r = str(room_type).lower()

    # high traffic defaults
    if p in ["hospital", "school", "mall", "airport", "station", "government"]:
        return "high"
    if r in ["corridor", "lobby", "entrance"]:
        return "high"
    if r in ["parking", "warehouse", "industrial"]:
        return "very_high"
    return "medium"


def assess_floor_engineering_confidence(result: dict, profile: dict) -> dict:
    best = result.get("best") or {}
    mat = (best.get("material") or "")
    tags = _floor_tags(mat)

    project_type = profile.get("project_type", "")
    room_type = profile.get("room_type", "")
    fire_req = str(profile.get("fire_rating", "")).lower()
    humidity = str(profile.get("humidity", "")).lower()
    budget = str(profile.get("budget", "")).lower()
    wet = bool(profile.get("wet_areas", False)) or _space_class(room_type) == "wet"
    traffic = profile.get("traffic") or _infer_traffic(project_type, room_type)

    flags, recs = [], []

    # Wet area slip + material sanity
    if wet:
        if "carpet" in tags or "hardwood" in tags or "engineered_wood" in tags:
            flags.append("💧 منطقة رطبة: الخشب/الموكيت غير مناسب بسبب الانتفاخ والعفن وصعوبة التعقيم.")
            recs.append("استخدم Porcelain Anti-slip (R11/R12) أو Vinyl Sheet للمستشفيات أو Epoxy حسب الاستخدام.")
        if ("marble" in tags) and ("polished" in tags) and ("anti_slip" not in tags):
            flags.append("⚠️ رخام مصقول في منطقة رطبة: خطر انزلاق عالي.")
            recs.append("اختر سطح خشن/Anti-slip أو استبدل ببورسلين R11/R12.")

    # Hospital hygiene logic (seams/bacteria)
    if str(project_type).lower() == "hospital":
        if not ("vinyl" in tags or "epoxy" in tags or "terrazzo" in tags):
            flags.append("🏥 مستشفى: يفضّل أرضيات قليلة الفواصل وسهلة التعقيم (Vinyl Sheet / Epoxy / Terrazzo).")
            recs.append("للممرات وغرف المرضى: Homogeneous Vinyl Sheet؛ للمختبرات/الخدمات: Epoxy.")

    # Traffic logic
    if traffic in ["high", "very_high"]:
        if "ceramic" in tags and "porcelain" not in tags and "granite" not in tags and "terrazzo" not in tags:
            flags.append("🚶 حركة عالية: السيراميك العادي قد يتشقق/يتآكل أسرع من البورسلين/التيرازو/الجرانيت.")
            recs.append("اختر Full-body Porcelain أو Terrazzo أو Granite حسب الميزانية.")
        if "hardwood" in tags:
            flags.append("🚶 حركة عالية: الخشب الطبيعي يحتاج صيانة عالية وقد يتضرر.")
            recs.append("بديل: LVT تجاري أو Porcelain بنقشة خشب.")

    # Budget vs marble
    if budget == "low" and ("marble" in tags):
        flags.append("💰 ميزانية منخفضة: الرخام غالبًا خيار مكلف وصيانته أعلى.")
        recs.append("بديل اقتصادي: Porcelain كبير بنقشة رخام.")

    # Fire requirement (general note)
    if fire_req == "high" and ("carpet" in tags):
        flags.append("🔥 متطلبات حريق عالية: تأكد من تصنيف الحريق للموكيت (Flame spread) حسب الكود.")
        recs.append("بديل آمن: Vinyl/Porcelain/terrazzo بتصنيف مناسب.")

    if any(f.startswith("🔥") or "خطر" in f for f in flags):
        confidence, risk_level = "Low", "High"
    elif flags:
        confidence, risk_level = "Medium", "Warning"
    else:
        confidence, risk_level = "High", "None"

    return {"confidence": confidence, "risk_level": risk_level, "flags": flags, "recommendations": recs}


def infer_flooring(profile: dict) -> dict:
    """
    profile expected keys (مثل الجدران):
      project_type, room_type, humidity, fire_rating, budget, wet_areas(optional)
      + optional: traffic, level ("ground" / "upper")
    """
    project_type = profile.get("project_type", "Residential")
    room_type = profile.get("room_type", "general")
    humidity = str(profile.get("humidity", "medium")).lower()
    fire_req = str(profile.get("fire_rating", "medium")).lower()
    budget = str(profile.get("budget", "medium")).lower()
    level = str(profile.get("level", "upper")).lower()

    wet = bool(profile.get("wet_areas", False)) or _space_class(room_type) == "wet"
    space_class = _space_class(room_type)
    traffic = profile.get("traffic") or _infer_traffic(project_type, room_type)

    # ---- Load materials list from cached datasets (reuse your existing cache pattern)
    # Try to reuse an existing dataset cache if you already have it.
    # Otherwise load from dataset_cache pkls similar to other modules.
    mats = []
    try:
        # if you already have a global cache function, use it
        # from your codebase: load_all_datasets() or get_datasets()
        # but keep it simple: attempt a known cache dict if exists
        global _DATASETS_CACHE  # if your project uses it
        df = None
        if isinstance(globals().get("_DATASETS_CACHE"), dict):
            df = _DATASETS_CACHE.get("flooring_materials")
        if df is None:
            # fallback: try to load from dataset_cache (pickle)
            import pickle
            from pathlib import Path

            base = Path(__file__).resolve().parent.parent  # project root guess (src/..)
            pkl = base / "dataset_cache" / "flooring_materials.pkl"
            if not pkl.exists():
                # another common name
                pkl = base / "dataset_cache" / "flooring_materials_global.pkl"
            if pkl.exists():
                with open(pkl, "rb") as f:
                    df = pickle.load(f)

        # if df is a dataframe, read material column
        if df is not None:
            # flexible column names
            cols = [c.lower() for c in getattr(df, "columns", [])]
            name_col = None
            for cand in ["material", "name", "name_en", "id", "code"]:
                if cand in cols:
                    name_col = df.columns[cols.index(cand)]
                    break
            if name_col is None and len(getattr(df, "columns", [])) > 0:
                name_col = df.columns[0]
            mats = [str(x) for x in df[name_col].dropna().tolist()]
    except Exception:
        mats = []

    # If materials list empty, still return a safe structure
    result = {
        "context": {
            "module": "flooring",
            "project_type": project_type,
            "room_type": room_type,
            "space_class": space_class,
            "wet": wet,
            "traffic": traffic,
            "level": level,
        },
        "hard_rules": {"blocked": []},
        "best": None,
        "alternatives": [],
    }

    if not mats:
        result["hard_rules"]["blocked"].append({"material": "N/A", "reason": "⚠️ لم يتم العثور على مواد أرضيات في dataset_cache. تأكد من توليد flooring_materials.pkl"})
        result["engineering_check"] = assess_floor_engineering_confidence(result, profile)
        return result

    ranked = []
    blocked = []

    for mat in mats:
        tags = _floor_tags(mat)
        score = 50.0
        why, warnings = [], []

        # ---- Hard blocks (expert rules)
        if wet:
            if "carpet" in tags or "hardwood" in tags or "engineered_wood" in tags:
                blocked.append({"material": mat, "reason": "💧 ممنوع في مناطق رطبة (خشب/موكيت)."})
                continue
            if ("marble" in tags) and ("polished" in tags) and ("anti_slip" not in tags):
                warnings.append("⚠️ رخام مصقول: احتمال انزلاق في الرطوبة.")

        if str(project_type).lower() == "hospital":
            # push seamless/hygienic
            if "vinyl" in tags:
                score += 14; why.append("🏥 مستشفى: Vinyl مناسب للتعقيم وتقليل الفواصل.")
            if "epoxy" in tags:
                score += 10; why.append("🏥 مستشفى: Epoxy مناسب للخدمات/المختبرات.")
            if "carpet" in tags:
                blocked.append({"material": mat, "reason": "🏥 ممنوع بالمستشفى (صعب التعقيم ويجمع بكتيريا)."})
                continue

        # ---- Wet logic preferences
        if wet:
            if "porcelain" in tags:
                score += 12; why.append("💧 منطقة رطبة: Porcelain مقاوم للماء.")
            if "ceramic" in tags:
                score += 6; why.append("💧 منطقة رطبة: Ceramic مناسب حسب الجودة.")
            if "anti_slip" in tags:
                score += 10; why.append("🦶 Anti-slip (R11/R12) للسلامة.")
            if "vinyl" in tags:
                score += 8; why.append("💧 Vinyl مناسب للماء والفواصل أقل.")

        # ---- Acoustic preference
        acoustic = str(profile.get("acoustic", "medium")).lower()
        if acoustic == "high":
            if "vinyl" in tags:
                score += 8; why.append("🔇 عزل صوتي: Vinyl يقلل صوت الخطوات.")
            if "carpet" in tags:
                score += 10; why.append("🔇 موكيت يعطي أفضل عزل صوتي (إذا مسموح).")
            if "hard_surface" in tags and not ("vinyl" in tags):
                score -= 4; warnings.append("🔇 سطح صلب قد يزيد صوت الخطوات بدون طبقة عزل تحته.")

        # ---- Traffic
        if traffic in ["high", "very_high"]:
            if "porcelain" in tags or "granite" in tags or "terrazzo" in tags:
                score += 10; why.append("🚶 حركة عالية: تحمل ممتاز.")
            if "ceramic" in tags and "porcelain" not in tags:
                score -= 6; warnings.append("🚶 حركة عالية: قد يتآكل/يتشقق أسرع من البورسلين.")
            if "engineered_wood" in tags or "hardwood" in tags:
                score -= 8; warnings.append("🚶 حركة عالية: الخشب يتضرر ويتطلب صيانة.")

        # ---- Budget
        if budget == "low":
            if "marble" in tags or "granite" in tags:
                score -= 10; warnings.append("💰 مكلف نسبيًا للميزانية المنخفضة.")
            if "ceramic" in tags or "vinyl" in tags:
                score += 4; why.append("💰 مناسب للميزانية.")

        # ---- Level logic (ground floor moisture)
        if level in ["ground", "slab_on_grade", "grade"]:
            # not blocking, just add package notes later
            pass

        ranked.append({
            "material": mat,
            "score": round(score, 2),
            "why": why,
            "warnings": warnings,
            "package": {}  # filled later for best only
        })

    result["hard_rules"]["blocked"] = blocked

    ranked.sort(key=lambda x: x["score"], reverse=True)
    best = ranked[0] if ranked else None
    alts = ranked[1:3] if len(ranked) > 1 else []

    if best:
        # Build Floor Assembly package
        pkg_notes = []
        if level in ["ground", "slab_on_grade", "grade"]:
            pkg_notes.append("✅ إضافة DPM (Damp Proof Membrane) أسفل الأرضية لمنع صعود الرطوبة (Slab on Grade).")

        if wet:
            pkg_notes.append("✅ استخدم Grout مقاوم للماء + سيليكون عند الزوايا + ميول تصريف حسب الحاجة.")
            if "anti_slip" not in _floor_tags(best["material"]):
                pkg_notes.append("⚠️ يفضّل اختيار درجة Anti-slip (R11/R12) في المناطق الرطبة لتقليل الانزلاق.")

        # Generic assembly
        best["package"] = {
            "base_material": best["material"],
            "binder": "مونة/لاصق مناسب لنوع الأرضية (Tile Adhesive أو Screed حسب النظام)",
            "layers": [
                "طبقة تسوية (Screed) حسب الحاجة",
                "لاصق (Adhesive) أو مونة أسمنتية",
                "طبقة المادة النهائية (Tiles/Vinyl/...)",
                "ترويبة/لحام فواصل (Grout أو Heat-weld للـ Vinyl sheet)"
            ],
            "accessories": [
                "Skirting (نعلة) حسب نوع الأرضية",
                "Expansion Joints (فواصل تمدد) عند الأبواب/المساحات الكبيرة",
                "Spacers/Leveling System للبلاط"
            ],
            "notes": pkg_notes
        }

    result["best"] = best
    result["alternatives"] = alts

    # Engineering Risk Flag
    result["engineering_check"] = assess_floor_engineering_confidence(result, profile)
    return result

# =========================
# 3) Hard rules (PKL): block / force
# =========================

def _normalize_rules(rules_obj: Any) -> List[Dict[str, Any]]:
    """
    Try to normalize PKL content into list[dict].
    Supports:
      - list of dict rules
      - dict with "rules" key
      - pandas DataFrame (if stored) -> to_dict("records")
    """
    if rules_obj is None:
        return []

    # pandas DataFrame
    if pd is not None and hasattr(rules_obj, "to_dict") and hasattr(rules_obj, "columns"):
        try:
            return rules_obj.to_dict("records")
        except Exception:
            pass

    # dict container
    if isinstance(rules_obj, dict):
        if "rules" in rules_obj and isinstance(rules_obj["rules"], list):
            return [r for r in rules_obj["rules"] if isinstance(r, dict)]
        # if it's already a single rule dict
        if "if" in rules_obj and "action" in rules_obj:
            return [rules_obj]
        # otherwise unknown dict
        return []

    # list container
    if isinstance(rules_obj, list):
        return [r for r in rules_obj if isinstance(r, dict)]

    return []


def apply_wall_hard_rules(ctx: Dict[str, Any], rules_obj: Any) -> Dict[str, Any]:
    """
    Returns:
      {
        "blocked": [{"material": "...", "reason": "..."}],
        "forced":  [{"material": "...", "reason": "..."}]
      }
    Rule formats accepted (flexible):
      A) {"if": {"wall_function": "structural"}, "action":"block", "material":"AAC", "reason":"..."}
      B) Flat columns: wall_function/action/material/reason
    """
    rules = _normalize_rules(rules_obj)

    blocked: List[Dict[str, str]] = []
    forced: List[Dict[str, str]] = []

    wall_function = ctx["domain"]  # "structural" or "partition"
    wall_zone = ctx["wall_zone"]   # internal/external
    wet = ctx["wet"]

    for r in rules:
        cond = r.get("if", {})
        action = _norm(r.get("action", r.get("Action", "")))
        material = r.get("material", r.get("Material", r.get("name", r.get("Name"))))
        reason = r.get("reason", r.get("Reason", ""))

        # Support flat rule style
        flat_wall_fn = r.get("wall_function", r.get("Wall_Function", r.get("function")))
        flat_zone = r.get("wall_zone", r.get("Wall_Zone", r.get("zone")))
        flat_wet = r.get("wet", r.get("Wet", None))

        # Evaluate conditions (best-effort)
        ok = True

        # condition by dict
        if isinstance(cond, dict) and cond:
            if "wall_function" in cond and _norm(cond["wall_function"]) != _norm(wall_function):
                ok = False
            if "wall_zone" in cond and _norm(cond["wall_zone"]) not in ("any", "") and _norm(cond["wall_zone"]) != _norm(wall_zone):
                ok = False
            if "wet" in cond and bool(cond["wet"]) != bool(wet):
                ok = False

        # condition by flat keys
        if flat_wall_fn is not None and _norm(flat_wall_fn) != _norm(wall_function):
            ok = False
        if flat_zone is not None and _norm(flat_zone) not in ("any", "") and _norm(flat_zone) != _norm(wall_zone):
            ok = False
        if flat_wet is not None and bool(flat_wet) != bool(wet):
            ok = False

        if not ok:
            continue

        if not material:
            continue

        material_str = str(material).strip()

        if action == "block":
            blocked.append({"material": material_str, "reason": str(reason or "ممنوع حسب قواعد النظام.")})
        elif action == "force":
            forced.append({"material": material_str, "reason": str(reason or "إجباري حسب قواعد النظام.")})

    # Extra built-in hard rules (safety net)
    # 1) In structural wall function, block typical partition-only systems if they somehow appear
    if wall_function == "structural":
        for m in ["drywall", "gypsum", "gypsum_board", "aac", "siporex", "glass"]:
            blocked.append({"material": m, "reason": "جدار إنشائي: مواد القواطع لا تُستخدم كحائط حامل."})

    # 2) Wet area blocks common gypsum (unless MR, but we block by default)
    if wet:
        blocked.append({"material": "drywall", "reason": "منطقة رطبة: يُمنع الجبس بورد العادي (استخدم Cement Board أو بلوك/طابوق أسمنتي)."})
        blocked.append({"material": "gypsum_board", "reason": "منطقة رطبة: استخدم مقاوم رطوبة أو Cement Board."})

    # 3) External walls: block glass/drywall as general systems
    if wall_zone == "external":
        blocked.append({"material": "drywall", "reason": "جدار خارجي: الجبس بورد ليس نظام واجهة عام."})
        blocked.append({"material": "glass", "reason": "الزجاج يحتاج نظام واجهات متخصص وليس كجدار مباني عام."})

    return {"blocked": blocked, "forced": forced}


# =========================
# 4) Materials (Excel KB): filter + scoring
# =========================

def _guess_name_column(df) -> str:
    # Try common name columns
    for col in df.columns:
        c = _norm(col)
        if c in ("name", "material", "material_name", "اسم", "المادة", "material_ar", "material_en"):
            return col
    # fallback first column
    return df.columns[0]

def _col_exists(df, key_norm: str) -> Optional[str]:
    for col in df.columns:
        if _norm(col) == key_norm:
            return col
    return None

def _material_matches_block(material_name: str, blocked_set: set) -> bool:
    n = _norm(material_name)
    # if blocked list contains a keyword, match loosely
    for b in blocked_set:
        if not b:
            continue
        bb = _norm(b)
        if bb == n:
            return True
        if bb in n:
            return True
    return False

def _material_tags(material_name: str) -> set:
    n = str(material_name).lower().replace(" ", "_")
    tags = set()

    if "gypsum" in n or "drywall" in n:
        tags.add("gypsum")
    if "mr" in n or "moist" in n:
        tags.add("mr")
    if "fr" in n or "fire" in n or "type_x" in n or "typex" in n:
        tags.add("fr")

    if "aac" in n or "siporex" in n:
        tags.add("aac")

    if "cement_board" in n or ("cement" in n and "board" in n):
        tags.add("cement_board")

    if "block" in n or "cmu" in n:
        tags.add("block")

    if "brick" in n or "clay" in n:
        tags.add("brick")

    if "glass" in n:
        tags.add("glass")

    # فئة عامة ثقيلة (masonry)
    if "brick" in tags or "block" in tags:
        tags.add("masonry")

    return tags


def _room_class(room_type: str) -> str:
    r = str(room_type).lower()
    if r in ["bathroom", "kitchen", "wc", "toilet"]:
        return "wet"
    if r in ["corridor", "hall", "lobby", "escape", "exit"]:
        return "corridor"
    if r in ["office", "meeting", "conference", "classroom"]:
        return "work"
    if r in ["bedroom", "living", "family", "home_cinema"]:
        return "residential"
    if r in ["service", "mechanical", "electrical", "storage"]:
        return "service"
    return "general"




def score_wall_candidates(df, profile: Dict[str, Any], ctx: Dict[str, Any], hard: Dict[str, Any]) -> List[Dict[str, Any]]:
    wall_zone = ctx["wall_zone"]
    room_type = ctx["room_type"]
    wet = ctx["wet"]
    domain = ctx["domain"]

    climate = _norm(_pick(profile, ["climate", "environment", "env"], ""))
    humidity = _norm(_pick(profile, ["humidity", "moisture", "humid"], "medium"))
    fire_req = _norm(_pick(profile, ["fire_rating", "fire", "fire_requirement"], "medium"))
    acoustic = _norm(_pick(profile, ["acoustic", "sound", "acoustic_requirement"], "medium"))
    budget = _norm(_pick(profile, ["budget", "cost_level", "budget_level"], "medium"))

    name_col = _guess_name_column(df)

    # Try optional columns if exist
    col_zone = _col_exists(df, "wall_zone") or _col_exists(df, "zone") or _col_exists(df, "location")
    col_domain = _col_exists(df, "wall_function") or _col_exists(df, "function") or _col_exists(df, "category")
    col_thermal = _col_exists(df, "thermal") or _col_exists(df, "u_value") or _col_exists(df, "insulation")
    col_moist = _col_exists(df, "moisture_resistance") or _col_exists(df, "moisture") or _col_exists(df, "water_resistance")
    col_fire = _col_exists(df, "fire") or _col_exists(df, "fire_resistance") or _col_exists(df, "fire_rating")
    col_acoustic = _col_exists(df, "acoustic") or _col_exists(df, "sound") or _col_exists(df, "sound_insulation")
    col_weight = _col_exists(df, "weight") or _col_exists(df, "density")
    col_cost = _col_exists(df, "cost") or _col_exists(df, "price")

    blocked_set = {b.get("material") for b in hard.get("blocked", []) if isinstance(b, dict)}
    forced_set = {f.get("material") for f in hard.get("forced", []) if isinstance(f, dict)}

    ranked: List[Dict[str, Any]] = []

    for _, row in df.iterrows():
        mat = str(row.get(name_col, "")).strip()
        if not mat:
            continue

        # Hard block (loose match)
        if _material_matches_block(mat, blocked_set):
            continue

        # Filter by zone/function if Excel provides it
        if col_zone:
            z = _norm(row.get(col_zone, ""))
            if z and z not in ("any", "both", "internal_external"):
                if wall_zone not in z:
                    # e.g. "external" must match
                    continue

        if col_domain:
            fn = _norm(row.get(col_domain, ""))
            if fn and fn not in ("any", ""):
                if domain not in fn:
                    continue

        # Base score
        score = 50.0
        why: List[str] = []
        warnings: List[str] = []


        # ---- Zone logic ----
        if wall_zone == "external":
            score += 5
            why.append("جدار خارجي: نركز على العزل والمتانة.")
        else:
            score += 3
            why.append("جدار داخلي: نركز على الصوت والوزن وسرعة التنفيذ.")

        # ---- Thermal (external) ----
        if wall_zone == "external" and col_thermal:
            t = _norm(row.get(col_thermal, ""))
            if t in ("high", "excellent", "good"):
                score += 15
                why.append("عزل حراري مناسب للواجهات.")
        # ---- Moisture (wet/ humid) ----
        if (wet or humidity == "high" or "humid" in climate or "coastal" in climate) and col_moist:
            m = _norm(row.get(col_moist, ""))
            if m in ("high", "excellent", "good"):
                score += 12
                why.append("مقاومة رطوبة جيدة.")
            else:
                score -= 8
                warnings.append("قد لا يكون أفضل خيار للرطوبة العالية.")

        # ---- Fire ----
        if fire_req == "high" and col_fire:
            f = _norm(row.get(col_fire, ""))
            if f in ("high", "excellent", "good"):
                score += 10
                why.append("يلبي متطلبات مقاومة الحريق.")

        # ---- Acoustic ----
        if acoustic == "high" and col_acoustic:
            a = _norm(row.get(col_acoustic, ""))
            if a in ("high", "excellent", "good"):
                score += 10
                why.append("يدعم العزل الصوتي.")

        # ---- Weight / density ----
        if col_weight:
            w = _norm(row.get(col_weight, ""))
            # handle numeric density if exists
            try:
                wd = float(row.get(col_weight))
                # lighter is better for frame systems / partitions
                if domain == "partition" and wd > 0:
                    if wd < 1200:
                        score += 8; why.append("خفيف نسبيًا ويقلل الأحمال الميتة.")
                    elif wd > 2000:
                        score -= 6; warnings.append("ثقيل وقد يزيد الأحمال الميتة بدون فائدة إنشائية في نظام الأعمدة.")
            except Exception:
                if domain == "partition":
                    if w in ("light", "low"):
                        score += 8; why.append("خفيف يقلل الأحمال الميتة.")
                    if w in ("heavy", "high"):
                        score -= 6; warnings.append("ثقيل وقد يزيد الأحمال الميتة.")

        # ---- Cost ----
        if col_cost:
            c = _norm(row.get(col_cost, ""))
            if budget == "low" and c in ("low", "cheap", "economic"):
                score += 8; why.append("خيار اقتصادي.")
            if budget == "low" and c in ("high", "expensive"):
                score -= 8; warnings.append("الكلفة قد تكون مرتفعة مقارنة بالميزانية.")

        # ---- Built-in room logic fallback ----
        if wet and _norm(mat) in ("drywall", "gypsum", "gypsum_board"):
            score -= 30
            warnings.append("غرفة رطبة: الجبس العادي غير مناسب (اختر Cement Board أو بلوك/طابوق أسمنتي).")
            # ========= Expert Scoring Layer (GLOBAL FIX) =========
            tags = _material_tags(mat)
            rclass = _room_class(room_type)

            # 1) Acoustic HIGH: نفضل أنظمة Partition الصوتية (Gypsum + Rockwool)
            if acoustic == "high":
                if ctx["domain"] == "partition":
                    if "gypsum" in tags:
                        score += 12;
                        why.append("Acoustic عالي: الجبس مع حشوة (Rockwool) يعطي عزل صوتي أفضل للمساحات الداخلية.")
                    if "masonry" in tags:
                        score -= 6;
                        warnings.append(
                            "Acoustic عالي: الجدران الثقيلة ليست أفضل خيار كقواطع بالمكاتب/الغرف مقارنة بنظام جبس+عزل.")

            # 2) Office/Work spaces: نفضل المرونة/سرعة التنفيذ/التعديل
            if rclass == "work" and ctx["domain"] == "partition":
                if "gypsum" in tags:
                    score += 8;
                    why.append("مساحات عمل: الجبس أسرع وأفضل مرونة للتعديلات والتمديدات.")
                if "masonry" in tags:
                    score -= 8;
                    warnings.append("مساحات عمل: الطابوق/البلوك أثقل وأبطأ ولا يعطي ميزة كقواطع في نظام أعمدة.")

            # 3) Wet areas / humidity high: نفضل Cement Board أو Block ونشدّد على MR
            if wet or humidity == "high":
                if "cement_board" in tags:
                    score += 10;
                    why.append("رطوبة/مناطق رطبة: Cement Board مناسب.")
                if "gypsum" in tags and "mr" in tags:
                    score += 6;
                    why.append("جبس MR مناسب للرطوبة المتوسطة/العالية.")
                if "gypsum" in tags and "mr" not in tags:
                    score -= 18;
                    warnings.append("رطوبة عالية: الجبس العادي غير مناسب.")

            # 4) Fire requirement: نرفع FR ونحذر من غير FR عندما fire=high
            if fire_req == "high":
                if "fr" in tags:
                    score += 12;
                    why.append("Fire عالي: مادة/نظام Fire Rated.")
                elif "gypsum" in tags:
                    score -= 10;
                    warnings.append("Fire عالي: الجبس يجب أن يكون FR (Type X) وليس عادي/MR فقط.")
                elif "masonry" in tags:
                    score += 6;
                    why.append("Fire عالي: الماسونري غالبًا أفضل أداء بالحريق (حسب النظام والتفاصيل).")

            # 5) Partition weight penalty (Value engineering عام)
            if ctx["domain"] == "partition":
                if "masonry" in tags:
                    score -= 4  # عقوبة خفيفة عامة لمنع فوز الطابوق على حلول أخف بلا سبب
            # =====================================================

        ranked.append({
            "material": mat,
            "score": round(score, 1),
            "why": why,
            "warnings": warnings
        })

    # Force rules: bring forced materials to top if present
    if forced_set:
        ranked.sort(key=lambda x: (not _material_matches_block(x["material"], forced_set), -x["score"]))
    else:
        ranked.sort(key=lambda x: -x["score"])

    return ranked


# =========================
# 5) Output package (full system)
# =========================

def build_wall_package(material_name: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a "system package" even if Excel doesn't have detailed columns.
    (You can later expand by mapping exact accessories per material.)
    """
    mat_n = _norm(material_name)

    # Default package
    package = {
        "base_material": material_name,
        "binder": "مونة/لاصق حسب نوع المادة",
        "accessories": ["روابط/زوايا عند التقاء الخرسانة", "شبك (Mesh) لتقليل التشققات", "معالجة فواصل"],
        "lintels": "عتبات خرسانية/جاهزة فوق الأبواب والنوافذ حسب الفتحات"
    }

    # Smart packages
    if "aac" in mat_n or "siporex" in mat_n:
        package["binder"] = "غراء خاص AAC (Thin-bed adhesive)"
        package["accessories"] = ["زوايا/روابط معدنية للربط مع الأعمدة", "شبك فايبر (Mesh) عند اللياسة لمنع التشققات"]
        package["lintels"] = "عتبات خرسانية جاهزة فوق الفتحات"
    elif "drywall" in mat_n or "gypsum" in mat_n:
        package["binder"] = "براغي + معجون فواصل + شريط"
        package["accessories"] = ["هيكل معدني (Metal studs)", "Rockwool (اختياري للعزل الصوتي)", "ألواح مقاومة حريق/رطوبة حسب الحاجة"]
        package["lintels"] = "يعالج ضمن الهيكل المعدني فوق الفتحات"
    elif "cement" in mat_n and "board" in mat_n:
        package["binder"] = "براغي + مواد عزل + معجون مناسب"
        package["accessories"] = ["غشاء عزل مائي (Waterproofing membrane)", "هيكل معدني مقاوم للصدأ", "فواصل مانعة لتسرب الماء"]
    elif "block" in mat_n or "blook" in mat_n or "cmu" in mat_n or "brick" in mat_n:
        package["binder"] = "مونة أسمنتية (أسمنت + رمل)"
        package["accessories"] = ["شبك معدني عند التقاء الجدار بالخرسانة", "روابط (Anchors) مع الأعمدة/الكمرات"]
        package["lintels"] = "عتبات خرسانية مسلحة جاهزة/مصبوبه بالموقع"

    # Context-aware hints
    if ctx["wall_zone"] == "external":
        package.setdefault("notes", [])
        package["notes"] = _safe_list(package.get("notes"))
        package["notes"].append("للواجهات: يمكن اعتماد جدار مزدوج + طبقة عزل (Rockwool/XPS) حسب متطلبات U-Value.")
    if ctx["wet"]:
        package.setdefault("notes", [])
        package["notes"] = _safe_list(package.get("notes"))
        package["notes"].append("للمناطق الرطبة: اعتمد عزل مائي جيد قبل التشطيب (سيراميك/دهان).")

    return package
def assess_wall_engineering_confidence(result: dict, profile: dict) -> dict:
    """
    يرجّع:
      - confidence: High / Medium / Low
      - risk_level: None / Warning / High
      - flags: قائمة أسباب واضحة
      - recommendations: ما الذي يجب تغييره أو التحقق منه
    """
    ctx = result.get("context", {})
    best = result.get("best") or {}
    mat = (best.get("material") or "").lower()

    wall_zone = str(profile.get("wall_zone", "")).lower()
    room_type = str(profile.get("room_type", "")).lower()
    fire_req  = str(profile.get("fire_rating", "")).lower()
    humidity  = str(profile.get("humidity", "")).lower()
    wet = bool(profile.get("wet_areas", False)) or room_type in ["bathroom", "kitchen"]

    flags = []
    recs = []

    # 1) Fire logic (مهم جدًا للممرات ومسارات الهروب)
    if fire_req == "high":
        # إذا المادة Gypsum لكنها ليست Fire Rated (FR/Type X) → خطر
        gypsum_like = ("gypsum" in mat) or ("drywall" in mat)
        fire_rated_hint = ("fr" in mat) or ("fire" in mat) or ("type_x" in mat) or ("typex" in mat)

        if room_type in ["corridor", "escape", "stair", "stairs", "exit"]:
            if gypsum_like and not fire_rated_hint:
                flags.append("🔥 متطلبات الحريق عالية + (Corridor): الجبس MR وحده قد لا يحقق تصنيف الحريق المطلوب (لازم Fire Rated/Type X).")
                recs.append("اعتمد Fire Rated Gypsum (Type X/FR) + عدد طبقات حسب الكود (مثل 1hr/2hr).")
        else:
            if gypsum_like and not fire_rated_hint:
                flags.append("🔥 متطلبات الحريق عالية: تأكد أن نظام الجبس Fire Rated (FR/Type X) وليس MR فقط.")
                recs.append("استبدل أو عدّل النظام إلى Gypsum FR أو نظام بلوك/مباني مقاوم حريق.")

    # 2) Wet / humidity high checks
    if wet or humidity == "high":
        if ("gypsum" in mat or "drywall" in mat) and ("mr" not in mat) and ("moist" not in mat):
            flags.append("💧 رطوبة/منطقة رطبة: الجبس غير MR قد يتضرر.")
            recs.append("استخدم Gypsum MR أو Cement Board أو بلوك أسمنتي حسب المنطقة.")

    # 3) External walls sanity
    if wall_zone == "external":
        if ("drywall" in mat) or ("gypsum" in mat):
            flags.append("🌦️ جدار خارجي: الجبس ليس نظام واجهات عام إلا إذا كان ضمن Facade System متخصص.")
            recs.append("للخارج: AAC/Block + عزل + تشطيبات مناسبة أو نظام واجهات معتمد.")

    # تحديد مستوى الثقة
    if any("🔥" in f for f in flags):
        confidence = "Low"
        risk_level = "High"
    elif flags:
        confidence = "Medium"
        risk_level = "Warning"
    else:
        confidence = "High"
        risk_level = "None"

    return {
        "confidence": confidence,
        "risk_level": risk_level,
        "flags": flags,
        "recommendations": recs
    }

# =========================
# 6) Main entry
# =========================

def infer_walls(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hybrid walls inference:
      - PKL rules => hard constraints (block/force)
      - Excel KB  => candidates + scoring
    Expected (best) profile keys:
      structural_system, wall_zone, room_type, climate, humidity, fire_rating, acoustic, budget
    """
    ctx = classify_wall_context(profile)

    rules_obj = load_walls_rules()
    hard = apply_wall_hard_rules(ctx, rules_obj)

    df = load_walls_materials_df()
    ranked = score_wall_candidates(df, profile, ctx, hard)

    best = ranked[0] if ranked else None
    alts = ranked[1:3] if len(ranked) > 1 else []

    result = {
        "category": "walls",
        "context": ctx,
        "hard_rules": hard,
        "best": None,
        "alternatives": [],
        "value_engineering": []
    }

    if best:
        result["best"] = {
            **best,
            "package": build_wall_package(best["material"], ctx)
        }

        result["alternatives"] = [
            {
                **a,
                "package": build_wall_package(a["material"], ctx)
            } for a in alts
        ]

        # Simple Value Engineering note
        if ctx["domain"] == "partition" and ctx["wall_zone"] == "internal":
            result["value_engineering"].append(
                "Value Engineering: في نظام الأعمدة، اختيار مواد أخف للقواطع يقلل الأحمال الميتة وقد يقلل كلفة الحديد/الخرسانة."
            )

        if ctx["domain"] == "structural":
            result["value_engineering"].append(
                "تنبيه إنشائي: للجدران الحاملة/القص، يلزم تصميم وتسليح وتفاصيل تنفيذ حسب الكود (ACI) وليس توصية مواد فقط."
            )
    result["engineering_check"] = assess_wall_engineering_confidence(result, profile)
    return result

# ==============================
# FLOORING EXPERT MODULE (D)
# ==============================

from typing import Dict, Any, Tuple, List, Optional

def _norm(s: Any) -> str:
    return str(s).strip().lower()

def _get_df(datasets: dict, keys: List[str]):
    if not isinstance(datasets, dict):
        return None
    for k in keys:
        if k in datasets and datasets[k] is not None:
            return datasets[k]
    return None

def _coerce_level(v: str) -> str:
    v = _norm(v)
    # unify UI values
    if v in ("ground", "lower", "basement"):
        return "ground"
    if v in ("upper", "typical", "floor"):
        return "upper"
    return v or "upper"

def _risk_map_humidity(h: str) -> str:
    h = _norm(h)
    if h in ("very_high", "very high"):
        return "wet"
    if h in ("high",):
        return "humid"
    if h in ("medium",):
        return "normal"
    return "dry"

def _traffic_from_project_room(project_type: str, room_type: str) -> str:
    p = _norm(project_type)
    r = _norm(room_type)

    # baseline by project
    if p in ("hospital",):
        base = "high"
    elif p in ("school",):
        base = "high"
    elif p in ("mall", "commercial", "airport", "station"):
        base = "very_high"
    else:
        base = "medium"

    # adjust by room
    if r in ("corridor", "hall", "lobby", "stairs", "stair", "entrance"):
        return "very_high" if base in ("high", "very_high") else "high"
    if r in ("classroom", "office", "meeting", "patient_room", "room", "bedroom"):
        return base
    if r in ("kitchen", "bathroom", "wc", "laundry"):
        return "high"
    if r in ("storage", "warehouse", "workshop", "garage"):
        return "very_high"
    return base

def _needs_hygiene(project_type: str) -> bool:
    return _norm(project_type) in ("hospital", "clinic", "lab", "laboratory")

def _min_slip_class(humidity_risk: str, room_type: str) -> str:
    r = _norm(room_type)
    if humidity_risk in ("wet", "humid") or r in ("bathroom", "wc", "kitchen", "laundry"):
        return "anti_slip"   # target R11/R12 idea
    return "normal"

def _block_finish_rules(finish_family: str, humidity_risk: str, min_slip: str, traffic: str, hygiene: bool) -> List[str]:
    f = _norm(finish_family)
    reasons = []

    # humidity blocks
    if humidity_risk in ("wet", "humid"):
        if f in ("wood", "laminate", "hdf", "hardwood"):
            reasons.append("غير مناسب للرطوبة العالية (انتفاخ/تعفن/تلف).")
        if f in ("carpet", "carpet_tile", "carpet tiles", "moquette"):
            reasons.append("غير مناسب للرطوبة/التنظيف المتكرر (روائح/بكتيريا).")

    # hygiene blocks
    if hygiene:
        if f in ("carpet", "carpet_tile", "moquette"):
            reasons.append("غير مناسب للمتطلبات الصحية (تجميع غبار/صعوبة تعقيم).")
        if f in ("porous_tile", "stone_polished"):
            reasons.append("قد يزيد مخاطر التلوث إذا كانت المسامية عالية/سطح مصقول.")

    # traffic blocks
    if traffic in ("high", "very_high"):
        if f in ("ceramic_light", "standard_ceramic", "laminate"):
            reasons.append("تحمل ضعيف لحركة عالية (تآكل/تكسر محتمل).")

    # slip blocks
    if min_slip == "anti_slip":
        if f in ("polished_marble", "polished_tile", "polished_stone"):
            reasons.append("خطر انزلاق مرتفع (سطح مصقول) بالمناطق الرطبة/التنظيف.")

    return reasons

def _base_score_finish(finish_family: str, traffic: str, humidity_risk: str, hygiene: bool, acoustic_priority: str, budget_level: str) -> float:
    f = _norm(finish_family)
    traffic = _norm(traffic)
    humidity_risk = _norm(humidity_risk)
    acoustic_priority = _norm(acoustic_priority)
    budget_level = _norm(budget_level)

    score = 50.0

    # traffic preference
    if traffic == "very_high":
        if f in ("terrazzo", "porcelain_full_body", "epoxy"):
            score += 18
        if f in ("vinyl_homo", "vinyl_lvt"):
            score += 10
        if f in ("standard_ceramic", "laminate", "wood"):
            score -= 12

    if traffic == "high":
        if f in ("porcelain_full_body", "terrazzo", "vinyl_homo", "vinyl_lvt"):
            score += 12
        if f in ("standard_ceramic",):
            score -= 4

    # humidity preference
    if humidity_risk in ("wet", "humid"):
        if f in ("vinyl_homo", "vinyl_sheet", "porcelain_full_body", "epoxy", "terrazzo"):
            score += 12
        if f in ("wood", "laminate", "carpet", "carpet_tile"):
            score -= 18

    # hygiene preference
    if hygiene:
        if f in ("vinyl_homo", "vinyl_sheet", "epoxy", "porcelain_full_body", "terrazzo"):
            score += 15
        if f in ("carpet", "carpet_tile"):
            score -= 25

    # acoustic preference
    if acoustic_priority == "high":
        if f in ("vinyl_lvt", "vinyl_sheet", "rubber", "carpet_tile"):
            score += 10
        if f in ("terrazzo", "stone", "porcelain_full_body"):
            score -= 4

    # budget preference
    if budget_level == "low":
        if f in ("vinyl_lvt", "standard_ceramic"):
            score += 6
        if f in ("terrazzo", "stone", "epoxy"):
            score -= 6
    if budget_level == "high":
        if f in ("terrazzo", "stone", "porcelain_full_body"):
            score += 6

    return float(score)

def _default_finish_catalog() -> List[Dict[str, Any]]:
    # fallback if dataset doesn't have clear finish families
    return [
        {"Material_ID": "FIN-VINYL-HOMO-001", "Finish_Family": "vinyl_homo", "Name_AR": "فينيل متجانس (Sheet) - صحي", "Name_EN": "Homogeneous Vinyl Sheet"},
        {"Material_ID": "FIN-PORC-FULL-001",  "Finish_Family": "porcelain_full_body", "Name_AR": "بورسلين (Full Body) - تحمل عالي", "Name_EN": "Full Body Porcelain"},
        {"Material_ID": "FIN-TERRAZZO-001",   "Finish_Family": "terrazzo", "Name_AR": "تيرازو - عمر طويل للممرات", "Name_EN": "Terrazzo"},
        {"Material_ID": "FIN-EPOXY-001",      "Finish_Family": "epoxy", "Name_AR": "إيبوكسي - صناعي/مواقف", "Name_EN": "Epoxy Flooring"},
        {"Material_ID": "FIN-VINYL-LVT-001",  "Finish_Family": "vinyl_lvt", "Name_AR": "فينيل (LVT) - مكاتب/صفوف", "Name_EN": "LVT Vinyl"},
        {"Material_ID": "FIN-CERAMIC-STD-001","Finish_Family": "standard_ceramic", "Name_AR": "سيراميك عادي - اقتصادي", "Name_EN": "Standard Ceramic"},
        {"Material_ID": "FIN-CARPET-TILE-001","Finish_Family": "carpet_tile", "Name_AR": "موكيت بلاطات - عزل صوتي", "Name_EN": "Carpet Tiles"},
        {"Material_ID": "FIN-WOOD-001",       "Finish_Family": "wood", "Name_AR": "خشب/باركيه - جاف فقط", "Name_EN": "Wood / Parquet"},
    ]


# ============================================================
# Flooring Expert Logic - (D1) Slip / Anti-Slip Validation
# ============================================================

from typing import Dict, Any, List, Tuple

def _slip_to_rank(val: Any) -> int:
    """
    Converts slip class like: R9/R10/R11/R12/R13 or text (low/medium/high)
    into an integer rank. Higher rank = better anti-slip.
    """
    if val is None:
        return 0
    s = str(val).strip().upper()

    # common formats: "R10", "R11", "R12"
    if s.startswith("R") and len(s) >= 2:
        try:
            return int(s.replace("R", "").strip())
        except Exception:
            return 0

    # fallback text
    if s in ["LOW", "L", "POOR"]:
        return 8
    if s in ["MEDIUM", "M", "OK"]:
        return 10
    if s in ["HIGH", "H", "GOOD", "VERY_HIGH"]:
        return 11

    return 0


def _required_slip_rank(ctx: Dict[str, Any]) -> int:
    """
    Determines minimum required slip class (rank) based on room type & humidity.
    You can tune these numbers later.
    """
    room = str(ctx.get("room_type", "")).strip().lower()
    hum = str(ctx.get("humidity", "")).strip().lower()

    # Wet / high-risk zones
    wet_rooms = {"bathroom", "wc", "toilet", "kitchen", "laundry", "pool", "shower"}
    high_traffic = {"corridor", "hall", "lobby", "entrance", "stair", "staircase"}

    # Base requirement
    req = 9  # default

    if room in wet_rooms:
        req = 11  # R11+ (anti-slip) for wet rooms
    elif room in high_traffic:
        req = 10  # R10+ for corridors/entrances

    # If humidity is high, raise requirement by 1 (conservative)
    if hum in ["high", "very_high"]:
        req = max(req, 11)

    return req


def apply_flooring_slip_logic(
    row: Dict[str, Any],
    ctx: Dict[str, Any],
    slip_col_candidates: List[str] = None,
) -> Tuple[int, List[str], List[str]]:
    """
    Returns:
      penalty_points, warnings, blocks
    - penalty reduces score
    - warnings appear to user
    - blocks means should be excluded entirely
    """
    if slip_col_candidates is None:
        slip_col_candidates = [
            "Slip_Resistance_Class",
            "Slip_Class",
            "Anti_Slip_Class",
            "SlipResistance",
            "Slip",
        ]

    penalty = 0
    warnings: List[str] = []
    blocks: List[str] = []

    # read slip class from row
    slip_val = None
    for c in slip_col_candidates:
        if c in row and row.get(c) not in [None, "", "nan", "NaN"]:
            slip_val = row.get(c)
            break

    req = _required_slip_rank(ctx)
    actual = _slip_to_rank(slip_val)

    # If column missing, warn and apply small penalty
    if actual == 0:
        penalty += 5
        warnings.append("⚠️ لا توجد قيمة واضحة لمقاومة الانزلاق ضمن الداتا (Slip Class).")
        return penalty, warnings, blocks

    # If actual below requirement
    if actual < req:
        gap = req - actual

        # big gap = block (danger)
        if gap >= 2:
            blocks.append(
                f"⛔ خطر انزلاق: المطلوب ≥ R{req} لكن المتوفر R{actual} (غير مسموح لهذا الاستخدام)."
            )
            # return strong penalty also (in case you still show it in debug)
            penalty += 30
        else:
            penalty += 15
            warnings.append(
                f"⚠️ مقاومة الانزلاق أقل من المطلوب: المطلوب ≥ R{req} لكن المتوفر R{actual}."
            )
    else:
        # bonus small if it exceeds requirement (optional)
        # you can keep it 0 if you don’t want bonuses
        pass

    return penalty, warnings, blocks


def enrich_flooring_candidates_with_slip(
    candidates: List[Dict[str, Any]],
    ctx: Dict[str, Any],
    base_score_key: str = "score",
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Applies slip logic to every candidate dict.
    Adds:
      - slip_penalty
      - warnings (list)
      - blocks (list)
      - final_score
    Returns filtered list + global blocked notes
    """
    blocked_notes: List[str] = []
    out: List[Dict[str, Any]] = []

    for row in candidates:
        base = row.get(base_score_key, row.get("total_score", 50))
        try:
            base = float(base)
        except Exception:
            base = 50.0

        penalty, warns, blocks = apply_flooring_slip_logic(row, ctx)

        row["slip_penalty"] = penalty
        row["warnings"] = list(warns) if warns else []
        row["blocks"] = list(blocks) if blocks else []

        row["final_score"] = max(0.0, base - penalty)

        if blocks:
            blocked_notes.extend(blocks)
            # exclude blocked from list
            continue

        out.append(row)

    # sort by final_score desc
    out.sort(key=lambda r: float(r.get("final_score", 0)), reverse=True)

    return out, blocked_notes

# =========================================
# HOSPITAL POLICIES (Inference Layer)
# =========================================

HOSPITAL_POLICIES = {
    # Zones inside hospital (you can expand later)
    "zones": {
        "OR": {  # Operation Room
            "title_en": "Operation Rooms",
            "title_ar": "غرف العمليات",
        },
        "XRAY": {
            "title_en": "X-Ray / Imaging",
            "title_ar": "الأشعة والتصوير",
        },
        "CORRIDOR": {
            "title_en": "Corridors",
            "title_ar": "الممرات",
        },
        "PATIENT": {
            "title_en": "Patient Rooms",
            "title_ar": "غرف المرضى",
        },
        "ICU": {
            "title_en": "ICU / Critical Care",
            "title_ar": "العناية المركزة",
        },
        "LAB": {
            "title_en": "Labs",
            "title_ar": "المختبرات",
        },
        "ADMIN": {
            "title_en": "Admin / Offices",
            "title_ar": "الإدارة والمكاتب",
        },
        "TOILET": {
            "title_en": "Toilets / Wet Areas",
            "title_ar": "الحمامات والمناطق الرطبة",
        },
    },

    # Global (applies to all zones by default)
    "global_blocked": [
        {
            "match": ["carpet", "moquette"],
            "reason_en": "High infection risk; difficult to disinfect and retains dust.",
            "reason_ar": "خطر عدوى عالي؛ صعب التعقيم ويحتفظ بالغبار.",
        },
        {
            "match": ["hardwood", "wood", "parquet"],
            "reason_en": "Sensitive to moisture and chemicals; poor hygiene performance.",
            "reason_ar": "حساس للرطوبة والمواد الكيميائية؛ غير مناسب صحياً.",
        },
    ],

    # Recommendations by zone
    "zone_logic": {
        "OR": {
            "recommended": [
                {
                    "match": ["homogeneous vinyl", "vinyl sheet", "sheet vinyl"],
                    "reason_en": "Seamless hygiene, easy sterilization, chemical resistance.",
                    "reason_ar": "نظافة عالية بدون فواصل، سهل التعقيم، مقاوم للمواد الكيميائية.",
                },
                {
                    "match": ["epoxy", "epoxy flooring"],
                    "reason_en": "Monolithic surface, high chemical resistance, easy cleaning.",
                    "reason_ar": "سطح متجانس قوي، مقاوم كيميائياً، سهل التنظيف.",
                },
            ],
            "conditional": [
                {
                    "match": ["ceramic", "porcelain"],
                    "reason_en": "Allowed only if anti-slip and grout is medical-grade; joints must be sealed.",
                    "reason_ar": "مسموح فقط إذا مانع انزلاق وترويبة طبية مع إحكام الفواصل.",
                }
            ],
            "blocked": [
                {
                    "match": ["marble", "granite polished", "polished"],
                    "reason_en": "Slip risk and difficult safety control in critical zones.",
                    "reason_ar": "خطر انزلاق وصعب ضبط السلامة في مناطق حرجة.",
                }
            ],
        },

        "CORRIDOR": {
            "recommended": [
                {
                    "match": ["vinyl", "lvt", "rubber flooring", "rubber"],
                    "reason_en": "Durable under traffic, quiet footsteps, easy cleaning.",
                    "reason_ar": "يتحمل الحركة العالية، يقلل الضوضاء، سهل التنظيف.",
                }
            ],
            "conditional": [
                {
                    "match": ["porcelain", "terrazzo"],
                    "reason_en": "OK with anti-slip class and strict joint detailing.",
                    "reason_ar": "مقبول مع مقاومة انزلاق وتفاصيل فواصل ممتازة.",
                }
            ],
        },

        "TOILET": {
            "recommended": [
                {
                    "match": ["anti-slip porcelain", "porcelain", "ceramic"],
                    "reason_en": "Wet-zone safe when anti-slip; water resistance.",
                    "reason_ar": "مناسب للمناطق الرطبة عند اختيار مانع انزلاق؛ مقاوم للماء.",
                }
            ],
            "blocked": [
                {
                    "match": ["carpet", "wood", "parquet"],
                    "reason_en": "Absorbs moisture and causes hygiene failure.",
                    "reason_ar": "يمتص الرطوبة ويسبب فشل صحي.",
                }
            ],
        },
    }
}


def _text_contains_any(value: str, keywords: list) -> bool:
    if value is None:
        return False
    v = str(value).lower()
    return any(k.lower() in v for k in keywords)


def apply_hospital_flooring_policy(material_name: str, zone_code: str):
    """
    Returns:
      decision: "Recommended" | "Conditional" | "Blocked" | "Allowed"
      reason_en, reason_ar
    """
    name = (material_name or "").strip()
    name_l = name.lower()

    # 1) Global blocked
    for rule in HOSPITAL_POLICIES.get("global_blocked", []):
        if _text_contains_any(name_l, rule.get("match", [])):
            return "Blocked", rule["reason_en"], rule["reason_ar"]

    # 2) Zone logic
    z = (zone_code or "").strip().upper()
    zone_logic = HOSPITAL_POLICIES.get("zone_logic", {}).get(z, {})

    for rule in zone_logic.get("blocked", []):
        if _text_contains_any(name_l, rule.get("match", [])):
            return "Blocked", rule["reason_en"], rule["reason_ar"]

    for rule in zone_logic.get("recommended", []):
        if _text_contains_any(name_l, rule.get("match", [])):
            return "Recommended", rule["reason_en"], rule["reason_ar"]

    for rule in zone_logic.get("conditional", []):
        if _text_contains_any(name_l, rule.get("match", [])):
            return "Conditional", rule["reason_en"], rule["reason_ar"]

    # Default
    return "Allowed", "Allowed if meets hospital hygiene and slip requirements.", "مسموح إذا حقق متطلبات النظافة ومقاومة الانزلاق."



if __name__ == "__main__":
    main_loop()
