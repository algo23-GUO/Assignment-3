# Assignment-3

需要读取NH_index.xlsx（南华商品各期货品种收益率指数）、NHC_index.xlsx（南华商品指数）、factor_df.csv、adjust_domin_return_df.csv（主力合约调整后收盘价）、adjust_second_domin_return_df.csv（次主力合约调整后收盘价）

主要有四个功能：

1.对商品进行筛选，将活跃度较低的品种的因子值赋空值，避免影响之后的因子排序

2.对因子值进行处理，生成交易信号

3.根据不同需求生成历史策略净值

4.对历史策略净值进行回测

回测结果：
![image](https://github.com/algo23-GUO/Assignment-3/assets/128219105/da442c7a-517e-40e1-aaaa-60b4efa714de)
