from strategies.smc_strategy import run_smc_strategy

if __name__ == "__main__":
    run_smc_strategy(symbol="ETHUSDT", capital=1000, risk_pct=0.01)
