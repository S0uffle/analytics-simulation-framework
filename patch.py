import re
import sys

filepath = '_pages/simulation_page.py'
with open(filepath, 'r') as f:
    content = f.read()

# Inject config loading
target_import = "            subscription_params = {}"
replacement_import = """            subscription_params = {}
            
            import json, os
            sim_cfg = {}
            if os.path.exists('sim_config.json'):
                try:
                    with open('sim_config.json', 'r') as f:
                        sim_cfg = json.load(f)
                except Exception:
                    pass"""
content = content.replace(target_import, replacement_import)

# Define replacements
replacements = [
    ('weekly_price = st.number_input("Giá ($)", 0.99, 999.0, 2.99, 0.50, key="weekly_price")', 'weekly_price = st.number_input("Giá ($)", 0.99, 999.0, float(sim_cfg.get("weekly_price", 2.99)), 0.50, key="weekly_price")'),
    ('weekly_pay_rate = st.slider("Pay Rate (%)", 0.0, 100.0, 2.0, 0.5, key="weekly_pay", help="% users mua gói này") / 100', 'weekly_pay_rate = st.slider("Pay Rate (%)", 0.0, 100.0, float(sim_cfg.get("weekly_pay_rate", 2.0)), 0.5, key="weekly_pay", help="% users mua gói này") / 100'),
    ('weekly_has_trial = st.checkbox("Có Trial", True, key="weekly_trial")', 'weekly_has_trial = st.checkbox("Có Trial", sim_cfg.get("weekly_has_trial", True), key="weekly_trial")'),
    ('weekly_has_intro = st.checkbox("Có giá ưu đãi tuần đầu", True, key="weekly_intro")', 'weekly_has_intro = st.checkbox("Có giá ưu đãi tuần đầu", sim_cfg.get("weekly_has_intro", True), key="weekly_intro")'),
    ('weekly_trial_days = st.number_input("Trial (ngày)", 1, 14, 3, key="weekly_trial_days")', 'weekly_trial_days = st.number_input("Trial (ngày)", 1, 14, int(sim_cfg.get("weekly_trial_days", 3)), key="weekly_trial_days")'),
    ('weekly_trial_rate = st.slider("Trial → Paid (%)", 0.0, 100.0, 15.0, 1.0, key="weekly_trial_rate") / 100', 'weekly_trial_rate = st.slider("Trial → Paid (%)", 0.0, 100.0, float(sim_cfg.get("weekly_trial_rate", 15.0)), 1.0, key="weekly_trial_rate") / 100'),
    ('weekly_intro_price = st.number_input("Giá ưu đãi ($)", 0.0, 999.0, 0.99, 0.50, key="weekly_intro_price")', 'weekly_intro_price = st.number_input("Giá ưu đãi ($)", 0.0, 999.0, float(sim_cfg.get("weekly_intro_price", 0.99)), 0.50, key="weekly_intro_price")'),
    ('weekly_ret_1 = st.slider("Cycle 1 (Gia hạn lần 1)", 0, 100, 50, 1, key="weekly_ret1") / 100', 'weekly_ret_1 = st.slider("Cycle 1 (Gia hạn lần 1)", 0, 100, int(sim_cfg.get("weekly_ret_1", 50)), 1, key="weekly_ret1") / 100'),
    ('weekly_ret_4 = st.slider("Cycle 4 (1 tháng)", 0, 100, 31, 1, key="weekly_ret4") / 100', 'weekly_ret_4 = st.slider("Cycle 4 (1 tháng)", 0, 100, int(sim_cfg.get("weekly_ret_4", 31)), 1, key="weekly_ret4") / 100'),
    ('weekly_ret_6 = st.slider("Cycle 6 (1.5 tháng)", 0, 100, 24, 1, key="weekly_ret6") / 100', 'weekly_ret_6 = st.slider("Cycle 6 (1.5 tháng)", 0, 100, int(sim_cfg.get("weekly_ret_6", 24)), 1, key="weekly_ret6") / 100'),
    ('weekly_ret_9 = st.slider("Cycle 9 (2 tháng)", 0, 100, 18, 1, key="weekly_ret9") / 100', 'weekly_ret_9 = st.slider("Cycle 9 (2 tháng)", 0, 100, int(sim_cfg.get("weekly_ret_9", 18)), 1, key="weekly_ret9") / 100'),
    ('weekly_ret_12 = st.slider("Cycle 12 (3 tháng)", 0, 100, 15, 1, key="weekly_ret12") / 100', 'weekly_ret_12 = st.slider("Cycle 12 (3 tháng)", 0, 100, int(sim_cfg.get("weekly_ret_12", 15)), 1, key="weekly_ret12") / 100'),
    ('weekly_ret_18 = st.slider("Cycle 18 (4.5 tháng)", 0, 100, 10, 1, key="weekly_ret18") / 100', 'weekly_ret_18 = st.slider("Cycle 18 (4.5 tháng)", 0, 100, int(sim_cfg.get("weekly_ret_18", 10)), 1, key="weekly_ret18") / 100'),

    ('monthly_price = st.number_input("Giá ($)", 1.99, 2999.0, 9.99, 1.0, key="monthly_price")', 'monthly_price = st.number_input("Giá ($)", 1.99, 2999.0, float(sim_cfg.get("monthly_price", 9.99)), 1.0, key="monthly_price")'),
    ('monthly_pay_rate = st.slider("Pay Rate (%)", 0.0, 100.0, 3.0, 0.5, key="monthly_pay") / 100', 'monthly_pay_rate = st.slider("Pay Rate (%)", 0.0, 100.0, float(sim_cfg.get("monthly_pay_rate", 3.0)), 0.5, key="monthly_pay") / 100'),
    ('monthly_has_trial = st.checkbox("Có Trial", True, key="monthly_trial")', 'monthly_has_trial = st.checkbox("Có Trial", sim_cfg.get("monthly_has_trial", True), key="monthly_trial")'),
    ('monthly_trial_days = st.number_input("Trial (ngày)", 1, 30, 7, key="monthly_trial_days")', 'monthly_trial_days = st.number_input("Trial (ngày)", 1, 30, int(sim_cfg.get("monthly_trial_days", 7)), key="monthly_trial_days")'),
    ('monthly_trial_rate = st.slider("Trial → Paid (%)", 0.0, 100.0, 20.0, 1.0, key="monthly_trial_rate") / 100', 'monthly_trial_rate = st.slider("Trial → Paid (%)", 0.0, 100.0, float(sim_cfg.get("monthly_trial_rate", 20.0)), 1.0, key="monthly_trial_rate") / 100'),
    ('monthly_ret_1 = st.slider("Cycle 1 (Gia hạn lần 1)", 0, 100, 55, 1, key="monthly_ret1") / 100', 'monthly_ret_1 = st.slider("Cycle 1 (Gia hạn lần 1)", 0, 100, int(sim_cfg.get("monthly_ret_1", 55)), 1, key="monthly_ret1") / 100'),
    ('monthly_ret_3 = st.slider("Cycle 3 (3 tháng)", 0, 100, 42, 1, key="monthly_ret3") / 100', 'monthly_ret_3 = st.slider("Cycle 3 (3 tháng)", 0, 100, int(sim_cfg.get("monthly_ret_3", 42)), 1, key="monthly_ret3") / 100'),
    ('monthly_ret_6 = st.slider("Cycle 6 (6 tháng)", 0, 100, 30, 1, key="monthly_ret6") / 100', 'monthly_ret_6 = st.slider("Cycle 6 (6 tháng)", 0, 100, int(sim_cfg.get("monthly_ret_6", 30)), 1, key="monthly_ret6") / 100'),
    ('monthly_ret_12 = st.slider("Cycle 12 (1 năm)", 0, 100, 20, 1, key="monthly_ret12") / 100', 'monthly_ret_12 = st.slider("Cycle 12 (1 năm)", 0, 100, int(sim_cfg.get("monthly_ret_12", 20)), 1, key="monthly_ret12") / 100'),

    ('yearly_price = st.number_input("Giá ($)", 9.99, 14999.0, 49.99, 5.0, key="yearly_price")', 'yearly_price = st.number_input("Giá ($)", 9.99, 14999.0, float(sim_cfg.get("yearly_price", 49.99)), 5.0, key="yearly_price")'),
    ('yearly_pay_rate = st.slider("Pay Rate (%)", 0.0, 100.0, 1.0, 0.2, key="yearly_pay") / 100', 'yearly_pay_rate = st.slider("Pay Rate (%)", 0.0, 100.0, float(sim_cfg.get("yearly_pay_rate", 1.0)), 0.2, key="yearly_pay") / 100'),
    ('yearly_has_trial = st.checkbox("Có Trial", True, key="yearly_trial")', 'yearly_has_trial = st.checkbox("Có Trial", sim_cfg.get("yearly_has_trial", True), key="yearly_trial")'),
    ('yearly_trial_days = st.number_input("Trial (ngày)", 1, 30, 7, key="yearly_trial_days")', 'yearly_trial_days = st.number_input("Trial (ngày)", 1, 30, int(sim_cfg.get("yearly_trial_days", 7)), key="yearly_trial_days")'),
    ('yearly_trial_rate = st.slider("Trial → Paid (%)", 0.0, 100.0, 25.0, 1.0, key="yearly_trial_rate") / 100', 'yearly_trial_rate = st.slider("Trial → Paid (%)", 0.0, 100.0, float(sim_cfg.get("yearly_trial_rate", 25.0)), 1.0, key="yearly_trial_rate") / 100'),

    ('lifetime_price = st.number_input("Giá ($)", 29.99, 29999.0, 99.99, 10.0, key="lifetime_price")', 'lifetime_price = st.number_input("Giá ($)", 29.99, 29999.0, float(sim_cfg.get("lifetime_price", 99.99)), 10.0, key="lifetime_price")'),
    ('lifetime_pay_rate = st.slider("Pay Rate (%)", 0.0, 100.0, 0.5, 0.1, key="lifetime_pay") / 100', 'lifetime_pay_rate = st.slider("Pay Rate (%)", 0.0, 100.0, float(sim_cfg.get("lifetime_pay_rate", 0.5)), 0.1, key="lifetime_pay") / 100')
]

for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
    elif "Tuần 2" in old:
        # Fallback if label changed "Gia hạn lần 1" vs "Tuần 2"
        old2 = old.replace("Gia hạn lần 1", "Tuần 2")
        new2 = new.replace("Gia hạn lần 1", "Tuần 2")
        content = content.replace(old2, new2)

with open(filepath, 'w') as f:
    f.write(content)
print("Patch applied successfully.")
