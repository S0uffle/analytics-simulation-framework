import json
import os

# 1. Update sim_config.json
config_file = 'sim_config.json'
with open(config_file, 'r') as f:
    j = json.load(f)

if 'enable_weekly' not in j: j['enable_weekly'] = True
if 'enable_monthly' not in j: j['enable_monthly'] = True
if 'enable_yearly' not in j: j['enable_yearly'] = False
if 'enable_lifetime' not in j: j['enable_lifetime'] = False

with open(config_file, 'w') as f:
    json.dump(j, f, indent=4)

# 2. Update _pages/simulation_page.py
sim_page = '_pages/simulation_page.py'
with open(sim_page, 'r') as f:
    content = f.read()

content = content.replace(
    'enable_weekly = st.checkbox("📅 Weekly", value=True, key="enable_weekly")',
    'enable_weekly = st.checkbox("📅 Weekly", value=sim_cfg.get("enable_weekly", True), key="enable_weekly")'
)
content = content.replace(
    'enable_monthly = st.checkbox("📆 Monthly", value=True, key="enable_monthly")',
    'enable_monthly = st.checkbox("📆 Monthly", value=sim_cfg.get("enable_monthly", True), key="enable_monthly")'
)
content = content.replace(
    'enable_yearly = st.checkbox("📅 Yearly", value=False, key="enable_yearly")',
    'enable_yearly = st.checkbox("📅 Yearly", value=sim_cfg.get("enable_yearly", False), key="enable_yearly")'
)
content = content.replace(
    'enable_lifetime = st.checkbox("♾️ Lifetime", value=False, key="enable_lifetime")',
    'enable_lifetime = st.checkbox("♾️ Lifetime", value=sim_cfg.get("enable_lifetime", False), key="enable_lifetime")'
)

with open(sim_page, 'w') as f:
    f.write(content)

print("Checkboxes patched successfully!")
