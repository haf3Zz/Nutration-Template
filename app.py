import streamlit as st
import json
from datetime import datetime

# تحميل قاعدة البيانات
with open("nutrition_data.json", "r", encoding="utf-8") as f:
    food_data = json.load(f)

st.set_page_config(layout="wide", page_title="Nutrition Plan")

st.title("📋 Nutrition Plan Creator (Cloud Version)")

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

meal_titles = {
    "breakfast": "🍳 فطور",
    "snack1": "🥜 سناك 1",
    "lunch": "🍗 غداء",
    "pre_workout": "🥤 قبل التمرين",
    "dinner": "🍽️ عشاء",
    "night_snack": "🍮 سناك ليلي"
}

st.sidebar.header("🧍‍♂️ بيانات العميل")
weight = st.sidebar.number_input("وزنك (كجم)", min_value=1.0, step=0.5)
if weight > 0:
    water_ml = int((weight * 0.033 * 1000) + 500)
    st.sidebar.success(f"💧 ماء يومي: {water_ml} مل")
    st.session_state.plan["client_info"]["weight"] = weight
    st.session_state.plan["client_info"]["water_intake"] = f"{water_ml} مل"

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
            st.success(f"تمت إضافة {food_name} ({qty} جم)")

        if st.session_state.plan["meals"][meal_id]:
            st.markdown("#### محتوى الوجبة:")
            for j, entry in enumerate(st.session_state.plan["meals"][meal_id]):
                st.write(f"- {entry['name']} | {entry['quantity']}g | {entry['calories']} kcal | P: {entry['protein']}g | C: {entry['carbs']}g | F: {entry['fat']}g")
                if st.button("❌ حذف", key=f"del_{meal_id}_{j}"):
                    del st.session_state.plan["meals"][meal_id][j]
                    st.experimental_rerun()

st.sidebar.header("💊 مكملات غذائية")
supp = st.sidebar.text_input("اسم المكمل")
if st.sidebar.button("➕ أضف مكمل"):
    if supp.strip():
        st.session_state.plan["supplements"].append(supp.strip())

if st.session_state.plan["supplements"]:
    st.sidebar.markdown("**📦 المكملات:**")
    for i, s in enumerate(st.session_state.plan["supplements"]):
        st.sidebar.write(f"- {s}")
        if st.sidebar.button("❌ حذف", key=f"del_supp_{i}"):
            del st.session_state.plan["supplements"][i]
            st.experimental_rerun()

st.header("📊 ملخص القيم")
total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
for meal in st.session_state.plan["meals"].values():
    for item in meal:
        total["calories"] += item["calories"]
        total["protein"] += item["protein"]
        total["carbs"] += item["carbs"]
        total["fat"] += item["fat"]
st.session_state.plan["calories"] = total

st.write(f"🔥 السعرات: {total['calories']:.0f} kcal")
st.write(f"💪 بروتين: {total['protein']:.1f} g")
st.write(f"🥔 كارب: {total['carbs']:.1f} g")
st.write(f"🧈 دهون: {total['fat']:.1f} g")
st.write(f"💧 ماء: {st.session_state.plan['client_info']['water_intake']}")

if st.button("💾 تحميل HTML"):
    html = f'''
    <html dir="rtl"><head><meta charset="UTF-8"><style>body {{ font-family: Cairo; }}</style></head><body>
    <h2>خطة غذائية</h2><p>الوزن: {weight} كجم</p><p>الماء اليومي: {water_ml} مل</p>
    '''
    for meal_id, items in st.session_state.plan["meals"].items():
        if items:
            html += f"<h3>{meal_titles[meal_id]}</h3><ul>"
            for item in items:
                html += f"<li>{item['name']} - {item['quantity']} جم - {item['calories']} kcal</li>"
            html += "</ul>"
    if st.session_state.plan["supplements"]:
        html += "<h3>المكملات:</h3><ul>"
        for s in st.session_state.plan["supplements"]:
            html += f"<li>{s}</li>"
        html += "</ul>"
    html += "<h3>ملاحظات:</h3><ul>"
    for n in st.session_state.plan["notes"]:
        html += f"<li>{n}</li>"
    html += "</ul></body></html>"
    file_name = f"plan_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    st.download_button("📥 تحميل HTML", data=html, file_name=file_name, mime="text/html")
