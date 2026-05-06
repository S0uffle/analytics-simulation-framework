"""
Analytics Business Framework - Step 1: Simulation
Monte Carlo & What-if Analysis (Enhanced Version)

Trả lời câu hỏi: "Nếu chúng ta tăng ngân sách quảng cáo 20% và CPI tăng 5%, 
lợi nhuận cuối tháng sẽ ra sao?"

Enhanced features:
- Organic user ratio
- eCPM/Impressions decay over lifetime
- Retention curve up to D365
- Multiple subscription plans with renewals
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from scipy import stats
import math

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CONFIG, AppConfig, create_config_from_dict


@dataclass
class SimulationParams:
    """Parameters for a single simulation run"""
    # UA params
    cpm: float
    ctr: float
    cvr: float
    organic_ratio: float
    
    # Ads params
    ecpm_d0: float
    impressions_d0: float
    ecpm_saturation_ratio: float
    impressions_saturation_ratio: float
    decay_half_life: int
    
    # Retention multiplier
    retention_mult: float
    
    # Subscription multipliers
    pay_rate_mult: float
    renewal_mult: float
    
    @property
    def cpi_paid(self) -> float:
        """Calculate CPI from UA metrics"""
        if self.ctr == 0 or self.cvr == 0:
            return float('inf')
        return self.cpm / (1000 * self.ctr * self.cvr)
    
    @property
    def blended_cpi(self) -> float:
        """Blended CPI including organic"""
        return self.cpi_paid * (1 - self.organic_ratio)
    
    def get_ecpm_at_day(self, day: int) -> float:
        """eCPM with decay"""
        if day <= 0:
            return self.ecpm_d0
        ecpm_sat = self.ecpm_d0 * self.ecpm_saturation_ratio
        decay = math.exp(-day / self.decay_half_life)
        return ecpm_sat + (self.ecpm_d0 - ecpm_sat) * decay
    
    def get_impressions_at_day(self, day: int) -> float:
        """Impressions with decay"""
        if day <= 0:
            return self.impressions_d0
        imp_sat = self.impressions_d0 * self.impressions_saturation_ratio
        decay = math.exp(-day / self.decay_half_life)
        return imp_sat + (self.impressions_d0 - imp_sat) * decay
    
    def get_arpdau_at_day(self, day: int) -> float:
        """ARPDAU at day N"""
        return self.get_ecpm_at_day(day) * self.get_impressions_at_day(day) / 1000


class EnhancedMonteCarloSimulator:
    """
    Enhanced Monte Carlo Simulation
    
    Features:
    - Organic user ratio
    - eCPM/Impressions decay
    - Full subscription model with renewals
    - D365 simulation
    """
    
    def __init__(self, config: AppConfig = None, n_simulations: int = None):
        self.config = config or CONFIG
        self.n_simulations = n_simulations or self.config.simulation.n_simulations
        self.results: List[Dict] = []
        
    def _sample_params(self) -> SimulationParams:
        """Generate sampled parameters with variation"""
        cfg = self.config
        sim = cfg.simulation
        
        def sample_with_variation(mean: float, variation: float, min_ratio: float = 0.3, max_ratio: float = 2.0) -> float:
            """Sample from normal distribution, or return mean if variation is 0"""
            if variation == 0 or variation < 0.001:
                return mean
            
            std = mean * variation
            while True:
                value = np.random.normal(mean, std)
                if mean * min_ratio <= value <= mean * max_ratio:
                    return value
        
        # Check if ALL variations are essentially zero (deterministic mode)
        is_deterministic = all([
            sim.cpm_variation < 0.001,
            sim.ctr_variation < 0.001,
            sim.cvr_variation < 0.001,
            sim.ecpm_variation < 0.001,
            sim.retention_variation < 0.001,
            sim.pay_rate_variation < 0.001,
            sim.sub_ret_variation < 0.001
        ])
        
        if is_deterministic:
            # Deterministic mode - use exact values
            return SimulationParams(
                cpm=cfg.ua.cpm,
                ctr=cfg.ua.ctr,
                cvr=cfg.ua.cvr,
                organic_ratio=cfg.ua.organic_ratio,
                
                ecpm_d0=cfg.ads.ecpm_d0,
                impressions_d0=cfg.ads.impressions_per_dau_d0,
                ecpm_saturation_ratio=cfg.ads.ecpm_saturation_ratio,
                impressions_saturation_ratio=cfg.ads.impressions_saturation_ratio,
                decay_half_life=cfg.ads.decay_half_life_days,
                
                retention_mult=1.0,
                pay_rate_mult=1.0,
                renewal_mult=1.0
            )
        else:
            # Stochastic mode - sample with variation
            # Calculate a small organic variation proportional to other variations
            avg_variation = (sim.cpm_variation + sim.ctr_variation + sim.cvr_variation) / 3
            organic_variation = min(0.03, avg_variation * 0.5)  # Cap at 3%, scale with other variations
            
            return SimulationParams(
                cpm=sample_with_variation(cfg.ua.cpm, sim.cpm_variation),
                ctr=sample_with_variation(cfg.ua.ctr, sim.ctr_variation),
                cvr=sample_with_variation(cfg.ua.cvr, sim.cvr_variation),
                organic_ratio=min(0.8, max(0.05, cfg.ua.organic_ratio + np.random.normal(0, organic_variation))),
                
                ecpm_d0=sample_with_variation(cfg.ads.ecpm_d0, sim.ecpm_variation),
                impressions_d0=sample_with_variation(cfg.ads.impressions_per_dau_d0, sim.ecpm_variation),
                ecpm_saturation_ratio=cfg.ads.ecpm_saturation_ratio,
                impressions_saturation_ratio=cfg.ads.impressions_saturation_ratio,
                decay_half_life=cfg.ads.decay_half_life_days,
                
                retention_mult=sample_with_variation(1.0, sim.retention_variation, 0.6, 1.5),
                pay_rate_mult=sample_with_variation(1.0, sim.pay_rate_variation, 0.5, 2.0),
                # renewal_mult capped tighter (0.97-1.03) to prevent compounding effect over many cycles
                renewal_mult=sample_with_variation(1.0, sim.sub_ret_variation, 0.97, 1.03)
            )
    
    def _is_deterministic(self) -> bool:
        """Check if simulation should run in deterministic mode"""
        sim = self.config.simulation
        return all([
            sim.cpm_variation < 0.001,
            sim.ctr_variation < 0.001,
            sim.cvr_variation < 0.001,
            sim.ecpm_variation < 0.001,
            sim.retention_variation < 0.001,
            sim.pay_rate_variation < 0.001,
            sim.sub_ret_variation < 0.001
        ])
    
    def _get_retention_at_day(self, day: int, retention_mult: float) -> float:
        """Get retention rate at day N with multiplier"""
        base_rate = self.config.retention.get_retention_at_day(day)
        adjusted = base_rate * retention_mult
        return min(1.0, max(0.0001, adjusted))
    
    def _calculate_ltv(self, params: SimulationParams, days: int = 365) -> Dict:
        """
        Calculate detailed LTV breakdown
        
        In deterministic mode: Uses expected values (pay_rate * price instead of random sampling)
        In stochastic mode: Uses random sampling for subscription decisions
        
        Returns:
            Dict with ltv_iaa, ltv_iap, ltv_total, and daily breakdown
        """
        cfg = self.config
        is_deterministic = self._is_deterministic()
        
        ltv_iaa = 0  # In-App Advertising
        ltv_iap = 0  # In-App Purchases / Subscriptions
        
        exploitation_day = cfg.subscription.exploitation_start_day
        
        if is_deterministic:
            # DETERMINISTIC MODE: Calculate expected LTV using expected values
            
            # Track cumulative LTV at milestones for curve plotting (more granular for smooth curve)
            milestones = [0, 1, 3, 7, 14, 21, 30, 45, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 365]
            cumulative_at_milestone = {m: {'iaa': 0, 'iap': 0} for m in milestones}
            
            # IAA: Sum of ARPDAU * retention over all days
            cumulative_iaa = 0
            for day in range(days + 1):
                retention = self._get_retention_at_day(day, params.retention_mult)
                daily_iaa = retention * params.get_arpdau_at_day(day)
                cumulative_iaa += daily_iaa
                
                # Record at milestones
                if day in cumulative_at_milestone:
                    cumulative_at_milestone[day]['iaa'] = cumulative_iaa
            
            ltv_iaa = cumulative_iaa
            
            # IAP: Expected value from each subscription plan
            # First, calculate all payment events with their days
            iap_events = []  # [(day, amount), ...]
            
            for plan in cfg.subscription.get_all_plans():
                effective_pay_rate = plan.pay_rate * params.pay_rate_mult
                
                if plan.has_trial:
                    expected_subscribers = effective_pay_rate * plan.trial_to_paid_rate
                else:
                    expected_subscribers = effective_pay_rate
                
                # First payment
                first_day = exploitation_day + (plan.trial_days if plan.has_trial else 0)
                if first_day <= days:
                    # Cycle 0: 100% of those who converted (no App_Retention needed for subscription)
                    current_sub_retention = 1.0 
                    
                    # LTV_Sub = Pay_Rate × Trial_to_Paid × Sub_Retention × Price
                    # (App_Retention removed - subscription auto-renews via app store)
                    payment = expected_subscribers * current_sub_retention * plan.price
                    iap_events.append((first_day, payment))
                    
                    # Renewal payments
                    if plan.duration_days < 36500:
                        cycle = 1
                        next_day = first_day + plan.duration_days
                        
                        while next_day <= days and cycle <= 52:
                            # Calculate renewal rate for this step (Sub Retention k / Sub Retention k-1)
                            step_renewal_rate = plan.get_renewal_rate(cycle) * params.renewal_mult
                            
                            # Update cumulative subscription retention
                            current_sub_retention *= step_renewal_rate
                            
                            # Calculate revenue: Initial_Subs × Sub_Retention × Price
                            # (App_Retention removed - subscription auto-renews via app store)
                            payment = expected_subscribers * current_sub_retention * plan.price
                            iap_events.append((next_day, payment))
                            
                            next_day += plan.duration_days
                            cycle += 1
            
            # Sort events by day and calculate cumulative IAP at milestones
            iap_events.sort(key=lambda x: x[0])
            cumulative_iap = 0
            event_idx = 0
            
            # Apply platform fee (Apple/Google commission)
            net_revenue_mult = 1 - cfg.subscription.platform_fee_rate
            
            for milestone in sorted(milestones):
                while event_idx < len(iap_events) and iap_events[event_idx][0] <= milestone:
                    cumulative_iap += iap_events[event_idx][1] * net_revenue_mult
                    event_idx += 1
                cumulative_at_milestone[milestone]['iap'] = cumulative_iap
            
            # Total IAP with platform fee deducted
            ltv_iap = sum(e[1] for e in iap_events) * net_revenue_mult
            
            # Build daily_breakdown from milestones
            daily_breakdown = []
            for m in sorted(milestones):
                if m <= days:
                    daily_breakdown.append({
                        'day': m,
                        'cumulative_iaa': cumulative_at_milestone[m]['iaa'],
                        'cumulative_iap': cumulative_at_milestone[m]['iap'],
                        'cumulative_total': cumulative_at_milestone[m]['iaa'] + cumulative_at_milestone[m]['iap']
                    })
            
            return {
                'ltv_iaa': ltv_iaa,
                'ltv_iap': ltv_iap,
                'ltv_total': ltv_iaa + ltv_iap,
                'blended_cpi': params.blended_cpi,
                'cpi_paid': params.cpi_paid,
                'daily_breakdown': daily_breakdown
            }
        
        else:
            # STOCHASTIC MODE: Use expected values with sampled parameters
            # This calculates expected LTV for a cohort, not simulating a single user
            
            exploitation_day = cfg.subscription.exploitation_start_day
            
            # IAA: Daily revenue with sampled parameters
            for day in range(days + 1):
                retention = self._get_retention_at_day(day, params.retention_mult)
                daily_iaa = retention * params.get_arpdau_at_day(day)
                ltv_iaa += daily_iaa
            
            # IAP: Expected value from each subscription plan (same logic as deterministic)
            iap_events = []
            
            for plan in cfg.subscription.get_all_plans():
                effective_pay_rate = plan.pay_rate * params.pay_rate_mult
                
                if plan.has_trial:
                    expected_subscribers = effective_pay_rate * plan.trial_to_paid_rate
                else:
                    expected_subscribers = effective_pay_rate
                
                # First payment
                first_day = exploitation_day + (plan.trial_days if plan.has_trial else 0)
                if first_day <= days:
                    current_sub_retention = 1.0
                    payment = expected_subscribers * current_sub_retention * plan.price
                    iap_events.append((first_day, payment))
                    
                    # Renewal payments with sampled renewal_mult
                    if plan.duration_days < 36500:
                        cycle = 1
                        next_day = first_day + plan.duration_days
                        
                        while next_day <= days and cycle <= 52:
                            step_renewal_rate = plan.get_renewal_rate(cycle) * params.renewal_mult
                            current_sub_retention *= step_renewal_rate
                            payment = expected_subscribers * current_sub_retention * plan.price
                            iap_events.append((next_day, payment))
                            
                            next_day += plan.duration_days
                            cycle += 1
            
            ltv_iap = sum(e[1] for e in iap_events)
            
            # Apply platform fee (Apple/Google commission)
            net_revenue_mult = 1 - cfg.subscription.platform_fee_rate
            ltv_iap *= net_revenue_mult
            
            # Build daily breakdown for curve plotting
            daily_breakdown = []
            cumulative_iaa = 0
            cumulative_iap = 0
            iap_events.sort(key=lambda x: x[0])
            event_idx = 0
            
            for day in range(days + 1):
                retention = self._get_retention_at_day(day, params.retention_mult)
                daily_iaa = retention * params.get_arpdau_at_day(day)
                cumulative_iaa += daily_iaa
                
                # Add IAP events for this day (with platform fee)
                daily_iap = 0
                while event_idx < len(iap_events) and iap_events[event_idx][0] == day:
                    daily_iap += iap_events[event_idx][1] * net_revenue_mult
                    event_idx += 1
                cumulative_iap += daily_iap
                
                daily_breakdown.append({
                    'day': day,
                    'retention': retention,
                    'arpdau': params.get_arpdau_at_day(day),
                    'daily_iaa': daily_iaa,
                    'daily_iap': daily_iap,
                    'cumulative_iaa': cumulative_iaa,
                    'cumulative_iap': cumulative_iap,
                    'cumulative_total': cumulative_iaa + cumulative_iap
                })
        
        return {
            'ltv_iaa': ltv_iaa,
            'ltv_iap': ltv_iap,
            'ltv_total': ltv_iaa + ltv_iap,
            'blended_cpi': params.blended_cpi,
            'cpi_paid': params.cpi_paid,
            'daily_breakdown': daily_breakdown
        }
    
    def run(self, days: int = None) -> Dict:
        """
        Run Monte Carlo simulation
        
        Args:
            days: Number of days to simulate (default: from config)
            
        Returns:
            Dictionary with simulation results and statistics
        """
        days = days or self.config.simulation_days
        self.results = []
        
        for i in range(self.n_simulations):
            params = self._sample_params()
            ltv_result = self._calculate_ltv(params, days)
            
            blended_cpi = ltv_result['blended_cpi']
            ltv_total = ltv_result['ltv_total']
            roas = ltv_total / blended_cpi if blended_cpi > 0 and blended_cpi != float('inf') else 0
            
            # Calculate ROAS at key milestones for curve plotting (granular for smooth curve)
            roas_curve = {}
            milestones = [0, 1, 3, 7, 14, 21, 30, 45, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 365]
            daily_breakdown = ltv_result.get('daily_breakdown', [])
            
            if blended_cpi > 0 and blended_cpi != float('inf'):
                # Create lookup for daily_breakdown by day
                breakdown_by_day = {}
                for entry in daily_breakdown:
                    day = entry.get('day', entry.get('day', -1))
                    if day >= 0:
                        breakdown_by_day[day] = entry.get('cumulative_total', 0)
                
                for milestone in milestones:
                    # Look for exact day match first
                    if milestone in breakdown_by_day:
                        cumulative_ltv = breakdown_by_day[milestone]
                    else:
                        # Find the closest day before milestone using binary search or scan using breakdown_by_day keys
                        # Since break_down keys are sorted days
                        available_days = sorted(breakdown_by_day.keys())
                        closest_day = -1
                        for d in available_days:
                            if d <= milestone:
                                closest_day = d
                            else:
                                break
                        
                        if closest_day != -1:
                            cumulative_ltv = breakdown_by_day[closest_day]
                        else:
                             # No data before milestone (e.g. D0 missing?)
                            cumulative_ltv = 0
                            
                    roas_curve[f'd{milestone}'] = cumulative_ltv / blended_cpi
            else:
                for milestone in milestones:
                    roas_curve[f'd{milestone}'] = 0
            
            self.results.append({
                'blended_cpi': blended_cpi,
                'cpi_paid': ltv_result['cpi_paid'],
                'ltv_total': ltv_total,
                'ltv_iaa': ltv_result['ltv_iaa'],
                'ltv_iap': ltv_result['ltv_iap'],
                'roas': roas,
                'roas_curve': roas_curve,
                'organic_ratio': params.organic_ratio,
                'ecpm_d0': params.ecpm_d0,
                'retention_mult': params.retention_mult,
                'profitable': roas >= 1.0
            })
        
        return self._calculate_statistics()
    
    def _calculate_statistics(self) -> Dict:
        """Calculate summary statistics from results"""
        if not self.results:
            return {}
        
        roas_values = np.array([r['roas'] for r in self.results])
        ltv_values = np.array([r['ltv_total'] for r in self.results])
        ltv_iaa_values = np.array([r['ltv_iaa'] for r in self.results])
        ltv_iap_values = np.array([r['ltv_iap'] for r in self.results])
        cpi_values = np.array([r['blended_cpi'] for r in self.results if r['blended_cpi'] != float('inf')])
        
        def calc_stats(arr):
            return {
                'mean': float(np.mean(arr)),
                'median': float(np.median(arr)),
                'std': float(np.std(arr)),
                'p5': float(np.percentile(arr, 5)),
                'p25': float(np.percentile(arr, 25)),
                'p50': float(np.percentile(arr, 50)),
                'p75': float(np.percentile(arr, 75)),
                'p95': float(np.percentile(arr, 95)),
                'min': float(np.min(arr)),
                'max': float(np.max(arr))
            }
        
        return {
            'n_simulations': self.n_simulations,
            'days': self.config.simulation_days,
            'roas': calc_stats(roas_values),
            'ltv_total': calc_stats(ltv_values),
            'ltv_iaa': calc_stats(ltv_iaa_values),
            'ltv_iap': calc_stats(ltv_iap_values),
            'cpi': calc_stats(cpi_values) if len(cpi_values) > 0 else {},
            'risk': {
                'probability_profitable': float(np.mean([1 if r >= 1.0 else 0 for r in roas_values])),
                'probability_roas_below_50pct': float(np.mean([1 if r < 0.5 else 0 for r in roas_values])),
                'value_at_risk_95': float(np.percentile(1 - roas_values, 95))
            }
        }
    
    def get_confidence_interval(self, metric: str = 'roas', confidence: float = 0.90) -> Tuple[float, float]:
        """Get confidence interval for a metric"""
        if not self.results:
            return (0, 0)
        
        values = np.array([r[metric] for r in self.results if r.get(metric, 0) != float('inf')])
        alpha = (1 - confidence) / 2
        
        return (
            float(np.percentile(values, alpha * 100)),
            float(np.percentile(values, (1 - alpha) * 100))
        )
    
    def get_ltv_curve(self, days: int = None) -> pd.DataFrame:
        """Get average LTV curve across all simulations"""
        days = days or self.config.simulation_days
        
        # Run one detailed simulation to get structure
        params = self._sample_params()
        result = self._calculate_ltv(params, days)
        
        return pd.DataFrame(result['daily_breakdown'])
    
    def get_results_df(self) -> pd.DataFrame:
        """Get simulation results as DataFrame"""
        return pd.DataFrame(self.results)


class TargetKPIGenerator:
    """
    Generate Target KPI thresholds: Safe, Expected, Breakthrough
    """
    
    def __init__(self, simulator: EnhancedMonteCarloSimulator = None):
        self.simulator = simulator or EnhancedMonteCarloSimulator()
    
    def generate_targets(self, days: int = None) -> Dict:
        """Generate KPI targets based on simulation"""
        if not self.simulator.results:
            self.simulator.run(days)
        
        stats = self.simulator._calculate_statistics()
        
        return {
            'roas': {
                'pessimistic': round(stats['roas']['p5'], 4),
                'safe': round(stats['roas']['p25'], 4),
                'expected': round(stats['roas']['p50'], 4),
                'breakthrough': round(stats['roas']['p75'], 4),
                'optimistic': round(stats['roas']['p95'], 4)
            },
            'ltv_total': {
                'pessimistic': round(stats['ltv_total']['p5'], 4),
                'expected': round(stats['ltv_total']['mean'], 4),
                'optimistic': round(stats['ltv_total']['p95'], 4)
            },
            'ltv_breakdown': {
                'iaa_mean': round(stats['ltv_iaa']['mean'], 4),
                'iap_mean': round(stats['ltv_iap']['mean'], 4),
                'iaa_ratio': round(stats['ltv_iaa']['mean'] / max(stats['ltv_total']['mean'], 0.001), 4)
            },
            'cpi': {
                'max_safe': round(stats['cpi']['p75'], 2) if stats.get('cpi') else 0,
                'expected': round(stats['cpi']['mean'], 2) if stats.get('cpi') else 0,
                'ideal': round(stats['cpi']['p25'], 2) if stats.get('cpi') else 0
            },
            'probability_profitable': round(stats['risk']['probability_profitable'], 4),
            'simulation_info': {
                'n_simulations': stats['n_simulations'],
                'days': stats['days']
            }
        }


# Backward compatibility - alias
MonteCarloSimulator = EnhancedMonteCarloSimulator


if __name__ == "__main__":
    print("=" * 60)
    print("ENHANCED MONTE CARLO SIMULATION")
    print("=" * 60)
    
    # Test with custom config
    simulator = EnhancedMonteCarloSimulator(n_simulations=500)
    results = simulator.run(365)
    
    print(f"\n📊 Simulation Results (n={results['n_simulations']}, {results['days']} days):")
    print(f"   ROAS Mean: {results['roas']['mean'] * 100:.1f}%")
    print(f"   ROAS Median: {results['roas']['median'] * 100:.1f}%")
    print(f"   Probability of Profit: {results['risk']['probability_profitable'] * 100:.1f}%")
    
    print(f"\n💰 LTV Breakdown:")
    print(f"   Total LTV: ${results['ltv_total']['mean']:.4f}")
    print(f"   IAA (Ads): ${results['ltv_iaa']['mean']:.4f}")
    print(f"   IAP (Subs): ${results['ltv_iap']['mean']:.4f}")
    
    ci = simulator.get_confidence_interval('roas', 0.90)
    print(f"\n📈 90% Confidence Interval: [{ci[0] * 100:.1f}%, {ci[1] * 100:.1f}%]")
    
    print("\n🎯 Target KPIs:")
    generator = TargetKPIGenerator(simulator)
    targets = generator.generate_targets()
    print(f"   Safe ROAS: {targets['roas']['safe'] * 100:.1f}%")
    print(f"   Expected ROAS: {targets['roas']['expected'] * 100:.1f}%")
    print(f"   Breakthrough ROAS: {targets['roas']['breakthrough'] * 100:.1f}%")
