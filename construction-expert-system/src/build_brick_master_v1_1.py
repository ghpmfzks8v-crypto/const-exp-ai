# src/build_brick_master_v1_1.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd


# ==========================
# v1.1 Constants (AGREED)
# ==========================
SECTIONS = [
    "Facade_External",
    "Internal_Partitions",
    "Wet_Zones",
    "Parapet_Roof",
    "Acoustic_Fire",
]

EXPOSURES = ["Normal", "Saline", "Humid"]
BUDGETS = ["Economic", "Medium", "Luxury"]
PROJECTS = [
    "Hospital",
    "Residential",
    "Industrial",
    "School",
    "Restaurant",
    "Bridge",
    "Tunnel",
    "Warehouse",
    "Parking",
    "Commercial",
]

# Functions (AGREED v1.1)
FUNCTIONS_BASE = {
    "Facade_External": ["Facade", "External_Wall"],
    "Internal_Partitions": ["General"],  # + Project special (Corridor/Classroom/Impact_Zone)
    "Wet_Zones": ["Wet_Zone"],
    "Parapet_Roof": ["Parapet_Roof"],
    "Acoustic_Fire": ["Any"],  # + Project special (Operating_Room/XRay_Room)
}

# Hospital must always show special rooms (AGREED: A)
HOSPITAL_SPECIAL_FUNCS = ["Operating_Room", "XRay_Room", "Corridor"]


@dataclass(frozen=True)
class BrickMaterial:
    key: str
    name_en: str
    name_ar: str
    origin_en: str
    origin_ar: str
    benefit_en: str
    benefit_ar: str
    tip_en: str
    tip_ar: str
    # suitability tags
    exposures_ok: Tuple[str, ...]  # ("Normal","Saline","Humid")
    budgets_ok: Tuple[str, ...]    # ("Economic","Medium","Luxury")
    sections_ok: Tuple[str, ...]   # SECTIONS
    functions_ok: Tuple[str, ...]  # e.g., ("General","Facade","Wet_Zone","Corridor",...)


def _lib() -> List[BrickMaterial]:
    """Seed library: realistic Iraq-market oriented starters.
    You can add more later without changing the engine.
    """
    return [
        # Facade / External (Normal)
        BrickMaterial(
            key="FACE_BRICK_A",
            name_en="Republican Face Brick (Al-Minjali) – Grade A",
            name_ar="طابوق جمهوري واجهات (المنجلي) – صنف أ",
            origin_en="Iraq",
            origin_ar="عراقي",
            benefit_en="High appearance quality and good durability for facades; balanced porosity helps wall 'breathe' without water leakage.",
            benefit_ar="جمالية عالية وديمومة جيدة للواجهات؛ مسامية متوازنة تسمح للجدار بالتنفس دون تسريب الماء.",
            tip_en="Soak bricks 1–2 hours before laying and control mortar ratio to reduce efflorescence.",
            tip_ar="نقع الطابوق 1–2 ساعة قبل البناء مع ضبط نسبة المونة لتقليل التزهير.",
            exposures_ok=("Normal",),
            budgets_ok=("Luxury", "Medium"),
            sections_ok=("Facade_External",),
            functions_ok=("Facade", "External_Wall"),
        ),
        BrickMaterial(
            key="MECH_BRICK",
            name_en="Perforated Mechanical Clay Brick",
            name_ar="طابوق ميكانيكي مثقب",
            origin_en="Iraq",
            origin_ar="عراقي",
            benefit_en="Fast construction and cost-effective for external walls with plaster/render protection.",
            benefit_ar="سريع التنفيذ واقتصادي للجدران الخارجية مع حماية باللياسة/الدهان.",
            tip_en="Provide good external render and joints mesh at interfaces to control cracking.",
            tip_ar="اعتماد لياسة خارجية جيدة مع شبك فايبر عند نقاط الالتقاء لتقليل التشققات.",
            exposures_ok=("Normal", "Humid"),
            budgets_ok=("Economic", "Medium"),
            sections_ok=("Facade_External",),
            functions_ok=("External_Wall",),
        ),

        # Saline / Humid (South-like)
        BrickMaterial(
            key="KOSH_BRICK",
            name_en="Hard-Burnt Brick (Kosh) / Very Dense Fired Brick",
            name_ar="طابوق محروق جداً (الكوش) / فخاري كثيف",
            origin_en="Iraq",
            origin_ar="عراقي",
            benefit_en="Very dense brick reduces capillary rise and improves durability in saline/humid exposure.",
            benefit_ar="كثافة عالية تقلل صعود الرطوبة بالأنابيب الشعرية وتزيد الديمومة في البيئات الملحية/الرطبة.",
            tip_en="Use sulfate-resistant cement mortar below grade; apply DPC and protect from standing water.",
            tip_ar="استخدم مونة بأسمنت مقاوم للكبريتات تحت منسوب الأرض مع DPC وحماية من تجمع الماء.",
            exposures_ok=("Saline", "Humid"),
            budgets_ok=("Medium", "Luxury"),
            sections_ok=("Facade_External", "Wet_Zones", "Parapet_Roof"),
            functions_ok=("External_Wall", "Wet_Zone", "Parapet_Roof"),
        ),
        BrickMaterial(
            key="DENSE_CEMENT_BLOCK",
            name_en="Dense Solid Cement Block (High Density)",
            name_ar="بلوك أسمنتي مصمت كثيف (عالي الكثافة)",
            origin_en="Iraq",
            origin_ar="عراقي",
            benefit_en="Lower water sensitivity and higher density; suitable for wet zones and lower impact areas.",
            benefit_ar="أقل حساسية للماء وكثافة أعلى؛ مناسب للمناطق الرطبة والمناطق المعرضة للصدمات.",
            tip_en="Use waterproof plaster/primer before tiles; ensure proper curing to reduce shrinkage cracks.",
            tip_ar="لياسة مقاومة للماء قبل السيراميك مع معالجة جيدة لتقليل التشققات الانكماشية.",
            exposures_ok=("Normal", "Saline", "Humid"),
            budgets_ok=("Economic", "Medium"),
            sections_ok=("Wet_Zones", "Internal_Partitions", "Facade_External"),
            functions_ok=("Wet_Zone", "Corridor", "Impact_Zone", "External_Wall", "General"),
        ),

        # Internal Partitions
        BrickMaterial(
            key="AAC_THERMOSTONE",
            name_en="AAC Blocks (Thermostone) – Grade A",
            name_ar="ثرمستون (AAC) – صنف أ",
            origin_en="Iraq",
            origin_ar="عراقي",
            benefit_en="Lightweight partitions reduce dead load and improve thermal comfort; good for general internal partitions.",
            benefit_ar="خفيف يقلل الأحمال الميتة ويحسن العزل الحراري؛ مناسب للقواطع الداخلية العامة.",
            tip_en="Use AAC adhesive and mesh at joints; avoid direct contact with water—provide base moisture barrier.",
            tip_ar="غراء AAC + شبك فايبر للفواصل؛ منع تماس مباشر مع الماء واستخدام عازل رطوبة أسفل الجدار.",
            exposures_ok=("Normal", "Humid", "Saline"),
            budgets_ok=("Economic", "Medium"),
            sections_ok=("Internal_Partitions",),
            functions_ok=("General", "Classroom"),
        ),
        BrickMaterial(
            key="HOLLOW_CLAY_BRICK",
            name_en="Hollow Clay Brick (Internal Use)",
            name_ar="طابوق فخاري مفرغ (داخلي)",
            origin_en="Iraq",
            origin_ar="عراقي",
            benefit_en="Cost-effective partitions in dry areas; acceptable acoustic performance with proper plaster.",
            benefit_ar="اقتصادي للقواطع في المناطق الجافة؛ عزل صوتي مقبول مع لياسة مناسبة.",
            tip_en="Avoid wet zones; ensure full bedding mortar and quality plaster finish.",
            tip_ar="تجنب المناطق الرطبة؛ مونة كاملة تحت الطابوق ولياسة جيدة.",
            exposures_ok=("Normal",),
            budgets_ok=("Economic", "Medium"),
            sections_ok=("Internal_Partitions",),
            functions_ok=("General",),
        ),

        # Corridor / Impact / Industrial lower zone
        BrickMaterial(
            key="SILICATE_BRICK",
            name_en="Calcium Silicate Brick (Silicate)",
            name_ar="طابوق جيري (سليكيت)",
            origin_en="Iraq/Turkey",
            origin_ar="عراقي/تركي",
            benefit_en="High hardness and impact resistance; suitable for corridors and industrial/school high-traffic areas.",
            benefit_ar="صلادة عالية ومقاومة صدمات؛ مناسب للممرات ومناطق الحركة العالية بالمدارس/الصناعة.",
            tip_en="Provide protective skirting/guards at lower wall; ensure proper curing to minimize cracking.",
            tip_ar="حماية أسفل الجدار بربر/سكرتنغ؛ معالجة جيدة لتقليل التشققات.",
            exposures_ok=("Normal", "Humid"),
            budgets_ok=("Medium", "Luxury"),
            sections_ok=("Internal_Partitions", "Facade_External"),
            functions_ok=("Corridor", "Impact_Zone", "External_Wall"),
        ),

        # Parapet / Roof edges
        BrickMaterial(
            key="PARAPET_BLOCK",
            name_en="Concrete Block + Bituminous Coating (Parapet)",
            name_ar="بلوك أسمنتي + دهان بيتوميني (ستارة)",
            origin_en="Iraq",
            origin_ar="عراقي",
            benefit_en="Good availability and durability when protected; suitable for parapet and roof edges.",
            benefit_ar="متوفر وديمومته جيدة عند الحماية؛ مناسب للستارة وحواف السطح.",
            tip_en="Protect bituminous layer from UV with screed/protection; provide slope for drainage.",
            tip_ar="حماية طبقة البيتومين من الشمس بطبقة حماية مع ميل للتصريف.",
            exposures_ok=("Normal", "Saline", "Humid"),
            budgets_ok=("Economic", "Medium"),
            sections_ok=("Parapet_Roof",),
            functions_ok=("Parapet_Roof",),
        ),

        # Hospital special rooms (Operating/XRay) – show always in hospital
        BrickMaterial(
            key="CEMENT_BLOCK_OPER",
            name_en="Dense Cement Block + Cement Board Finish (Hygienic)",
            name_ar="بلوك كثيف + ألواح إسمنتية (تشطيب صحي)",
            origin_en="Global/Iraq",
            origin_ar="عالمي/عراقي",
            benefit_en="Durable, washable surface and low moisture sensitivity; suitable for operating/service rooms.",
            benefit_ar="سطح متين قابل للتعقيم وأقل حساسية للرطوبة؛ مناسب لغرف العمليات والخدمات.",
            tip_en="Seal joints; use hygienic coating system; follow hospital infection control requirements.",
            tip_ar="إغلاق الفواصل + نظام طلاء صحي؛ الالتزام بمتطلبات التعقيم والسيطرة على العدوى.",
            exposures_ok=("Normal", "Humid", "Saline"),
            budgets_ok=("Medium", "Luxury"),
            sections_ok=("Acoustic_Fire",),
            functions_ok=("Operating_Room",),
        ),
        BrickMaterial(
            key="XRAY_SHIELD",
            name_en="Radiation Shielding Blocks (Lead Brick / High Density Shield)",
            name_ar="طابوق/بلوك مقاوم للإشعاع (رصاصي/كثافة عالية)",
            origin_en="Global",
            origin_ar="عالمي",
            benefit_en="Provides radiation shielding required for X-Ray rooms; density and detailing are critical.",
            benefit_ar="يوفر عزل إشعاعي لغرف الأشعة؛ الكثافة والتفاصيل التنفيذية حاسمة.",
            tip_en="Must follow radiation consultant design (lead lining thickness, overlaps, joints).",
            tip_ar="يُنفذ حصراً حسب تصميم مهندس الأشعة (سماكات الرصاص وتفاصيل الفواصل).",
            exposures_ok=("Normal", "Humid", "Saline"),
            budgets_ok=("Luxury",),
            sections_ok=("Acoustic_Fire",),
            functions_ok=("XRay_Room",),
        ),
    ]


def _budget_fallback_chain(selected: str) -> List[str]:
    selected = selected.strip()
    if selected == "Luxury":
        return ["Luxury", "Medium", "Economic"]
    if selected == "Medium":
        return ["Medium", "Economic"]
    return ["Economic"]


def _pick_top2(
    materials: List[BrickMaterial],
    project: str,
    exposure: str,
    budget: str,
    section: str,
    function: str,
) -> List[Tuple[int, BrickMaterial]]:
    """
    Return two items as (Rank, material):
    Rank=1 Recommended, Rank=2 Alternative.
    Budget fallback applies.
    """
    # Project priority: exact project first, then Any
    project_chain = [project, "Any"]

    # Exposure priority: exact exposure then Any
    exposure_chain = [exposure, "Any"]

    # Budget fallback chain
    budget_chain = _budget_fallback_chain(budget) + ["Any"]

    picked: List[BrickMaterial] = []

    for pj in project_chain:
        for ex in exposure_chain:
            for bd in budget_chain:
                # filter
                cands = []
                for m in materials:
                    if section not in m.sections_ok:
                        continue
                    if function not in m.functions_ok and "Any" not in m.functions_ok:
                        continue
                    if ex != "Any" and ex not in m.exposures_ok:
                        continue
                    if bd != "Any" and bd not in m.budgets_ok:
                        continue

                    # project fit is encoded by the row we generate; for library we accept all
                    cands.append(m)

                # Keep stable order & avoid duplicates
                for m in cands:
                    if m.key not in [x.key for x in picked]:
                        picked.append(m)
                    if len(picked) >= 2:
                        break

                if len(picked) >= 2:
                    break
            if len(picked) >= 2:
                break
        if len(picked) >= 2:
            break

    out: List[Tuple[int, BrickMaterial]] = []
    if len(picked) >= 1:
        out.append((1, picked[0]))
    if len(picked) >= 2:
        out.append((2, picked[1]))
    elif len(picked) == 1:
        # no alternative found: repeat with same but mark alternative from same family
        out.append((2, picked[0]))
    return out


def build_brick_master_v1_1(output_path: Path) -> pd.DataFrame:
    mats = _lib()

    rows = []
    for project in PROJECTS + ["Any"]:
        for exposure in EXPOSURES:
            for budget in BUDGETS:
                for section in SECTIONS:
                    base_funcs = list(FUNCTIONS_BASE.get(section, ["Any"]))

                    # project-specific extra functions
                    funcs = base_funcs[:]

                    if project == "Hospital":
                        # Always include these special areas (AGREED A)
                        if section == "Internal_Partitions":
                            if "Corridor" not in funcs:
                                funcs.append("Corridor")
                        if section == "Acoustic_Fire":
                            for f in ["Operating_Room", "XRay_Room"]:
                                if f not in funcs:
                                    funcs.append(f)

                    if project in ["School"]:
                        if section == "Internal_Partitions":
                            if "Classroom" not in funcs:
                                funcs.append("Classroom")

                    if project in ["Industrial", "Warehouse", "Parking"]:
                        if section in ["Internal_Partitions", "Facade_External"]:
                            if "Impact_Zone" not in funcs:
                                funcs.append("Impact_Zone")

                    # Build for each function under each section
                    for func in funcs:
                        top2 = _pick_top2(
                            materials=mats,
                            project=project,
                            exposure=exposure,
                            budget=budget,
                            section=section,
                            function=func,
                        )

                        for rank, m in top2:
                            rows.append({
                                "Project_Type": project,
                                "Exposure": exposure,
                                "Budget": budget,
                                "Section": section,
                                "Function": func,
                                "Rank": rank,
                                "Material_Name_EN": m.name_en,
                                "Material_Name_AR": m.name_ar,
                                "Origin_EN": m.origin_en,
                                "Origin_AR": m.origin_ar,
                                "Engineering_Benefit_EN": m.benefit_en,
                                "Engineering_Benefit_AR": m.benefit_ar,
                                "Execution_Tip_EN": m.tip_en,
                                "Execution_Tip_AR": m.tip_ar,
                            })

    df = pd.DataFrame(rows)

    # Remove exact duplicates
    df = df.drop_duplicates(subset=[
        "Project_Type","Exposure","Budget","Section","Function","Rank",
        "Material_Name_EN","Material_Name_AR"
    ]).reset_index(drop=True)

    # Sort nicely
    df["__p"] = df["Project_Type"].apply(lambda x: (0 if x != "Any" else 1, x))
    df["__e"] = df["Exposure"].apply(lambda x: {"Normal":0,"Humid":1,"Saline":2}.get(x, 9))
    df["__b"] = df["Budget"].apply(lambda x: {"Luxury":0,"Medium":1,"Economic":2}.get(x, 9))
    df["__s"] = df["Section"].apply(lambda x: SECTIONS.index(x) if x in SECTIONS else 99)
    df["__f"] = df["Function"].astype(str)
    df = df.sort_values(["__p","__e","__b","__s","__f","Rank"]).drop(columns=["__p","__e","__b","__s","__f"])

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Brick_Master_v1_1")

    return df


if __name__ == "__main__":
    # Output to dataset folder by default
    root = Path(__file__).resolve().parents[1]
    out = root / "dataset" / "brick_master_v1_1.xlsx"
    df = build_brick_master_v1_1(out)
    print(f"✅ Generated: {out}")
    print(f"Rows: {len(df)}")