import streamlit as st
import json

# تحميل قاعدة بيانات الطعام
with open("nutrition_data.json", "r", encoding="utf-8") as f:
    food_data = json.load(f)

st.title("🧮 حساب السعرات والماكروز")
st.markdown("احسب كمية المياه اليومية وخطتك الغذائية بسهولة")

# ✅ الوزن وحساب الماء
weight = st.number_input("📦 أدخل وزنك بالكيلوغرام:", min_value=1.0, step=1.0)
if weight:
    water_intake = weight * 0.033 * 1000 + 500
    st.success(f"💧 الكمية الموصى بها: {water_intake:.0f} مل يوميًا")

# ✅ اختيار الطعام
st.subheader("🍴 اختر طعامًا وأدخل الكمية:")
food_names = [f["name"] for f in food_data]
selected_food = st.selectbox("اختر من القائمة:", food_names)
quantity = st.number_input("الكمية (جرام):", min_value=1.0, step=10.0, value=100.0)

# حساب القيم الغذائية
if selected_food and quantity:
    food_item = next(f for f in food_data if f["name"] == selected_food)
    cal = food_item["calories"] * quantity / 100
    p = food_item["protein"] * quantity / 100
    c = food_item["carbs"] * quantity / 100
    f_ = food_item["fat"] * quantity / 100

    st.info(f"🔍 القيم لـ {quantity:.0f} جرام من {selected_food}:")
    st.write(f"✅ السعرات: {cal:.1f} kcal")
    st.write(f"💪 البروتين: {p:.1f} g")
    st.write(f"🥔 الكارب: {c:.1f} g")
    st.write(f"🧈 الدهون: {f_:.1f} g")

# تجميع وجبة
if "meal" not in st.session_state:
    st.session_state.meal = []

if st.button("➕ أضف للطعام"):
    st.session_state.meal.append({
        "name": selected_food,
        "quantity": quantity,
        "cal": cal,
        "protein": p,
        "carbs": c,
        "fat": f_
    })

if st.session_state.meal:
    st.subheader("🍽️ الوجبة الحالية:")
    total = {"cal": 0, "protein": 0, "carbs": 0, "fat": 0}
    for item in st.session_state.meal:
        st.write(f"- {item['name']} - {item['quantity']} جم | {item['cal']:.1f} kcal")
        total["cal"] += item["cal"]
        total["protein"] += item["protein"]
        total["carbs"] += item["carbs"]
        total["fat"] += item["fat"]

    st.success(f"✅ المجموع الكلي:")
    st.write(f"🔸 السعرات: {total['cal']:.1f} kcal")
    st.write(f"💪 البروتين: {total['protein']:.1f} g")
    st.write(f"🥔 الكارب: {total['carbs']:.1f} g")
    st.write(f"🧈 الدهون: {total['fat']:.1f} g")

if st.button("🗑️ إعادة تعيين"):
    st.session_state.meal = []
