import streamlit as st
import json
import os
from weasyprint import HTML
from datetime import datetime

# تحميل قاعدة البيانات
def load_food_data():
    with open("nutrition_data.json", "r", encoding="utf-8") as f:
        return json.load(f)

food_data = load_food_data()

st.set_page_config(layout="wide", page_title="Nutrition Plan")

st.title("📋 Nutrition Plan Creator (Web Version)")
st.markdown("نظام غذائي مقسم إلى وجبات مع حساب السعرات والطباعة PDF")

# تهيئة البيانات في الجلسة
if "plan" not in st.session_state:
    st.session_state.plan = {
        "client_info": {"weight": 0, "water_intake": "0 مل"},
        "calories": {"total": 0, "protein": 0, "carbs": 0, "fat": 0},
        "meals": {m: [] for m in ["breakfast", "snack1", "lunch", "pre_workout", "dinner", "night_snack"]},
        "supplements": [],
        "notes": [
            "🕒 التزم بمواعيد الوجبات",
            "💧 اشرب كمية المياه اليومية",
            "🛌 احصل على 7-8 ساعات نوم",
            "🥗 تجنب الأطعمة المصنعة والسكريات"
        ]
    }

# حساب الماء من الوزن
st.sidebar.header("🧍‍♂️ بيانات العميل")
weight = st.sidebar.number_input("وزنك (كجم)", min_value=1.0, step=0.5)
if weight > 0:
    water_ml = int((weight * 0.033 * 1000) + 500)
    st.sidebar.success(f"💧 ماء يومي: {water_ml} مل")
    st.session_state.plan["client_info"]["weight"] = weight
    st.session_state.plan["client_info"]["water_intake"] = f"{water_ml} مل"

# الوجبات
meal_titles = {
    "breakfast": "🍳 فطور",
    "snack1": "🥜 سناك 1",
    "lunch": "🍗 غداء",
    "pre_workout": "🥤 قبل التمرين",
    "dinner": "🍽️ عشاء",
    "night_snack": "🍮 سناك ليلي"
}

tab_meals = st.tabs([meal_titles[k] for k in st.session_state.plan["meals"].keys()])
for i, (meal_id, tab) in enumerate(zip(st.session_state.plan["meals"].keys(), tab_meals)):
    with tab:
        st.markdown(f"### أضف طعامًا إلى {meal_titles[meal_id]}")
        col1, col2 = st.columns(2)
        with col1:
            food_name = st.selectbox("الطعام:", [f["name"] for f in food_data], key=f"food_{meal_id}")
        with col2:
            qty = st.number_input("الكمية (جم):", min_value=1, value=100, step=10, key=f"qty_{meal_id}")
        if st.button("➕ أضف", key=f"add_{meal_id}"):
            item = next(f for f in food_data if f["name"] == food_name)
            record = {
                "name": food_name,
                "quantity": qty,
                "calories": round(item["calories"] * qty / 100, 1),
                "protein": round(item["protein"] * qty / 100, 1),
                "carbs": round(item["carbs"] * qty / 100, 1),
                "fat": round(item["fat"] * qty / 100, 1)
            }
            st.session_state.plan["meals"][meal_id].append(record)
            st.success(f"تمت إضافة {food_name} ({qty} جم) إلى {meal_titles[meal_id]}")

        # عرض محتويات الوجبة
        if st.session_state.plan["meals"][meal_id]:
            st.markdown("#### محتوى الوجبة:")
            for j, entry in enumerate(st.session_state.plan["meals"][meal_id]):
                st.write(f"- {entry['name']} | {entry['quantity']}g | {entry['calories']} kcal | P: {entry['protein']}g | C: {entry['carbs']}g | F: {entry['fat']}g")
                if st.button("❌ حذف", key=f"del_{meal_id}_{j}"):
                    del st.session_state.plan["meals"][meal_id][j]
                    st.experimental_rerun()

# المكملات والملاحظات
st.sidebar.header("💊 مكملات غذائية")
supp = st.sidebar.text_input("اسم المكمل")
if st.sidebar.button("➕ أضف مكمل"):
    if supp.strip():
        st.session_state.plan["supplements"].append(supp.strip())

if st.session_state.plan["supplements"]:
    st.sidebar.markdown("**📦 قائمة المكملات:**")
    for i, s in enumerate(st.session_state.plan["supplements"]):
        st.sidebar.write(f"- {s}")
        if st.sidebar.button("❌ حذف", key=f"del_supp_{i}"):
            del st.session_state.plan["supplements"][i]
            st.experimental_rerun()

# ملخص القيم الغذائية
st.header("📊 ملخص القيم الغذائية")
total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
for meal in st.session_state.plan["meals"].values():
    for item in meal:
        total["calories"] += item["calories"]
        total["protein"] += item["protein"]
        total["carbs"] += item["carbs"]
        total["fat"] += item["fat"]

st.write(f"🔥 السعرات: {total['calories']:.0f} kcal")
st.write(f"💪 البروتين: {total['protein']:.1f} g")
st.write(f"🥔 الكارب: {total['carbs']:.1f} g")
st.write(f"🧈 الدهون: {total['fat']:.1f} g")
st.write(f"💧 الماء اليومي: {st.session_state.plan['client_info']['water_intake']}")

# تحديث الخطة
st.session_state.plan["calories"] = total

# زر حفظ PDF
if st.button("📤 تصدير PDF"):
    html = f"""
    <html dir="rtl" lang="ar"><head><meta charset="UTF-8">
    <style>
    body {{ font-family: "Cairo", sans-serif; font-size: 14px; direction: rtl; }}
    .meal {{ margin-bottom: 20px; }}
    h2 {{ color: #2c3e50; }}
    .supplement, .note {{ margin-bottom: 4px; }}
    </style></head><body>
    <h2>خطة غذائية</h2>
    <p><strong>الوزن:</strong> {st.session_state.plan["client_info"]["weight"]} كجم</p>
    <p><strong>الماء:</strong> {st.session_state.plan["client_info"]["water_intake"]}</p>
    <h3>الوجبات:</h3>
    """
    for meal_id, items in st.session_state.plan["meals"].items():
        if items:
            html += f"<div class='meal'><h4>{meal_titles[meal_id]}</h4><ul>"
            for item in items:
                html += f"<li>{item['name']} - {item['quantity']} جم - {item['calories']} Kcal</li>"
            html += "</ul></div>"

    html += "<h3>المكملات:</h3><ul>"
    for s in st.session_state.plan["supplements"]:
        html += f"<li class='supplement'>{s}</li>"
    html += "</ul>"

    html += "<h3>ملاحظات:</h3><ul>"
    for n in st.session_state.plan["notes"]:
        html += f"<li class='note'>{n}</li>"
    html += "</ul>"

    html += "</body></html>"

    pdf_filename = f"nutrition_plan_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    HTML(string=html).write_pdf(pdf_filename)
    with open(pdf_filename, "rb") as f:
        st.download_button("📥 تحميل الملف", data=f, file_name=pdf_filename, mime="application/pdf")
