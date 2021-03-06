from yahoofinancials import YahooFinancials
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import numpy as np
import scipy.optimize as sco

def prices(ticker, start, end):
    print("...")
    def definir_acoes(tickers, start, end):
        df_tickers = []
        df_df = pd.DataFrame()
        def retrieve_stock_data(ticker, start, end):
            json = YahooFinancials([ticker]).get_historical_price_data(start, end, "daily")
            df = pd.DataFrame(columns=["open", "close", "adjclose", "volume"])
            for row in json[ticker]["prices"]:
                date = datetime.date.fromisoformat(row["formatted_date"])
                df.loc[date] = [row["open"], row["close"], row["adjclose"], row["volume"]]
            df.index.name = "Date"
            print("Ação " + ticker + " enviado ao dataframe - " + str(datetime.datetime.now().strftime('%M:%S.%f')[:-4]))
            return df
        for a in tickers:
            try:
                df_tickers.append(retrieve_stock_data(a, start, end))
            except:
                print("Erro em inserir a ação: " + a)
                continue
        for b in range(len(df_tickers)):
            df_df[tickers[b]] = df_tickers[b]["adjclose"]
        return df_df
    df = definir_acoes(ticker, start, end)
    df = df[~df.index.duplicated()]

    return df


def portfolio_annualised_performance(weights, mean_returns, cov_matrix):
    returns = np.sum(mean_returns * weights) * 252
    std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
    return std, returns


def random_portfolios(num_portfolios, mean_returns, cov_matrix, risk_free_rate):
    results = np.zeros((3, num_portfolios))
    weights_record = []
    for i in range(num_portfolios):
        weights = np.random.random(len(mean_returns))
        weights /= np.sum(weights)
        weights_record.append(weights)
        portfolio_std_dev, portfolio_return = portfolio_annualised_performance(weights, mean_returns, cov_matrix)
        results[0, i] = portfolio_std_dev
        results[1, i] = portfolio_return
        results[2, i] = (portfolio_return - risk_free_rate) / portfolio_std_dev
    return results, weights_record

def neg_sharpe_ratio(weights, mean_returns, cov_matrix, risk_free_rate):
    p_var, p_ret = portfolio_annualised_performance(weights, mean_returns, cov_matrix)
    return -(p_ret - risk_free_rate) / p_var

def max_sharpe_ratio(mean_returns, cov_matrix, risk_free_rate):
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix, risk_free_rate)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bound = (0.0,1.0)
    bounds = tuple(bound for asset in range(num_assets))
    result = sco.minimize(neg_sharpe_ratio, num_assets*[1./num_assets,], args=args,
                        method='SLSQP', bounds=bounds, constraints=constraints)
    return result

def portfolio_volatility(weights, mean_returns, cov_matrix):
    return portfolio_annualised_performance(weights, mean_returns, cov_matrix)[0]

def min_variance(mean_returns, cov_matrix):
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bound = (0.0,1.0)
    bounds = tuple(bound for asset in range(num_assets))

    result = sco.minimize(portfolio_volatility, num_assets*[1./num_assets,], args=args,
                        method='SLSQP', bounds=bounds, constraints=constraints)

    return result

def efficient_return(mean_returns, cov_matrix, target):
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix)

    def portfolio_return(weights):
        return portfolio_annualised_performance(weights, mean_returns, cov_matrix)[1]

    constraints = ({'type': 'eq', 'fun': lambda x: portfolio_return(x) - target},
                   {'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0,1) for asset in range(num_assets))
    result = sco.minimize(portfolio_volatility, num_assets*[1./num_assets,], args=args, method='SLSQP', bounds=bounds, constraints=constraints)
    return result


def efficient_frontier(mean_returns, cov_matrix, returns_range):
    efficients = []
    for ret in returns_range:
        efficients.append(efficient_return(mean_returns, cov_matrix, ret))
    return efficients


def display_calculated_ef_with_random(mean_returns, cov_matrix, num_portfolios, risk_free_rate, retornos_finais):
    results, _ = random_portfolios(num_portfolios, mean_returns, cov_matrix, risk_free_rate)

    max_sharpe = max_sharpe_ratio(mean_returns, cov_matrix, risk_free_rate)
    sdp, rp = portfolio_annualised_performance(max_sharpe['x'], mean_returns, cov_matrix)
    max_sharpe_allocation = pd.DataFrame(max_sharpe.x, index=table.columns, columns=['allocation'])
    max_sharpe_allocation.allocation = [round(i * 100, 2) for i in max_sharpe_allocation.allocation]
    max_sharpe_allocation = max_sharpe_allocation.T
    max_sharpe_allocation

    min_vol = min_variance(mean_returns, cov_matrix)
    sdp_min, rp_min = portfolio_annualised_performance(min_vol['x'], mean_returns, cov_matrix)
    min_vol_allocation = pd.DataFrame(min_vol.x, index=table.columns, columns=['allocation'])
    min_vol_allocation.allocation = [round(i * 100, 2) for i in min_vol_allocation.allocation]
    min_vol_allocation = min_vol_allocation.T

    print("-" * 80)
    print("Maximum Sharpe Ratio Portfolio Allocation\n")
    print("Annualised Return:", round(rp, 2))
    print("Annualised Volatility:", round(sdp, 2))
    print(max_sharpe_allocation)
    max_sharpe_allocation.to_csv("sharpe_allocation.csv")
    print("-" * 80)
    print("Minimum Volatility Portfolio Allocation\n")
    print("Annualised Return:", round(rp_min, 2))
    print("Annualised Volatility:", round(sdp_min, 2))
    print(min_vol_allocation)
    min_vol_allocation.to_csv("min_vol_allocation.csv")



    plt.figure(figsize=(10, 7))
    plt.scatter(results[0, :], results[1, :], c=results[2, :], cmap='YlGnBu', marker='o', s=10, alpha=0.3)
    plt.colorbar()
    plt.scatter(sdp, rp, marker='*', color='r', s=500, label='Maximum Sharpe ratio')
    plt.scatter(sdp_min, rp_min, marker='*', color='g', s=500, label='Minimum volatility')

    target = np.linspace(rp_min, 0.32, 50)
    efficient_portfolios = efficient_frontier(mean_returns, cov_matrix, target)
    plt.plot([p['fun'] for p in efficient_portfolios], target, linestyle='-.', color='black',
             label='efficient frontier')
    plt.title('Calculated Portfolio Optimization based on Efficient Frontier')
    plt.xlabel('annualised volatility')
    plt.ylabel('annualised returns')
    plt.legend(labelspacing=0.8)
    plt.show()




tickers = ["MGLU3.SA", "ITUB4.SA", "BBDC3.SA", "BBDC4.SA", "JBSS3.SA", "ITUB3.SA"]
# tickers = ["ABEV3.SA", "ALPA4.SA", "ALSO3.SA", "AMAR3.SA", "AZUL4.SA", "B3SA3.SA", "BBAS3.SA", "BBDC3.SA", "BBDC4.SA", "BBSE3.SA", "BEEF3.SA", "BIDI4.SA", "BPAC11.SA", "BPAN4.SA", "BRAP4.SA", "BRDT3.SA", "BRFS3.SA", "BRKM5.SA", "BRML3.SA", "BTOW3.SA", "CCRO3.SA", "CESP6.SA", "CIEL3.SA", "CMIG4.SA", "CNTO3.SA", "COGN3.SA", "CPFE3.SA", "CPLE6.SA", "CRFB3.SA", "CSAN3.SA", "CSMG3.SA", "CSNA3.SA", "CVCB3.SA", "CYRE3.SA", "DTEX3.SA", "ECOR3.SA", "EGIE3.SA", "ELET3.SA", "ELET6.SA", "EMBR3.SA", "ENBR3.SA", "ENEV3.SA", "ENGI11.SA", "EQTL3.SA", "EZTC3.SA", "FLRY3.SA", "GGBR4.SA", "GNDI3.SA", "GOAU4.SA", "GOLL4.SA", "HAPV3.SA", "HGTX3.SA", "HYPE3.SA", "IGTA3.SA", "IRBR3.SA", "ITSA4.SA", "ITUB4.SA", "JBSS3.SA", "JHSF3.SA", "KLBN11.SA", "LAME3.SA", "LAME4.SA", "LCAM3.SA", "LIGT3.SA", "LINX3.SA", "LREN3.SA", "MDIA3.SA", "MGLU3.SA", "MOVI3.SA", "MRFG3.SA", "MRVE3.SA", "MULT3.SA", "NEOE3.SA", "NTCO3.SA", "PCAR3.SA", "PETR3.SA", "PETR4.SA", "PRIO3.SA", "PSSA3.SA", "QUAL3.SA", "RADL3.SA", "RAIL3.SA", "RAPT4.SA", "RENT3.SA", "SANB11.SA", "SAPR11.SA", "SBSP3.SA", "SULA11.SA", "SUZB3.SA", "TAEE11.SA", "TIMS3.SA", "TOTS3.SA", "TRPL4.SA", "UGPA3.SA", "USIM5.SA", "VALE3.SA", "VIVT3.SA", "VVAR3.SA", "WEGE3.SA", "YDUQ3.SA"]

start = "2015-01-01"
end = "2020-12-31"

feedback = []

df = prices(tickers, start, end)
# df_log_ret = np.log(df/df.shift(-1))

retornos_finais = df.loc[datetime.date(year=2017,month=1,day=1):datetime.date(year=2020,month=12,day=31)].pct_change()

returns = df.loc[datetime.date(year=2015,month=1,day=1):datetime.date(year=2016,month=12,day=31)].pct_change()

table = df
mean_returns = returns.mean()
cov_matrix = returns.cov()
num_portfolios = 50000
risk_free_rate = 0.02

display_calculated_ef_with_random(mean_returns, cov_matrix, num_portfolios, risk_free_rate, retornos_finais)