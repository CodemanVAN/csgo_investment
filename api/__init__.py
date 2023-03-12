"""buff api"""
import requests
import json
import pickle
import os
import datetime


class Goods:
    def __init__(self, goods_id, cost=0, token=''):
        self.index = 0
        self.id = goods_id  # buff id
        self.youpin_id = 0

        self.name = ''  # name
        self.cost = cost  # 购入花费
        self.price = 0  # buff当前价格
        self.steam_price = 0  # steam当前价格

        self.rent_day = 0
        self.rent_return_date = datetime.datetime.today()
        self.rent_earn = 0
        self.status = 0  # 0:在库中 1:租出 2:卖出
        self.token = token  # youpin 登录token
        self.on_sale_count = 0  # youpin在售
        self.on_lease_count = 0  # youpin租出
        self.lease_unit_price = 0  # youpin短租金
        self.long_lease_unit_price = 0  # youpin长租金
        self.youpin_price = 0  # youpin当前价格
        self.deposit = 0  # 押金
        self.sell_price = 0  # 卖出价格
        self.__get_buff()
        self.__get_youpin()

    def __get_buff(self):
        url = (
            'https://buff.163.com/api/market/goods/sell_order?game=csgo&goods_id='
            + self.id
        )
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            self.price = eval(data['data']['items'][0]['price'])
            self.name = data['data']['goods_infos'][self.id]['name']
            self.steam_price = eval(
                data['data']['goods_infos'][self.id]['steam_price_cny']
            )
            return True
        else:
            return False

    def __get_youpin(self):
        url = "https://api.youpin898.com/api/homepage/es/template/GetCsGoPagedList"
        payload = json.dumps(
            {
                "listType": "30",
                "gameId": "730",
                "keyWords": self.name,
                "pageIndex": 1,
                "pageSize": 20,
                "sortType": "0",
                "listSortType": "2",
            }
        )
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "apptype": "1",
            "authorization": self.token,
            "content-type": "application/json",
            "sec-ch-ua": "\"Chromium\";v=\"110\", \"Not A(Brand\";v=\"24\", \"Microsoft Edge\";v=\"110\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "Referer": "https://www.youpin898.com/",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
        response = requests.request(
            "POST", url, headers=headers, data=payload).json()
        idx = 0
        

        self.youpin_price = float(response['Data'][idx]["Price"])  # youpin当前价格
        while self.youpin_price-self.price > self.youpin_price*10 and len(response['Data'])>1:
            idx+=1
            if idx >= len(response['Data'])-1:break
        self.youpin_price = float(response['Data'][idx]["Price"])  # youpin当前价格
        """
        print('--------------------------------')
        print(self.name,self.youpin_price, len(response['Data']))
        print('--------------------------------')
        """
        idx=min(idx,len(response['Data'])-1)
        self.youpin_id = response['Data'][idx]['Id']
        self.on_sale_count = response['Data'][idx]["OnSaleCount"]  # youpin在售
        self.on_lease_count = response['Data'][idx]["OnLeaseCount"]  # youpin租出
        self.lease_unit_price = eval(
            response['Data'][idx]["LeaseUnitPrice"])  # youpin短租金
        self.long_lease_unit_price = eval(
            response['Data'][idx]["LongLeaseUnitPrice"]
        )  # youpin长租金

        self.deposit = eval(response['Data'][idx]["LeaseDeposit"])  # 押金

    def refresh(self):
        self.__get_buff()
        self.__get_youpin()

    def sell(self, price):
        self.status = 2
        self.sell_price = price

    def lease(self, day,profit):
        self.rent_day += day
        self.rent_earn += profit
        self.rent_return_date = datetime.datetime.today()+datetime.timedelta(day)
        self.status = 1

    def back(self):
        self.rent_return_date = datetime.datetime.today()
        self.status = 0

    def get_status(self):
        if self.status == 0 and self.cost != 0:
            return "在库中"
        elif self.status == 1:
            return "租出"
        elif self.status == 0 and self.cost == 0:
            return "观望中"
        else:
            return "卖出"

    def __call__(self):
        if self.cost == 0:
            return {
                "BuffId": self.id,
                "YoupinId": self.youpin_id,
                "Name": self.name,
                "Cost": self.cost,
                "BuffPrice": self.price,
                "YoupinPrice": self.youpin_price,
                "SteamPrice": self.steam_price,
                "Status": self.status,
                "OnSaleCount": self.on_sale_count,
                "OnLeaseCount": self.on_lease_count,
                "LeaseUnitPrice": self.lease_unit_price,
                "LongLeaseUnitPrice": self.long_lease_unit_price,
                "Deposit": self.deposit,
                "RentSaleRatio": self.on_lease_count / self.on_sale_count,  # 目前租售比
                "LeaseRatio": self.lease_unit_price / self.price * 100,  # 租金比例
                "DepositRatio": self.deposit / self.price * 100,  # 押金比例
                "AnnualizedShortTermLeaseRatio": 192
                * self.lease_unit_price
                / self.price
                * 100,  # 年化短租比例
                "AnnualizedLongTermLeaseRatio": 264
                * self.long_lease_unit_price
                / self.price
                * 100,  # 年化长租比例
                "CashRatio": self.price / self.steam_price * 100,  # 套现比例
            }
        else:
            return {
                "BuffId": self.id,
                "YoupinId": self.youpin_id,
                "Name": self.name,
                "Cost": self.cost,
                "BuffPrice": self.price,
                "YoupinPrice": self.youpin_price,
                "SteamPrice": self.steam_price,
                "Status": self.status,
                "OnSaleCount": self.on_sale_count,
                "OnLeaseCount": self.on_lease_count,
                "LeaseUnitPrice": self.lease_unit_price,
                "LongLeaseUnitPrice": self.long_lease_unit_price,
                "Deposit": self.deposit,
                "RentSaleRatio": self.on_lease_count / self.on_sale_count,  # 目前租售比
                "TheoreticalCurrentEarnings": self.price-self.cost+self.rent_earn,  # 理论目前收益
                "TheoreticalCurrentEarningsRate": (self.price - self.cost + self.rent_earn)
                / self.cost
                * 100,  # 理论目前收益率
                "LeaseRatio": self.lease_unit_price / self.price * 100,  # 租金比例
                "DepositRatio": self.deposit / self.price * 100,  # 押金比例
                "AnnualizedShortTermLeaseRatio": 192
                * self.lease_unit_price
                / self.price
                * 100,  # 年化短租比例
                "AnnualizedLongTermLeaseRatio": 264
                * self.long_lease_unit_price
                / self.price
                * 100,  # 年化长租比例
                "CashRatio": self.price / self.steam_price * 100,  # 套现比例
                "Rentearn": self.rent_earn,  # 总出租收益
                "TotalRentDay": self.rent_day,  # 总出租天数
                "ReturnDay": self.rent_return_date,  # 归还日期
            }


class Inventory:
    """库存管理"""

    def __init__(self, path) -> None:
        """选择一个库存并启动该库存"""
        self.path = path
        if os.path.exists(path):
            self.__data = pickle.load(open(path, "rb"))
        else:
            self.__data = {}

    def __call__(self):
        return self.__data

    def __iter__(self):
        return self.__data.__iter__()

    def add(self, good: Goods):
        if good.__class__ == Goods:
            good.index = len(self())
            self.__data[good.index] = good
        else:
            raise TypeError("输入类型错误")

    def delete(self, good):
        del self()[good]

    def save(self):
        pickle.dump(self.__data, open(self.path, "wb"))

    def reset(self):
        self.__data = []

    def total_cost(self):
        return sum([self()[good].cost for good in self()])

    def total_cost_in_inventory(self):
        return sum(
            [
                self()[good].cost
                for good in self()
                if (self()[good].status == 0 and self()[good].cost != 0)
                or self()[good].status == 1
            ]
        )

    def calc_rent_earn(self):
        return sum(
            [
                self()[good].rent_earn
                for good in self()
            ]
        )
    def cala_sell_earn(self):
        return sum([
                self()[good].sell_price - self()[good].cost
                for good in self()
                if (self()[good].cost != 0 and self()[good].status == 2)
            ])
    def calc_buff_earn(self):
        return sum(
            [
                self()[good].price - self()[good].cost
                for good in self()
                if (self()[good].cost != 0 & self()[good].status == 0) or self()[good].status == 1
            ]
        )+self.cala_sell_earn()

    def calc_youpin_earn(self):
        return sum(
            [
                self()[good].youpin_price - self()[good].cost
                for good in self()
                if (self()[good].cost != 0 & self()[good].status == 0) or self()[good].status == 1
            ]
        )+self.cala_sell_earn()

    def calc_buff_earn_rate(self):
        return self.calc_buff_earn() / self.total_cost_in_inventory() * 100

    def calc_youpin_earn_rate(self):
        return self.calc_youpin_earn() / self.total_cost_in_inventory() * 100

    def calc_price(self):
        return sum(
            [
                self()[good].price
                for good in self()
                if (self()[good].status == 0 and self()[good].cost != 0)
                or self()[good].status == 1
            ]
        )

    def calc_yyyp_price(self):
        return sum(
            [
                self()[good].youpin_price
                for good in self()
                if (self()[good].status == 0 and self()[good].cost != 0)
                or self()[good].status == 1
            ]
        )

    def sell_earn(self):
        return sum(
            [self()[good].sell_price+self()[good].rent_earn for good in self() if self()[good].status == 2]
        ) - sum(
            [self()[good].cost for good in self() if self()[good].status == 2]
        )

    def sell_price(self):
        return sum(
            [self()[good].sell_price+self()[good].rent_earn for good in self() if self()[good].status == 2]
        )


def test_tokens(token):
    try:
        tmp = Goods('33912', '1188', token)
        return True
    except:
        return False
