"""
Analytics Business Framework - Configuration
Cấu hình toàn bộ thông số cho 5-step Data Flywheel

Các thông số có thể được override qua Dashboard hoặc .env file
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


# =====================================================
# 1. USER ACQUISITION (UA) METRICS
# =====================================================
@dataclass
class UAMetrics:
    """Thông số User Acquisition"""
    # CPM, CTR, CVR → tính ra CPI
    cpm: float = 5.0            # Cost per Mille ($)
    ctr: float = 0.02           # Click-Through Rate (2%)
    cvr: float = 0.45           # Conversion Rate (45%)
    
    # Organic ratio
    organic_ratio: float = 0.05  # 5% users là organic (không mất chi phí UA)
    
    @property
    def cpi_paid(self) -> float:
        """Cost per Install for paid users"""
        if self.ctr == 0 or self.cvr == 0:
            return float('inf')
        return self.cpm / (1000 * self.ctr * self.cvr)
    
    @property
    def blended_cpi(self) -> float:
        """Blended CPI including organic (organic CPI = 0)"""
        return self.cpi_paid * (1 - self.organic_ratio)


# =====================================================
# 2. MONETIZATION - ADS (IAA)
# =====================================================
@dataclass
class AdsMetrics:
    """Thông số In-App Advertising với decay theo lifetime"""
    # Thông số tại D0
    ecpm_d0: float = 12.0           # eCPM tại ngày đầu ($12)
    impressions_per_dau_d0: float = 6.0  # Số impressions/user/ngày tại D0
    
    # Decay parameters (sụt giảm theo thời gian)
    ecpm_saturation_ratio: float = 0.50      # eCPM giảm còn 50% so với D0 khi bão hòa
    impressions_saturation_ratio: float = 0.40  # Impressions giảm còn 40% so với D0
    decay_half_life_days: int = 30           # Thời gian để giảm 50% (half-life)
    
    def get_ecpm_at_day(self, day: int) -> float:
        """Tính eCPM tại ngày N với decay exponential"""
        if day <= 0:
            return self.ecpm_d0
        
        # Exponential decay towards saturation
        # ecpm(d) = ecpm_saturation + (ecpm_d0 - ecpm_saturation) * exp(-d/half_life)
        import math
        ecpm_saturation = self.ecpm_d0 * self.ecpm_saturation_ratio
        decay = math.exp(-day / self.decay_half_life_days)
        return ecpm_saturation + (self.ecpm_d0 - ecpm_saturation) * decay
    
    def get_impressions_at_day(self, day: int) -> float:
        """Tính số impressions tại ngày N với decay"""
        if day <= 0:
            return self.impressions_per_dau_d0
        
        import math
        imp_saturation = self.impressions_per_dau_d0 * self.impressions_saturation_ratio
        decay = math.exp(-day / self.decay_half_life_days)
        return imp_saturation + (self.impressions_per_dau_d0 - imp_saturation) * decay
    
    def get_arpdau_at_day(self, day: int) -> float:
        """ARPDAU tại ngày N = eCPM(N) * impressions(N) / 1000"""
        return self.get_ecpm_at_day(day) * self.get_impressions_at_day(day) / 1000
    
    @property
    def arpdau_d0(self) -> float:
        """ARPDAU tại D0"""
        return self.ecpm_d0 * self.impressions_per_dau_d0 / 1000


# =====================================================
# 3. RETENTION CURVE (tới D365)
# =====================================================
@dataclass
class RetentionMetrics:
    """Retention curve mở rộng tới D365"""
    # Key retention points
    d0: float = 1.00
    d1: float = 0.40
    d3: float = 0.30
    d7: float = 0.20
    d14: float = 0.15
    d30: float = 0.10
    d60: float = 0.07
    d90: float = 0.05
    d180: float = 0.03
    d365: float = 0.02
    
    def get_curve(self) -> Dict[int, float]:
        """Trả về retention curve dictionary"""
        return {
            0: self.d0,
            1: self.d1,
            3: self.d3,
            7: self.d7,
            14: self.d14,
            30: self.d30,
            60: self.d60,
            90: self.d90,
            180: self.d180,
            365: self.d365
        }
    
    def get_retention_at_day(self, day: int) -> float:
        """Interpolate retention tại bất kỳ ngày nào"""
        import numpy as np
        curve = self.get_curve()
        known_days = sorted(curve.keys())
        
        if day in curve:
            return curve[day]
        
        if day > max(known_days):
            return curve[max(known_days)]
        
        # Log-linear interpolation
        prev_day = max([d for d in known_days if d < day])
        next_day = min([d for d in known_days if d > day])
        
        prev_rate = curve[prev_day]
        next_rate = curve[next_day]
        progress = (day - prev_day) / (next_day - prev_day)
        
        log_prev = np.log(max(prev_rate, 0.001))
        log_next = np.log(max(next_rate, 0.001))
        return np.exp(log_prev + progress * (log_next - log_prev))


# =====================================================
# 4. SUBSCRIPTION & IAP
# =====================================================
@dataclass
class SubscriptionRetentionCurve:
    """Subscription Retention Curve - tương tự User Retention nhưng cho subscribers"""
    # Retention của subscribers sau mỗi billing cycle
    # cycle_0 = người mới subscribe (100%)
    # cycle_1 = sau lần thanh toán đầu tiên (renewal 1)
    # cycle_N = sau N lần thanh toán
    cycle_0: float = 1.00   # 100% - vừa mới subscribe
    cycle_1: float = 0.55   # 55% còn lại sau renewal đầu tiên
    cycle_2: float = 0.45   # 45% sau renewal thứ 2
    cycle_3: float = 0.38   # 38% 
    cycle_4: float = 0.32   # 32%
    cycle_5: float = 0.28   # 28% (thêm cho weekly)
    cycle_6: float = 0.25   # 25% sau 6 cycles
    cycle_8: float = 0.21   # 21% sau 8 cycles (~2 tháng với weekly)
    cycle_12: float = 0.18  # 18% sau 12 cycles (1 năm với monthly)
    cycle_24: float = 0.12  # 12% sau 24 cycles (2 năm)
    cycle_52: float = 0.08  # 8% sau 52 cycles (1 năm với weekly)
    
    def get_curve(self) -> Dict[int, float]:
        """Trả về subscription retention curve dictionary"""
        return {
            0: self.cycle_0,
            1: self.cycle_1,
            2: self.cycle_2,
            3: self.cycle_3,
            4: self.cycle_4,
            5: self.cycle_5,
            6: self.cycle_6,
            8: self.cycle_8,
            12: self.cycle_12,
            24: self.cycle_24,
            52: self.cycle_52
        }
    
    def get_retention_at_cycle(self, cycle: int) -> float:
        """Interpolate subscription retention tại bất kỳ cycle nào"""
        import numpy as np
        curve = self.get_curve()
        known_cycles = sorted(curve.keys())
        
        if cycle in curve:
            return curve[cycle]
        
        if cycle <= 0:
            return 1.0
        
        if cycle > max(known_cycles):
            # Decay tiếp theo tỷ lệ cuối cùng
            last_cycle = max(known_cycles)
            decay_rate = curve[last_cycle] / curve[known_cycles[-2]] if len(known_cycles) >= 2 else 0.9
            return curve[last_cycle] * (decay_rate ** (cycle - last_cycle))
        
        # Log-linear interpolation
        prev_cycle = max([c for c in known_cycles if c < cycle])
        next_cycle = min([c for c in known_cycles if c > cycle])
        
        prev_rate = curve[prev_cycle]
        next_rate = curve[next_cycle]
        progress = (cycle - prev_cycle) / (next_cycle - prev_cycle)
        
        log_prev = np.log(max(prev_rate, 0.001))
        log_next = np.log(max(next_rate, 0.001))
        return np.exp(log_prev + progress * (log_next - log_prev))


@dataclass
class SubscriptionPlan:
    """Một gói subscription cụ thể"""
    name: str                           # Tên gói: weekly, monthly, yearly, lifetime
    price: float                        # Giá ($)
    duration_days: int                  # Thời hạn (ngày): 7, 30, 365, 36500 (lifetime)
    pay_rate: float                     # Tỷ lệ user subscribe / total installs
    has_trial: bool = True              # Có trial không
    trial_days: int = 3                 # Số ngày trial
    trial_to_paid_rate: float = 0.20    # Tỷ lệ convert từ trial → paid
    
    # Ưu đãi mua gói lần đầu
    has_intro_price: bool = False       # Có giá ưu đãi lần đầu không
    intro_price: float = 0.0            # Giá ưu đãi lần đầu ($)
    
    # Subscription Retention Curve (thay thế renewal_rates)
    sub_retention: SubscriptionRetentionCurve = field(default_factory=SubscriptionRetentionCurve)
    
    # Legacy support: renewal_rates dict (deprecated, use sub_retention instead)
    renewal_rates: Dict[int, float] = field(default_factory=dict)
    
    def get_renewal_rate(self, cycle: int) -> float:
        """Lấy tỷ lệ còn lại tại cycle N (dùng subscription retention curve)"""
        if self.duration_days >= 36500:  # Lifetime - no renewal
            return 0
        
        # Renewal rate = ratio of retention at cycle N vs cycle N-1
        if cycle <= 0:
            return 1.0
        
        retention_current = self.sub_retention.get_retention_at_cycle(cycle)
        retention_prev = self.sub_retention.get_retention_at_cycle(cycle - 1)
        
        if retention_prev <= 0:
            return 0
        
        return retention_current / retention_prev
    
    def get_cumulative_retention(self, cycle: int) -> float:
        """Tỷ lệ subscribers còn lại sau N cycles"""
        return self.sub_retention.get_retention_at_cycle(cycle)


@dataclass
class SubscriptionMetrics:
    """Tổng hợp tất cả subscription plans"""
    # Ngày bắt đầu khai thác (show offer)
    exploitation_start_day: int = 0     # Khai thác từ ngày đầu tiên (D0)
    
    # Platform fee (App Store / Google Play)
    platform_fee_rate: float = 0.30     # 30% default (Apple/Google commission)
    
    # Các gói subscription
    weekly: SubscriptionPlan = field(default_factory=lambda: SubscriptionPlan(
        name="weekly",
        price=2.99,
        duration_days=7,
        pay_rate=0.02,          # 2% users mua weekly
        has_trial=True,
        trial_days=3,
        trial_to_paid_rate=0.15,
        has_intro_price=True,
        intro_price=0.99,
        # Weekly cần nhiều cycles hơn vì 52 tuần/năm
        sub_retention=SubscriptionRetentionCurve(
            cycle_0=1.00,   # Mới subscribe
            cycle_1=0.50,   # Tuần 2
            cycle_2=0.42,   # Tuần 3
            cycle_3=0.36,   # Tuần 4 (1 tháng)
            cycle_4=0.31,   # Tuần 5
            cycle_5=0.27,   # Tuần 6
            cycle_6=0.24,   # Tuần 7
            cycle_8=0.19,   # Tuần 9 (~2 tháng)
            cycle_12=0.15,  # Tuần 13 (~3 tháng)
            cycle_24=0.08,  # Tuần 25 (~6 tháng)
            cycle_52=0.03   # Tuần 53 (1 năm)
        )
    ))
    
    monthly: SubscriptionPlan = field(default_factory=lambda: SubscriptionPlan(
        name="monthly",
        price=9.99,
        duration_days=30,
        pay_rate=0.03,          # 3% users mua monthly
        has_trial=True,
        trial_days=7,
        trial_to_paid_rate=0.20,
        sub_retention=SubscriptionRetentionCurve(
            cycle_0=1.00, cycle_1=0.55, cycle_2=0.48, cycle_3=0.42,
            cycle_4=0.37, cycle_6=0.30, cycle_12=0.20, cycle_24=0.12, cycle_52=0.05
        )
    ))
    
    yearly: SubscriptionPlan = field(default_factory=lambda: SubscriptionPlan(
        name="yearly",
        price=49.99,
        duration_days=365,
        pay_rate=0.01,          # 1% users mua yearly
        has_trial=True,
        trial_days=7,
        trial_to_paid_rate=0.25,
        sub_retention=SubscriptionRetentionCurve(
            cycle_0=1.00, cycle_1=0.65, cycle_2=0.55, cycle_3=0.48,
            cycle_4=0.42, cycle_6=0.35, cycle_12=0.25, cycle_24=0.18, cycle_52=0.10
        )
    ))
    
    lifetime: SubscriptionPlan = field(default_factory=lambda: SubscriptionPlan(
        name="lifetime",
        price=99.99,
        duration_days=36500,    # ~100 years (effectively lifetime)
        pay_rate=0.005,         # 0.5% users mua lifetime
        has_trial=False,        # Lifetime không có trial
        trial_days=0,
        trial_to_paid_rate=1.0, # Trả ngay
        sub_retention=SubscriptionRetentionCurve()  # Không dùng (lifetime)
    ))
    
    def get_all_plans(self) -> List[SubscriptionPlan]:
        """Trả về tất cả subscription plans"""
        return [self.weekly, self.monthly, self.yearly, self.lifetime]
    
    def get_total_pay_rate(self) -> float:
        """Tổng tỷ lệ users có trả phí (any plan)"""
        return self.weekly.pay_rate + self.monthly.pay_rate + self.yearly.pay_rate + self.lifetime.pay_rate


# =====================================================
# 5. ALERT THRESHOLDS
# =====================================================
@dataclass
class AlertThresholds:
    """Ngưỡng cảnh báo cho monitoring"""
    roas_safe: float = 1.20         # ROAS > 120% = safe
    roas_warning: float = 1.00      # ROAS 80-100% = warning
    roas_danger: float = 0.80       # ROAS < 80% = danger
    
    retention_drop_warning: float = 0.10    # Giảm > 10% so với baseline
    retention_drop_danger: float = 0.20     # Giảm > 20%
    
    revenue_drop_warning: float = 0.15
    revenue_drop_danger: float = 0.30
    
    dau_drop_warning: float = 0.10
    dau_drop_danger: float = 0.25


# =====================================================
# 6. SIMULATION CONFIG
# =====================================================
@dataclass
class SimulationConfig:
    """Cấu hình cho Monte Carlo Simulation"""
    n_simulations: int = 1000       # Số kịch bản giả lập
    simulation_days: int = 365      # Số ngày dự báo
    confidence_level: float = 0.90  # Mức độ tin cậy
    
    # Độ biến động của các thông số (cho random sampling)
    cpm_variation: float = 0.15     # ±15%
    ctr_variation: float = 0.20     # ±20%
    cvr_variation: float = 0.25     # ±25%
    ecpm_variation: float = 0.20    # ±20%
    retention_variation: float = 0.15   # ±15%
    pay_rate_variation: float = 0.30    # ±30%
    sub_ret_variation: float = 0.20     # ±20% (Subscription Retention)


# =====================================================
# 7. BIGQUERY CONFIG
# =====================================================
@dataclass
class BigQueryConfig:
    """Cấu hình kết nối BigQuery"""
    project_id: str = field(default_factory=lambda: os.getenv("BQ_PROJECT_ID", "team-begamob"))
    dataset_id: str = field(default_factory=lambda: os.getenv("BQ_DATASET_ID", "analytics"))
    credentials_path: str = field(default_factory=lambda: os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""))
    
    # Table names
    daily_metrics_table: str = "daily_metrics"
    cohort_retention_table: str = "cohort_retention"
    campaigns_table: str = "campaigns"
    user_segments_table: str = "user_segments"
    funnel_table: str = "funnel_events"


# =====================================================
# MAIN CONFIG CLASS
# =====================================================
@dataclass
class AppConfig:
    """Master configuration combining all sub-configs"""
    ua: UAMetrics = field(default_factory=UAMetrics)
    ads: AdsMetrics = field(default_factory=AdsMetrics)
    retention: RetentionMetrics = field(default_factory=RetentionMetrics)
    subscription: SubscriptionMetrics = field(default_factory=SubscriptionMetrics)
    alerts: AlertThresholds = field(default_factory=AlertThresholds)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    bigquery: BigQueryConfig = field(default_factory=BigQueryConfig)
    
    # General settings
    simulation_days: int = 365


# Global config instance
CONFIG = AppConfig()


# =====================================================
# HELPER FUNCTIONS
# =====================================================
def create_config_from_dict(params: dict) -> AppConfig:
    """Tạo config từ dictionary (cho dashboard input)"""
    config = AppConfig()
    
    # UA params
    if 'cpm' in params:
        config.ua.cpm = params['cpm']
    if 'ctr' in params:
        config.ua.ctr = params['ctr']
    if 'cvr' in params:
        config.ua.cvr = params['cvr']
    if 'organic_ratio' in params:
        config.ua.organic_ratio = params['organic_ratio']
    
    # Ads params
    if 'ecpm_d0' in params:
        config.ads.ecpm_d0 = params['ecpm_d0']
    if 'impressions_per_dau_d0' in params:
        config.ads.impressions_per_dau_d0 = params['impressions_per_dau_d0']
    if 'ecpm_saturation_ratio' in params:
        config.ads.ecpm_saturation_ratio = params['ecpm_saturation_ratio']
    if 'decay_half_life_days' in params:
        config.ads.decay_half_life_days = params['decay_half_life_days']
    
    # Retention params
    if 'd1' in params:
        config.retention.d1 = params['d1']
    if 'd7' in params:
        config.retention.d7 = params['d7']
    if 'd30' in params:
        config.retention.d30 = params['d30']
    if 'd365' in params:
        config.retention.d365 = params['d365']
    
    # Subscription params
    if 'exploitation_start_day' in params:
        config.subscription.exploitation_start_day = params['exploitation_start_day']
    
    return config



# --- Auto-loaded JSON Config ---
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

    # Demo
    print("=" * 60)
    print("Analytics Business Framework - Configuration")
    print("=" * 60)
    
    print(f"\n📊 UA Metrics:")
    print(f"   CPM: ${CONFIG.ua.cpm}")
    print(f"   CPI (paid): ${CONFIG.ua.cpi_paid:.2f}")
    print(f"   Organic ratio: {CONFIG.ua.organic_ratio * 100:.0f}%")
    print(f"   Blended CPI: ${CONFIG.ua.blended_cpi:.2f}")
    
    print(f"\n📈 Ads Metrics (with decay):")
    print(f"   ARPDAU D0: ${CONFIG.ads.arpdau_d0:.4f}")
    print(f"   ARPDAU D30: ${CONFIG.ads.get_arpdau_at_day(30):.4f}")
    print(f"   ARPDAU D90: ${CONFIG.ads.get_arpdau_at_day(90):.4f}")
    print(f"   ARPDAU D365: ${CONFIG.ads.get_arpdau_at_day(365):.4f}")
    
    print(f"\n📉 Retention Curve:")
    curve = CONFIG.retention.get_curve()
    for day, rate in curve.items():
        if day in [1, 7, 30]:
            print(f"   D{day}: {rate * 100:.1f}%")
    
    print(f"\n💳 Subscription Plans:")
    for plan in CONFIG.subscription.get_all_plans():
        print(f"   {plan.name}: ${plan.price} / {plan.duration_days}d, pay_rate={plan.pay_rate*100:.1f}%")
