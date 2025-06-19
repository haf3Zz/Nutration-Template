
import streamlit as st
import json

# تحميل قاعدة بيانات الطعام
with open("nutrition_data.json", "r", encoding="utf-8") as f:
    food_db = json.load(f)

st.set_page_config(page_title="Nutrition Plan Creator", layout="wide")
st.title("🥗 Nutrition Plan Creator (Streamlit Version)")

# بيانات العميل
with st.sidebar:
    st.header("📋 Client Info")
    weight = st.number_input("الوزن (كجم)", min_value=1.0, step=0.5)
    if weight:
        water_ml = weight * 0.033 * 1000 + 500
        st.success(f"💧 كمية الماء الموصى بها: {water_ml:.0f} مل")

# تعريف الوجبات
meal_names = {
    "breakfast": "🍳 فطور",
    "snack1": "🍌 سناك 1",
    "lunch": "🍗 غداء",
    "pre_workout": "🥤 قبل التمرين",
    "dinner": "🍽️ عشاء",
    "night_snack": "🍮 سناك ليلي"
}

if "meals" not in st.session_state:
    st.session_state.meals = {k: [] for k in meal_names}

# اختيار الوجبة الحالية
meal_selected = st.selectbox("اختر الوجبة التي تضيف إليها:", list(meal_names.keys()), format_func=lambda x: meal_names[x])

# اختيار الطعام والكمية
food_names = [f["name"] for f in food_db]
selected_food = st.selectbox("اختر الطعام:", food_names)
quantity = st.number_input("الكمية (جم)", min_value=1.0, value=100.0, step=10.0)

if st.button("➕ أضف إلى الوجبة"):
    food_item = next((f for f in food_db if f["name"] == selected_food), None)
    if food_item:
        st.session_state.meals[meal_selected].append({
            "name": selected_food,
            "quantity": quantity,
            "calories": food_item["calories"] * quantity / 100,
            "protein": food_item["protein"] * quantity / 100,
            "carbs": food_item["carbs"] * quantity / 100,
            "fat": food_item["fat"] * quantity / 100
        })

# عرض الوجبات
st.subheader("📊 خطة الوجبات")
total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}

for meal_id, items in st.session_state.meals.items():
    if items:
        st.markdown(f"### {meal_names[meal_id]}")
        for item in items:
            st.write(f"- {item['name']} | {item['quantity']} جم | {item['calories']:.1f} kcal | بروتين: {item['protein']:.1f}g | كارب: {item['carbs']:.1f}g | دهون: {item['fat']:.1f}g")
            total["calories"] += item["calories"]
            total["protein"] += item["protein"]
            total["carbs"] += item["carbs"]
            total["fat"] += item["fat"]

# إجمالي القيم الغذائية
st.success(f"🔢 الإجمالي الكلي: {total['calories']:.0f} kcal | بروتين: {total['protein']:.1f}g | كارب: {total['carbs']:.1f}g | دهون: {total['fat']:.1f}g")
