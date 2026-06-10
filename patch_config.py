import re

config_path = "config.py"
with open(config_path, "r") as f:
    content = f.read()

# Find the start of the Auto-loaded JSON Config block
start_marker = "# --- Auto-loaded JSON Config ---"
if start_marker in content:
    pre_content = content.split(start_marker)[0]
else:
    pre_content = content

new_loader = """# --- Auto-loaded JSON Config ---
import json, os
if os.path.exists('sim_config.json'):
    try:
        with open('sim_config.json', 'r') as f:
            j = json.load(f)
            # UA
            if 'ua_cpm' in j: CONFIG.ua.cpm = j['ua_cpm']
            if 'ua_ctr' in j: CONFIG.ua.ctr = j['ua_ctr']
            if 'ua_cvr' in j: CONFIG.ua.cvr = j['ua_cvr']
            if 'ua_organic_ratio' in j: CONFIG.ua.organic_ratio = j['ua_organic_ratio']
            
            # Ads
            if 'ads_ecpm_d0' in j: CONFIG.ads.ecpm_d0 = j['ads_ecpm_d0']
            if 'ads_impressions_d0' in j: CONFIG.ads.impressions_per_dau_d0 = j['ads_impressions_d0']
            
            # Retention
            if 'retention_d1' in j: CONFIG.retention.d1 = j['retention_d1']
            if 'retention_d3' in j: CONFIG.retention.d3 = j['retention_d3']
            if 'retention_d7' in j: CONFIG.retention.d7 = j['retention_d7']
            if 'retention_d14' in j: CONFIG.retention.d14 = j['retention_d14']
            if 'retention_d30' in j: CONFIG.retention.d30 = j['retention_d30']
            if 'retention_d60' in j: CONFIG.retention.d60 = j['retention_d60']
            if 'retention_d90' in j: CONFIG.retention.d90 = j['retention_d90']
            if 'retention_d180' in j: CONFIG.retention.d180 = j['retention_d180']
            if 'retention_d365' in j: CONFIG.retention.d365 = j['retention_d365']
            
            # Variation
            if 'cpm_variation' in j: CONFIG.simulation.cpm_variation = j['cpm_variation']
            if 'ctr_variation' in j: CONFIG.simulation.ctr_variation = j['ctr_variation']
            if 'cvr_variation' in j: CONFIG.simulation.cvr_variation = j['cvr_variation']
            if 'ecpm_variation' in j: CONFIG.simulation.ecpm_variation = j['ecpm_variation']
            if 'retention_variation' in j: CONFIG.simulation.retention_variation = j['retention_variation']
            if 'pay_rate_variation' in j: CONFIG.simulation.pay_rate_variation = j['pay_rate_variation']
            if 'sub_ret_variation' in j: CONFIG.simulation.sub_ret_variation = j['sub_ret_variation']
            
            # Subscriptions
            if 'weekly_price' in j: CONFIG.subscription.weekly.price = j['weekly_price']
            if 'weekly_pay_rate' in j: CONFIG.subscription.weekly.pay_rate = j['weekly_pay_rate'] / 100
            if 'weekly_has_trial' in j: CONFIG.subscription.weekly.has_trial = j['weekly_has_trial']
            if 'weekly_trial_days' in j: CONFIG.subscription.weekly.trial_days = j['weekly_trial_days']
            if 'weekly_trial_rate' in j: CONFIG.subscription.weekly.trial_to_paid_rate = j['weekly_trial_rate'] / 100
            if 'weekly_has_intro' in j: CONFIG.subscription.weekly.has_intro_price = j['weekly_has_intro']
            if 'weekly_intro_price' in j: CONFIG.subscription.weekly.intro_price = j['weekly_intro_price']
            if 'weekly_ret_1' in j: CONFIG.subscription.weekly.sub_retention.cycle_1 = j['weekly_ret_1'] / 100
            if 'weekly_ret_4' in j: CONFIG.subscription.weekly.sub_retention.cycle_4 = j['weekly_ret_4'] / 100
            if 'weekly_ret_6' in j: CONFIG.subscription.weekly.sub_retention.cycle_6 = j['weekly_ret_6'] / 100
            if 'weekly_ret_9' in j: CONFIG.subscription.weekly.sub_retention.cycle_8 = j['weekly_ret_9'] / 100
            if 'weekly_ret_12' in j: CONFIG.subscription.weekly.sub_retention.cycle_12 = j['weekly_ret_12'] / 100
            if 'weekly_ret_18' in j: CONFIG.subscription.weekly.sub_retention.cycle_24 = j['weekly_ret_18'] / 100
            
            if 'monthly_price' in j: CONFIG.subscription.monthly.price = j['monthly_price']
            if 'monthly_pay_rate' in j: CONFIG.subscription.monthly.pay_rate = j['monthly_pay_rate'] / 100
            if 'monthly_has_trial' in j: CONFIG.subscription.monthly.has_trial = j['monthly_has_trial']
            if 'monthly_trial_days' in j: CONFIG.subscription.monthly.trial_days = j['monthly_trial_days']
            if 'monthly_trial_rate' in j: CONFIG.subscription.monthly.trial_to_paid_rate = j['monthly_trial_rate'] / 100
            if 'monthly_ret_1' in j: CONFIG.subscription.monthly.sub_retention.cycle_1 = j['monthly_ret_1'] / 100
            if 'monthly_ret_3' in j: CONFIG.subscription.monthly.sub_retention.cycle_3 = j['monthly_ret_3'] / 100
            if 'monthly_ret_6' in j: CONFIG.subscription.monthly.sub_retention.cycle_6 = j['monthly_ret_6'] / 100
            if 'monthly_ret_12' in j: CONFIG.subscription.monthly.sub_retention.cycle_12 = j['monthly_ret_12'] / 100
            
            if 'yearly_price' in j: CONFIG.subscription.yearly.price = j['yearly_price']
            if 'yearly_pay_rate' in j: CONFIG.subscription.yearly.pay_rate = j['yearly_pay_rate'] / 100
            if 'yearly_has_trial' in j: CONFIG.subscription.yearly.has_trial = j['yearly_has_trial']
            if 'yearly_trial_days' in j: CONFIG.subscription.yearly.trial_days = j['yearly_trial_days']
            if 'yearly_trial_rate' in j: CONFIG.subscription.yearly.trial_to_paid_rate = j['yearly_trial_rate'] / 100
            
            if 'lifetime_price' in j: CONFIG.subscription.lifetime.price = j['lifetime_price']
            if 'lifetime_pay_rate' in j: CONFIG.subscription.lifetime.pay_rate = j['lifetime_pay_rate'] / 100

    except Exception as e:
        print("Error loading sim_config.json:", e)

if __name__ == "__main__":
"""

if "if __name__ == \"__main__\":" in pre_content:
    pre_content = pre_content.replace("if __name__ == \"__main\":", "")

content = pre_content + new_loader + "\n" + """    # Demo
    print("=" * 60)
    print("Analytics Business Framework - Configuration")
    print("=" * 60)
    
    print(f"\\n📊 UA Metrics:")
    print(f"   CPM: ${CONFIG.ua.cpm}")
    print(f"   CPI (paid): ${CONFIG.ua.cpi_paid:.2f}")
    print(f"   Organic ratio: {CONFIG.ua.organic_ratio * 100:.0f}%")
    print(f"   Blended CPI: ${CONFIG.ua.blended_cpi:.2f}")
    
    print(f"\\n📈 Ads Metrics (with decay):")
    print(f"   ARPDAU D0: ${CONFIG.ads.arpdau_d0:.4f}")
    print(f"   ARPDAU D30: ${CONFIG.ads.get_arpdau_at_day(30):.4f}")
    print(f"   ARPDAU D90: ${CONFIG.ads.get_arpdau_at_day(90):.4f}")
    print(f"   ARPDAU D365: ${CONFIG.ads.get_arpdau_at_day(365):.4f}")
    
    print(f"\\n📉 Retention Curve:")
    curve = CONFIG.retention.get_curve()
    for day, rate in curve.items():
        if day in [1, 7, 30]:
            print(f"   D{day}: {rate * 100:.1f}%")
    
    print(f"\\n💳 Subscription Plans:")
    for plan in CONFIG.subscription.get_all_plans():
        print(f"   {plan.name}: ${plan.price} / {plan.duration_days}d, pay_rate={plan.pay_rate*100:.1f}%")
"""

with open(config_path, "w") as f:
    f.write(content)
print("config.py updated with full subscription parsing!")
