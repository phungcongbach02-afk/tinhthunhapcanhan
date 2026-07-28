import streamlit as st
import pandas as pd
import plotly.express as px

# Thiết lập trang Streamlit
st.set_page_config(
    page_title="Công Cụ Tính Thuế TNCN Việt Nam bởi sinh viên PHÙNG CÔNG BÁCH",
    page_icon="💰",
    layout="wide"
)

# Thêm CSS tùy chỉnh giao diện
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">💰 Công Cụ Tính Thuế Thu Nhập Cá Nhân (TNCN)</div>', unsafe_allow_html=True)
st.caption("Cập nhật theo biểu thuế lũy tiến và mức giảm trừ gia cảnh mới nhất")

# Sidebar - Nhập dữ liệu
st.sidebar.header("⚙️ Cấu Hình Thu Nhập")

regulation_year = st.sidebar.radio(
    "Áp dụng quy định thuế:",
    options=["Quy định Mới (Biểu thuế 5 bậc)", "Quy định Cũ (Biểu thuế 7 bậc)"],
    index=0,
    help="Quy định mới áp dụng mức giảm trừ bản thân 15.5tr, NPT 6.2tr và biểu thuế 5 bậc."
)

is_new_rules = "Mới" in regulation_year

gross_salary = st.sidebar.number_input(
    "Lương Gross hàng tháng (VNĐ):",
    min_value=0,
    value=35000000,
    step=1000000,
    format="%d"
)

num_dependents = st.sidebar.number_input(
    "Số người phụ thuộc:",
    min_value=0,
    max_value=20,
    value=1,
    step=1
)

other_deductions = st.sidebar.number_input(
    "Các khoản giảm trừ khác (Từ thiện, hưu trí tự nguyện...) (VNĐ):",
    min_value=0,
    value=0,
    step=500000,
    format="%d"
)

# Cấu hình bảo hiểm bắt buộc
st.sidebar.subheader("🛡️ Bảo Hiểm Bắt Buộc (10.5%)")
apply_insurance = st.sidebar.checkbox("Tính khấu trừ BHXH, BHYT, BHTN", value=True)

if apply_insurance:
    insurance_salary = st.sidebar.number_input(
        "Mức lương đóng bảo hiểm (VNĐ):",
        min_value=0,
        value=gross_salary,
        step=1000000,
        format="%d",
        help="Thường là lương Gross hoặc lương tối thiểu vùng/lương đóng BH"
    )
    # Tỷ lệ đóng BHXH: 8%, BHYT: 1.5%, BHTN: 1% => Tổng 10.5%
    insurance_amount = min(insurance_salary * 0.105, 4680000)  # Tối đa theo quy định
else:
    insurance_amount = 0

# Thông số thuế theo quy định
if is_new_rules:
    SELF_DEDUCTION = 15_500_000
    DEPENDENT_DEDUCTION = 6_200_000
    # Biểu thuế 5 bậc mới
    TAX_BRACKETS = [
        (10_000_000, 0.05),
        (30_000_000, 0.10),
        (60_000_000, 0.20),
        (100_000_000, 0.30),
        (float('inf'), 0.35)
    ]
else:
    SELF_DEDUCTION = 11_000_000
    DEPENDENT_DEDUCTION = 4_400_000
    # Biểu thuế 7 bậc cũ
    TAX_BRACKETS = [
        (5_000_000, 0.05),
        (10_000_000, 0.10),
        (18_000_000, 0.15),
        (32_000_000, 0.20),
        (52_000_000, 0.25),
        (80_000_000, 0.30),
        (float('inf'), 0.35)
    ]

# Tính toán
total_dependent_deduction = num_dependents * DEPENDENT_DEDUCTION
total_deductions = SELF_DEDUCTION + total_dependent_deduction + insurance_amount + other_deductions
taxable_income = max(0, gross_salary - total_deductions)

# Hàm tính thuế từng bậc
def calculate_pit(income, brackets):
    remaining = income
    previous_limit = 0
    bracket_details = []
    total_tax = 0

    for limit, rate in brackets:
        if remaining <= 0:
            break
        
        bracket_range = limit - previous_limit
        taxable_in_bracket = min(remaining, bracket_range)
        tax_in_bracket = taxable_in_bracket * rate
        total_tax += tax_in_bracket

        bracket_details.append({
            "Mức thu nhập tính thuế": f"{int(previous_limit/1e6)}tr - {int(limit/1e6) if limit != float('inf') else 'Trở lên'}tr",
            "Thuế suất": f"{int(rate * 100)}%",
            "Thu nhập tính thuế bậc này": taxable_in_bracket,
            "Tiền thuế bậc này": tax_in_bracket
        })

        remaining -= taxable_in_bracket
        previous_limit = limit

    return total_tax, bracket_details

pit_tax, tax_details = calculate_pit(taxable_income, TAX_BRACKETS)
net_salary = gross_salary - insurance_amount - pit_tax

# Hiển thị Kết Quả Overview
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="💵 Lương GROSS", value=f"{gross_salary:,.0f} đ")

with col2:
    st.metric(label="🛡️ BHXH, BHYT, BHTN", value=f"{insurance_amount:,.0f} đ")

with col3:
    st.metric(label="🏛️ Thuế TNCN Phải Nộp", value=f"{pit_tax:,.0f} đ", delta=f"{(pit_tax/gross_salary*100) if gross_salary else 0:.1f}% Gross", delta_color="inverse")

with col4:
    st.metric(label="🎉 Lương NET Thực Nhận", value=f"{net_salary:,.0f} đ")

st.markdown("---")

# Tab Chi Tiết
tab1, tab2, tab3 = st.tabs(["📊 Diễn Giải Chi Tiết", "📋 Chi Tiết Từng Bậc Thuế", "📈 Biểu Đồ Phân PBThu Nhập"])

with tab1:
    st.subheader("Chi Tiết Các Khoản Khấu Trừ")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.write(f"- **Giảm trừ bản thân:** {SELF_DEDUCTION:,.0f} đ")
        st.write(f"- **Giảm trừ người phụ thuộc ({num_dependents} người):** {total_dependent_deduction:,.0f} đ")
        st.write(f"- **Bảo hiểm bắt buộc:** {insurance_amount:,.0f} đ")
        st.write(f"- **Khoản giảm trừ khác:** {other_deductions:,.0f} đ")
        st.markdown(f"👉 **Tổng các khoản giảm trừ:** `{total_deductions:,.0f} đ`")

    with col_b:
        st.write(f"- **Lương Gross:** {gross_salary:,.0f} đ")
        st.write(f"- **Thu nhập tính thuế (Gross - Giảm trừ):** {taxable_income:,.0f} đ")
        st.write(f"- **Thuế TNCN tạm tính:** {pit_tax:,.0f} đ")
        st.markdown(f"👉 **Thu nhập thực nhận (NET):** `{net_salary:,.0f} đ`")

with tab2:
    st.subheader("Bảng Bậc Thuế Áp Dụng")
    if tax_details:
        df_tax = pd.DataFrame(tax_details)
        df_tax["Thu nhập tính thuế bậc này"] = df_tax["Thu nhập tính thuế bậc này"].apply(lambda x: f"{x:,.0f} đ")
        df_tax["Tiền thuế bậc này"] = df_tax["Tiền thuế bậc này"].apply(lambda x: f"{x:,.0f} đ")
        st.table(df_tax)
    else:
        st.success("🎉 Bạn chưa đạt ngưỡng thu nhập phải nộp thuế TNCN!")

with tab3:
    # Biểu đồ phân bổ Lương Gross
    data_chart = {
        "Thành phần": ["Lương NET", "Bảo hiểm", "Thuế TNCN"],
        "Số tiền": [net_salary, insurance_amount, pit_tax]
    }
    df_chart = pd.DataFrame(data_chart)
    fig = px.pie(
        df_chart, 
        values="Số tiền", 
        names="Thành phần", 
        title="Tỷ Lệ Phân Bổ Lương Gross",
        color="Thành phần",
        color_discrete_map={"Lương NET": "#10B981", "Bảo hiểm": "#F59E0B", "Thuế TNCN": "#EF4444"}
    )
    st.plotly_chart(fig, use_container_width=True)

# Footnote
st.markdown("---")
st.caption("📌 *Lưu ý: Công cụ chỉ mang tính chất tham khảo dựa trên quy định biểu thuế mới nhất.*")
