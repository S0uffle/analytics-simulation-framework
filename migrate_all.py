import json
import os

# 1. Read existing sim_config.json if exists
sim_config = {}
if os.path.exists('sim_config.json'):
    with open('sim_config.json', 'r') as f:
        sim_config = json.load(f)

# 2. Add defaults from config.py
# UA
if 'ua_cpm' not in sim_config: sim_config['ua_cpm'] = 5.0
if 'ua_ctr' not in sim_config: sim_config['ua_ctr'] = 0.02
if 'ua_cvr' not in sim_config: sim_config['ua_cvr'] = 0.45
if 'ua_organic_ratio' not in sim_config: sim_config['ua_organic_ratio'] = 0.05

# Ads
if 'ads_ecpm_d0' not in sim_config: sim_config['ads_ecpm_d0'] = 12.0
if 'ads_impressions_d0' not in sim_config: sim_config['ads_impressions_d0'] = 6.0

# Retention
if 'retention_d1' not in sim_config: sim_config['retention_d1'] = 0.40
if 'retention_d3' not in sim_config: sim_config['retention_d3'] = 0.30
if 'retention_d7' not in sim_config: sim_config['retention_d7'] = 0.20
if 'retention_d14' not in sim_config: sim_config['retention_d14'] = 0.15
if 'retention_d30' not in sim_config: sim_config['retention_d30'] = 0.10
if 'retention_d60' not in sim_config: sim_config['retention_d60'] = 0.07
if 'retention_d90' not in sim_config: sim_config['retention_d90'] = 0.05
if 'retention_d180' not in sim_config: sim_config['retention_d180'] = 0.03
if 'retention_d365' not in sim_config: sim_config['retention_d365'] = 0.02

# Variations
if 'cpm_variation' not in sim_config: sim_config['cpm_variation'] = 0.15
if 'ctr_variation' not in sim_config: sim_config['ctr_variation'] = 0.20
if 'cvr_variation' not in sim_config: sim_config['cvr_variation'] = 0.25
if 'ecpm_variation' not in sim_config: sim_config['ecpm_variation'] = 0.20
if 'impressions_variation' not in sim_config: sim_config['impressions_variation'] = 0.15
if 'retention_variation' not in sim_config: sim_config['retention_variation'] = 0.15
if 'pay_rate_variation' not in sim_config: sim_config['pay_rate_variation'] = 0.30
if 'sub_ret_variation' not in sim_config: sim_config['sub_ret_variation'] = 0.20

with open('sim_config.json', 'w') as f:
    json.dump(sim_config, f, indent=4)

# 3. Modify config.py to load this JSON at the bottom
config_py_path = 'config.py'
with open(config_py_path, 'r') as f:
    config_code = f.read()

injection = """
# --- Auto-loaded JSON Config ---
import json, os
if os.path.exists('sim_config.json'):
    try:
        with open('sim_config.json', 'r') as f:
            j = json.load(f)
            if 'ua_cpm' in j: CONFIG.ua.cpm = j['ua_cpm']
            if 'ua_ctr' in j: CONFIG.ua.ctr = j['ua_ctr']
            if 'ua_cvr' in j: CONFIG.ua.cvr = j['ua_cvr']
            if 'ua_organic_ratio' in j: CONFIG.ua.organic_ratio = j['ua_organic_ratio']
            
            if 'ads_ecpm_d0' in j: CONFIG.ads.ecpm_d0 = j['ads_ecpm_d0']
            if 'ads_impressions_d0' in j: CONFIG.ads.impressions_per_dau_d0 = j['ads_impressions_d0']
            
            if 'retention_d1' in j: CONFIG.retention.d1 = j['retention_d1']
            if 'retention_d3' in j: CONFIG.retention.d3 = j['retention_d3']
            if 'retention_d7' in j: CONFIG.retention.d7 = j['retention_d7']
            if 'retention_d14' in j: CONFIG.retention.d14 = j['retention_d14']
            if 'retention_d30' in j: CONFIG.retention.d30 = j['retention_d30']
            if 'retention_d60' in j: CONFIG.retention.d60 = j['retention_d60']
            if 'retention_d90' in j: CONFIG.retention.d90 = j['retention_d90']
            if 'retention_d180' in j: CONFIG.retention.d180 = j['retention_d180']
            if 'retention_d365' in j: CONFIG.retention.d365 = j['retention_d365']
            
            if 'cpm_variation' in j: CONFIG.simulation.cpm_variation = j['cpm_variation']
            if 'ctr_variation' in j: CONFIG.simulation.ctr_variation = j['ctr_variation']
            if 'cvr_variation' in j: CONFIG.simulation.cvr_variation = j['cvr_variation']
            if 'ecpm_variation' in j: CONFIG.simulation.ecpm_variation = j['ecpm_variation']
            if 'retention_variation' in j: CONFIG.simulation.retention_variation = j['retention_variation']
            if 'pay_rate_variation' in j: CONFIG.simulation.pay_rate_variation = j['pay_rate_variation']
            if 'sub_ret_variation' in j: CONFIG.simulation.sub_ret_variation = j['sub_ret_variation']
    except Exception as e:
        print("Error loading sim_config.json:", e)
"""

if "# --- Auto-loaded JSON Config ---" not in config_code:
    # insert before "if __name__ == '__main__':" or at the end
    if 'if __name__ == "__main__":' in config_code:
        config_code = config_code.replace('if __name__ == "__main__":', injection + '\n\nif __name__ == "__main__":')
    else:
        config_code += injection

    with open(config_py_path, 'w') as f:
        f.write(config_code)

# 4. Patch _pages/simulation_page.py to use CONFIG.simulation.* for variations instead of hardcoded `value=1.0`
sim_page_path = '_pages/simulation_page.py'
with open(sim_page_path, 'r') as f:
    sim_code = f.read()

sim_code = sim_code.replace(
    'min_value=0.0, max_value=5000.0, value=1.0, step=0.5,',
    'min_value=0.0, max_value=5000.0, value=float(CONFIG.simulation.cpm_variation * 100), step=0.5,'
)
sim_code = sim_code.replace(
    'cpm_variation = st.slider(\n                "CPM Variation (%)",\n                min_value=0.0, max_value=5000.0, value=1.0, step=0.5,',
    'cpm_variation = st.slider(\n                "CPM Variation (%)",\n                min_value=0.0, max_value=5000.0, value=float(CONFIG.simulation.cpm_variation * 100), step=0.5,'
)
sim_code = sim_code.replace(
    'ctr_variation = st.slider(\n                "CTR Variation (%)",\n                min_value=0.0, max_value=5000.0, value=1.0, step=0.5,',
    'ctr_variation = st.slider(\n                "CTR Variation (%)",\n                min_value=0.0, max_value=5000.0, value=float(CONFIG.simulation.ctr_variation * 100), step=0.5,'
)
sim_code = sim_code.replace(
    'cvr_variation = st.slider(\n                "CVR Variation (%)",\n                min_value=0.0, max_value=6000.0, value=1.0, step=0.5,',
    'cvr_variation = st.slider(\n                "CVR Variation (%)",\n                min_value=0.0, max_value=6000.0, value=float(CONFIG.simulation.cvr_variation * 100), step=0.5,'
)
sim_code = sim_code.replace(
    'ecpm_variation = st.slider(\n                "eCPM Variation (%)",\n                min_value=0.0, max_value=5000.0, value=1.0, step=0.5,',
    'ecpm_variation = st.slider(\n                "eCPM Variation (%)",\n                min_value=0.0, max_value=5000.0, value=float(CONFIG.simulation.ecpm_variation * 100), step=0.5,'
)
sim_code = sim_code.replace(
    'impressions_variation = st.slider(\n                "Impressions Variation (%)",\n                min_value=0.0, max_value=4000.0, value=1.0, step=0.5,',
    'impressions_variation = st.slider(\n                "Impressions Variation (%)",\n                min_value=0.0, max_value=4000.0, value=float(CONFIG.simulation.ecpm_variation * 100), step=0.5,' # simplified fallback
)
sim_code = sim_code.replace(
    'retention_variation = st.slider(\n                "Retention Variation (%)",\n                min_value=0.0, max_value=5000.0, value=1.0, step=0.5,',
    'retention_variation = st.slider(\n                "Retention Variation (%)",\n                min_value=0.0, max_value=5000.0, value=float(CONFIG.simulation.retention_variation * 100), step=0.5,'
)
sim_code = sim_code.replace(
    'pay_rate_variation = st.slider(\n                "Pay Rate Variation (%)",\n                min_value=0.0, max_value=5000.0, value=1.0, step=0.5,',
    'pay_rate_variation = st.slider(\n                "Pay Rate Variation (%)",\n                min_value=0.0, max_value=5000.0, value=float(CONFIG.simulation.pay_rate_variation * 100), step=0.5,'
)
sim_code = sim_code.replace(
    'sub_ret_variation = st.slider(\n                "Sub Retention Variation (%)",\n                min_value=0.0, max_value=5000.0, value=1.0, step=0.5,',
    'sub_ret_variation = st.slider(\n                "Sub Retention Variation (%)",\n                min_value=0.0, max_value=5000.0, value=float(CONFIG.simulation.sub_ret_variation * 100), step=0.5,'
)

with open(sim_page_path, 'w') as f:
    f.write(sim_code)

print("Migration completed successfully.")
