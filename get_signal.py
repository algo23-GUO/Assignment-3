import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from backtest import Multi_Asset_backtest,Single_Asset_backtest


plt.rcParams["font.sans-serif"] = ["SimHei"]


class Signal:
    def __init__(self) -> None:
        self.roll_return_factor = pd.read_csv(r"./factor/roll_return_factor.csv", index_col=0)
        self.liquidity_factor = pd.read_csv(r"./factor/liquidity_factor.csv", index_col=0)
        self.volatility_factor = pd.read_csv(r"./factor/volatility_factor.csv", index_col=0)
        self.ssectional_momentum_factor = pd.read_csv(r"./factor/ssectional_momentum_factor.csv", index_col=0)
        self.lsectional_momentum_factor = pd.read_csv(r"./factor/lsectional_momentum_factor.csv", index_col=0)
        self.stiming_momentum_factor = pd.read_csv(r"./factor/stiming_momentum_factor.csv", index_col=0)
        self.ltiming_momentum_factor = pd.read_csv(r"./factor/ltiming_momentum_factor.csv", index_col=0)
        self.warrant_factor = pd.read_csv(r"./factor/warrant_factor.csv", index_col=0)
        self.basis_factor = pd.read_csv(r"./factor/basis_factor.csv", index_col=0)
        self.inventory_factor = pd.read_csv(r"./factor/inventory_factor.csv", index_col=0)
        self.basis_sw_factor = pd.read_csv(r"./factor/basis_sw_factor.csv", index_col=0)
        self.adjust_domin_return_df = pd.read_csv(r"./nav/adjust_domin_return_df.csv", index_col=0).pct_change().shift(
            -1)
        self.adjust_second_domin_return_df = pd.read_csv(r"./nav/adjust_second_domin_return_df.csv",
                                                         index_col=0).pct_change().shift(-1)
        self.volume_df = pd.read_csv(r"./index/volume.csv", index_col=0)
        self.turnover_df = pd.read_csv(r"./index/turnover.csv", index_col=0)
        self.factor_list = [self.roll_return_factor, self.liquidity_factor, self.volatility_factor,
                            self.ssectional_momentum_factor,
                            self.lsectional_momentum_factor, self.stiming_momentum_factor, self.ltiming_momentum_factor,
                            self.warrant_factor, self.basis_factor, self.inventory_factor, self.basis_sw_factor]

    def get_filter(self):
        volume_filter = self.volume_df.mask(self.volume_df > 10000, 1)
        turnover_filter = self.turnover_df.mask(self.turnover_df > 1000000000, 1)
        filter = volume_filter + turnover_filter
        filter = filter.mask(filter == 2, 1)
        self.filter = filter.mask(filter != 1, np.nan)

    def filtering(self, df):
        filter = self.filter[list(df.columns)]
        return filter * df

    # 因子值大做多小做空，适用于截面动量、期限结构、波动率
    def get_quantile_signal(self, factor, _type="Large"):
        """_summary_

        Parameters
        ----------
        factor : _type_:dataframe
            _description_:修正后的因子值

        Returns
        -------
        _type_:dataframe
            _description_:适用于截面动量、期限结构、波动率
        """
        signal_df = {}
        if _type == "Large":
            signal = 1
        else:
            signal = -1
        for i in factor.index:
            sort_series = factor.loc[i]
            positive_series = sort_series.mask(sort_series > sort_series.quantile(0.8), signal)
            positive_series = positive_series.mask(positive_series != signal, 0)
            negetive_series = sort_series.mask(sort_series < sort_series.quantile(0.2), -signal)
            negetive_series = negetive_series.mask(negetive_series != -signal, 0)
            _series = positive_series + negetive_series
            signal_df[i] = _series
        return pd.DataFrame(signal_df).T

    def get_pn_signal(self, factor):
        """_summary_

        Parameters
        ----------
        factor : _type_:dataframe
            _description_:修正后的因子值

        Returns
        -------
        _type_:dataframe
            _description_:适用于时序动量
        """
        signal_df = factor.mask(factor > 0, 1)
        signal_df = signal_df.mask(signal_df < 0, -1)
        return signal_df

    def get_liquidity_signal(self, factor):
        """_summary_

        Parameters
        ----------
        factor : _type_:dataframe
            _description_:修正后的因子值

        Returns
        -------
        _type_:dataframe
            _description_:适用于流动性
        """
        signal_df = {}
        for i in factor.index:
            sort_series = factor.loc[i]
            _series = sort_series.mask(sort_series > sort_series.quantile(0.7), 1)
            _series = _series.mask(_series != 1, 0)
            signal_df[i] = _series
        return pd.DataFrame(signal_df).T

    def generate_nav(self, singal_df, _type="Not Roll"):
        """_summary_
        生成净值(默认不包括展期收益率策略)
        Parameters
        ----------
        singal_df : _type_:dataframe
            _description_
        _type : str, optional
            _description_, by default "Not Roll"

        Returns
        -------
        _type_:dataframe
            _description_:拟合净值
        """
        if _type == "Not Roll":
            ret = self.adjust_domin_return_df
        else:
            ret = self.adjust_second_domin_return_df
        ret = ret[list(singal_df.columns)]
        nav = ((singal_df * ret).mean(axis=1)+1).cumprod().dropna()
        return nav

    def get_return_sum(self, singal_df,_type="Not Roll"):
        if _type == "Not Roll":
            ret = self.adjust_domin_return_df
        else:
            ret = self.adjust_second_domin_return_df
        ret = ret[list(singal_df.columns)]
        nav = ((singal_df * ret).sum(axis=1)).cumsum().dropna()
        return nav


if __name__ == "__main__":
    #_start_date = "2017-12-01"
    #_end_date = "2022-12-31"
    print("start")
    signal = Signal()
    signal.get_filter()

    def _fliter(df, type1, type2, _type="Not Roll"):
        factor = signal.filtering(df)
        if type1 == "quantile":
            _signal = signal.get_quantile_signal(factor)
        elif type1 == "pn":
            _signal = signal.get_pn_signal(factor)
        elif type1 == "liquidity":
            _signal = signal.get_liquidity_signal(factor)
        if type2 == "power":
            nav = signal.generate_nav(_signal, _type)
        else:
            nav = signal.get_return_sum(_signal, _type)
        return nav

    roll_return_nav = _fliter(signal.roll_return_factor, "quantile", "power", _type="Roll")
    roll_return_nav_sum = _fliter(signal.roll_return_factor, "quantile", "sum", _type="Roll")
    ssectional_momentum_nav = _fliter(signal.ssectional_momentum_factor, "quantile", "power")
    ssectional_momentum_nav_sum = _fliter(signal.ssectional_momentum_factor, "quantile", "sum")
    lsectional_momentum_nav = _fliter(signal.lsectional_momentum_factor, "quantile", "power")
    lsectional_momentum_nav_sum = _fliter(signal.lsectional_momentum_factor, "quantile", "sum")
    basis_sw_nav = _fliter(signal.basis_sw_factor, "quantile", "power")
    basis_sw_nav_sum = _fliter(signal.basis_sw_factor, "quantile", "sum")
    basis_nav = _fliter(signal.basis_factor, "quantile", "power")
    basis_nav_sum = _fliter(signal.basis_factor, "quantile", "sum")
    stiming_momentum_nav = _fliter(signal.stiming_momentum_factor, "pn", "power")
    stiming_momentum_nav_sum = _fliter(signal.stiming_momentum_factor, "pn", "sum")
    ltiming_momentum_nav = _fliter(signal.ltiming_momentum_factor, "pn", "power")
    ltiming_momentum_nav_sum = _fliter(signal.ltiming_momentum_factor, "pn", "sum")
    liquidity_nav = _fliter(signal.liquidity_factor, "liquidity", "power")
    liquidity_nav_sum = _fliter(signal.liquidity_factor, "liquidity", "sum")

    warrant_factor = signal.filtering(signal.warrant_factor)
    warrant_signal = signal.get_quantile_signal(warrant_factor, _type="Small")
    warrant_nav = signal.generate_nav(warrant_signal)
    warrant_nav_sum = signal.get_return_sum(warrant_signal)
    inventory_factor = signal.filtering(signal.inventory_factor)
    inventory_signal = signal.get_quantile_signal(inventory_factor, _type="Small")
    inventory_nav = signal.generate_nav(inventory_signal)
    inventory_nav_sum = signal.get_return_sum(inventory_signal)

    print("end")
    nav_df = pd.concat(
        [roll_return_nav_sum, ssectional_momentum_nav_sum, lsectional_momentum_nav_sum, liquidity_nav_sum,
         ltiming_momentum_nav_sum, stiming_momentum_nav_sum, warrant_nav_sum, basis_nav_sum, basis_sw_nav_sum,
         inventory_nav_sum], axis=1)
    nav_df.columns = ["展期", "短截面", "长截面", "流动性", "长时序", "短时序", "仓单", "基差", "基差动量", "库存"]
    nav_df.plot()
    plt.show()
    NHC_index = pd.read_excel(r"./index/NHC_index.xlsx", index_col=0, header=0)
    NHC_index = NHC_index["close"]
    NHC_index = NHC_index.loc[roll_return_nav.index[0]:roll_return_nav.index[-1]]
    mab = Multi_Asset_backtest(NHC_index,
                               asset_nav_list=[roll_return_nav, ssectional_momentum_nav, lsectional_momentum_nav,
                                               liquidity_nav, ltiming_momentum_nav, stiming_momentum_nav,
                                               warrant_nav, basis_nav, basis_sw_nav, inventory_nav])
    result = mab.multi_backtest()
    result.columns = ["展期", "短截面", "长截面", "流动性", "长时序", "短时序", "仓单", "基差", "基差动量", "库存"]
    print(result)
