import streamlit as st
import base64
import json
from datetime import datetime

st.set_page_config(layout="wide", page_title="نظام غذائي احترافي")

st.title("📋 منشئ الخطة الغذائية بتنسيق PDF/HTML")

# --- بيانات أولية ---
if "meal_plan" not in st.session_state:
    st.session_state.meal_plan = {
        "client_info": {"weight": 0, "water_intake": "0 مل"},
        "calories": {"total": "0 سعرة حرارية", "protein": "0 جرام", "fat": "0 جرام", "carbs": "0 جرام", "water": "0 مل"},
        "meals": {
            "breakfast": [], "snack1": [], "lunch": [],
            "pre_workout": [], "dinner": [], "night_snack": []
        },
        "supplements": [],
        "notes": [
            "✅ التزم بمواعيد الوجبات قدر المستطاع",
            "💧 اشرب الكمية المطلوبة من المياه يوميًا",
            "🍗 يمكن تبديل البروتينات حسب البدائل المذكورة",
            "❌ تجنب السكريات والأطعمة المصنعة والمشروبات الغازية",
            "🛌 احصل على نوم كافٍ (7-8 ساعات)"
        ]
    }

# --- رفع الشعار ---
st.sidebar.header("📷 شعار الخطة")
logo_file = st.sidebar.file_uploader("ارفع شعار PNG", type=["png"])
if logo_file:
    logo_data = base64.b64encode(logo_file.read()).decode("utf-8")
else:
    # شعار فارغ إذا لم يتم رفع صورة
    logo_data = ""

# --- إدخال الوزن وحساب الماء ---
weight = st.sidebar.number_input("وزن العميل (كجم)", min_value=1.0, step=0.5)
if weight:
    water_ml = int(weight * 0.033 * 1000 + 500)
    st.session_state.meal_plan["client_info"]["weight"] = weight
    st.session_state.meal_plan["client_info"]["water_intake"] = f"{water_ml} مل"
    st.sidebar.success(f"💧 كمية الماء اليومية: {water_ml} مل")

# --- بيانات الوجبات ---
meal_titles = {
    "breakfast": "🍳 الفطور",
    "snack1": "🥜 سناك 1",
    "lunch": "🍗 الغداء",
    "pre_workout": "🥤 قبل التمرين",
    "dinner": "🍽️ العشاء",
    "night_snack": "🍮 سناك ليلي"
}

st.header("🍽️ أضف الوجبات")

for meal_key, meal_name in meal_titles.items():
    with st.expander(meal_name):
        food = st.text_input(f"اسم الطعام ({meal_name})", key=f"name_{meal_key}")
        qty = st.number_input("الكمية (جم)", min_value=1, value=100, step=10, key=f"qty_{meal_key}")
        if st.button("➕ أضف", key=f"add_{meal_key}"):
            if food:
                st.session_state.meal_plan["meals"][meal_key].append({
                    "name": food,
                    "quantity": qty
                })

        for i, item in enumerate(st.session_state.meal_plan["meals"][meal_key]):
            st.write(f"- {item['name']} - {item['quantity']} جم")
            if st.button("❌ حذف", key=f"del_{meal_key}_{i}"):
                del st.session_state.meal_plan["meals"][meal_key][i]
                st.experimental_rerun()

# --- المكملات ---
st.header("💊 مكملات")
supplement = st.text_input("اسم المكمل")
if st.button("➕ أضف مكمل"):
    if supplement.strip():
        st.session_state.meal_plan["supplements"].append(supplement.strip())

for i, s in enumerate(st.session_state.meal_plan["supplements"]):
    st.write(f"- {s}")
    if st.button("❌ حذف مكمل", key=f"del_supp_{i}"):
        del st.session_state.meal_plan["supplements"][i]
        st.experimental_rerun()

# --- إنشاء HTML ---
st.header("📤 تصدير HTML")

if st.button("📥 تحميل ملف HTML"):
    def build_html(plan):
        html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <style>
    body {{
      background-color: #2b0000;
      color: white;
      font-family: 'Cairo', sans-serif;
      padding: 20px;
    }}
    h2 {{ color: #FFD700; text-align: center; }}
    h3 {{ color: #FFD700; margin-top: 20px; }}
    ul {{ list-style-type: disc; padding-right: 20px; }}
    .logo {{ width: 100px; height: auto; }}
    .section {{ margin-bottom: 20px; }}
  </style>
</head>
<body>
"""
        if logo_data:
            html += f'<img src="data:image/png;base64,{logo_data}" class="logo" alt="Logo" />'
        html += f"<h2>نظامك الغذائي</h2>"

        for key, title in meal_titles.items():
            if plan["meals"][key]:
                html += f'<div class="section"><h3>{title}</h3><ul>'
                for item in plan["meals"][key]:
                    html += f"<li>{item['name']} - {item['quantity']} جم</li>"
                html += "</ul></div>"

        if plan["supplements"]:
            html += "<div class='section'><h3>المكملات الغذائية</h3><ul>"
            for s in plan["supplements"]:
                html += f"<li>{s}</li>"
            html += "</ul></div>"

        html += "<div class='section'><h3>نصائح</h3><ul>"
        for note in plan["notes"]:
            html += f"<li>{note}</li>"
        html += "</ul></div>"

        html += f"<p>💧 كمية الماء اليومية: {plan['client_info']['water_intake']}</p>"
        html += "</body></html>"
        return html

    html_content = build_html(st.session_state.meal_plan)
    st.download_button(
        label="⬇️ اضغط هنا لتحميل HTML",
        data=html_content,
        file_name=f"nutrition_plan_{datetime.now().strftime('%Y%m%d')}.html",
        mime="text/html"
    )
