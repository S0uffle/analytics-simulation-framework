from config import CONFIG
from modules.simulation import EnhancedMonteCarloSimulator
import json
import os

def main():
    if os.path.exists('sim_config.json'):
        with open('sim_config.json', 'r') as f:
            j = json.load(f)
            if not j.get('enable_weekly', True):
                CONFIG.subscription.weekly.pay_rate = 0
            if not j.get('enable_monthly', True):
                CONFIG.subscription.monthly.pay_rate = 0
            if not j.get('enable_yearly', False):
                CONFIG.subscription.yearly.pay_rate = 0
            if not j.get('enable_lifetime', False):
                CONFIG.subscription.lifetime.pay_rate = 0

    simulator = EnhancedMonteCarloSimulator(config=CONFIG, n_simulations=500)
    results = simulator.run()
    
    # Print the key metrics to output
    print(json.dumps({
        'mean_roas': results['roas']['mean'],
        'median_roas': results['roas']['median'],
        'prob_profit': results['risk']['probability_profitable'],
        'ltv_total': results['ltv_total']['mean'],
        'ltv_iaa': results['ltv_iaa']['mean'],
        'ltv_iap': results['ltv_iap']['mean'],
        'cpi': results['cpi']['mean']
    }, indent=2))

if __name__ == '__main__':
    main()
