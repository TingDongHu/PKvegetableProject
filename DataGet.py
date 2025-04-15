import json
from datetime import datetime
from pymongo import MongoClient
from collections import defaultdict
import plotly.graph_objects as go
import random
from datetime import timedelta




class DataGet:
    def __init__(self):
        # 连接到MongoDB
        self.client = MongoClient('mongodb://DBadmin:DBpwd@127.0.0.1:27017/admin')
        self.db = self.client['xinfadi']
        self.collection = self.db['prices']
        self.samples=self.get_random_samples()
        self.origin_stats=self.get_origin_stats()
        self.pricetend=self.get_price_trend()
        self.categroy=self.get_category_stats()

    def get_random_samples(self, n=40):
        """获取随机样本数据"""
        data = list(self.collection.find({}, {'_id': 0}))
        return random.sample(data, min(n, len(data))) if data else []

    def get_origin_stats(self):
        """统计产地数据并转换为全称"""
        # 省份简称到全称的映射表
        PROVINCE_MAP = {
            '京': '北京', '津': '天津', '冀': '河北', '晋': '山西', '蒙': '内蒙古',
            '辽': '辽宁', '吉': '吉林', '黑': '黑龙江', '沪': '上海', '苏': '江苏',
            '浙': '浙江', '皖': '安徽', '闽': '福建', '赣': '江西', '鲁': '山东',
            '豫': '河南', '鄂': '湖北', '湘': '湖南', '粤': '广东', '桂': '广西',
            '琼': '海南', '川': '四川', '贵': '贵州', '云': '云南', '渝': '重庆',
            '藏': '西藏', '陕': '陕西', '甘': '甘肃', '青': '青海', '宁': '宁夏',
            '新': '新疆', '港': '香港', '澳': '澳门', '台': '台湾',

        }

        pipeline = [
            {"$match": {
                "产地": {"$exists": True, "$ne": None, "$nin": ["无", "None", "null"]}
            }},
            {"$project": {"产地": 1}},
        ]

        raw_data = list(self.collection.aggregate(pipeline))
        origin_counter = defaultdict(int)

        for item in raw_data:
            origin = item["产地"].strip()

            # 特殊处理"国产"
            if origin == "国产":
                origin_counter["国产"] += 1
                continue
            if origin == "越南":
                origin_counter["越南"] += 1
                continue
            if origin == "泰国":
                origin_counter["泰国"] += 1
                continue
            if origin == "美国":
                origin_counter["美国"] += 1
                continue
            if origin == "南非":
                origin_counter["南非"] += 1
                continue
            if origin == "秘鲁":
                origin_counter["秘鲁"] += 1
                continue
            if origin == "新西兰":
                origin_counter["新西兰"] += 1
                continue
            if origin == "菲律宾":
                origin_counter["菲律宾"] += 1
                continue
            if origin == "荷兰":
                origin_counter["荷兰"] += 1
                continue
            if origin == "智利":
                origin_counter["智利"] += 1
                continue
            if origin == "埃及":
                origin_counter["埃及"] += 1
                continue
            if origin == "比利时":
                origin_counter["比利时"] += 1
                continue
            if origin == "澳洲":
                origin_counter["澳洲"] += 1
                continue
            if origin == "印尼":
                origin_counter["印度尼西亚"] += 1
                continue

            # 处理组合产地
            if len(origin) > 1 and all('\u4e00' <= char <= '\u9fff' for char in origin):
                for char in origin:
                    full_name = PROVINCE_MAP.get(char, char)
                    origin_counter[full_name] += 1
            else:
                full_name = PROVINCE_MAP.get(origin, origin)
                origin_counter[full_name] += 1

        # 排序并取前20
        sorted_origins = sorted(origin_counter.items(), key=lambda x: x[1], reverse=True)[:60]

        return {
            'origins': [x[0] for x in sorted_origins],
            'counts': [x[1] for x in sorted_origins],
            'total': sum(x[1] for x in sorted_origins)
        }

    def get_price_trend(self):
        """获取90天价格趋势数据（每天计算商品的平均最高价、平均最低价和平均价格）"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        pipeline = [
            # 1. 筛选最近90天的数据
            {"$match": {
                "发布日期": {
                    "$gte": start_date,
                    "$lte": end_date
                },
                "平均价": {"$gt": 0}  # 排除价格为0的异常数据
            }},
            # 2. 按商品分组，计算每个商品的日均价、最低价和最高价
            {"$group": {
                "_id": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$发布日期"}},
                    "product": "$品名"  # 假设有"品名"字段，根据实际字段名调整
                },
                "daily_avg_price": {"$avg": "$平均价"},
                "daily_min_price": {"$min": "$平均价"},
                "daily_max_price": {"$max": "$平均价"}
            }},
            # 3. 按日期分组，计算所有商品的平均值
            {"$group": {
                "_id": "$_id.date",
                "avg_price": {"$avg": "$daily_avg_price"},  # 所有商品日均价的平均
                "min_price": {"$avg": "$daily_min_price"},  # 所有商品最低价的平均
                "max_price": {"$avg": "$daily_max_price"},  # 所有商品最高价的平均
                "product_count": {"$sum": 1}  # 当天商品种类数
            }},
            # 4. 按日期排序
            {"$sort": {"_id": 1}},
            # 5. 确保数据完整性（至少包含一定数量的商品）
            {"$match": {"product_count": {"$gt": 5}}}  # 排除商品种类太少的天数
        ]

        try:
            results = list(self.collection.aggregate(pipeline))
            print(f"获取到{len(results)}天的有效数据")  # 调试输出

            # 处理结果
            dates = []
            avg_prices = []
            min_prices = []
            max_prices = []

            for item in results:
                dates.append(item["_id"])
                avg_prices.append(round(item["avg_price"], 2))
                min_prices.append(round(item["min_price"], 2))
                max_prices.append(round(item["max_price"], 2))

            return {
                'dates': dates,
                'avg_prices': avg_prices,
                'min_prices': min_prices,
                'max_prices': max_prices,
                'data_range': f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
                'total_days': len(dates)
            }
        except Exception as e:
            print(f"获取价格趋势数据失败: {str(e)}")
            return {
                'dates': [],
                'avg_prices': [],
                'min_prices': [],
                'max_prices': [],
                'data_range': '',
                'total_days': 0
            }

    def get_category_stats(self):
        """获取分类统计数据"""
        pipeline = [
            {"$match": {
                "一级分类": {"$exists": True, "$ne": None},
                "二级分类": {"$exists": True, "$ne": None, "$ne": "无"}  # 添加对"无"的过滤
            }},
            {"$group": {
                "_id": {"l1": "$一级分类", "l2": "$二级分类"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 50}
        ]
        results = list(self.collection.aggregate(pipeline))

        # 组织为层级结构
        categories = defaultdict(list)
        for item in results:
            l1 = item['_id']['l1']
            l2 = item['_id']['l2']
            if l2 != "无":  # 再次确保过滤
                categories[l1].append({'name': l2, 'value': item['count']})

        return {
            'categories': dict(categories),
            'top_l1': sorted(
                [k for k in categories.keys() if k != "无"],  # 过滤掉一级分类中的"无"
                key=lambda x: sum(y['value'] for y in categories[x]),
                reverse=True
            )[:5]  # 只取前5个一级分类
        }



if __name__ == "__main__":
    # 初始化数据获取对象
    data = DataGet()

    print("=" * 50)
    print("新发地农产品数据统计分析结果")
    print("=" * 50)

    # 1. 打印随机样本数据
    print("\n🔹 随机样本数据（15条）：")
    for i, sample in enumerate(data.samples, 1):
        print(f"{i}. {sample.get('品名', 'N/A')} - "
              f"均价: {sample.get('平均价', 'N/A')}元 "
              f"产地: {sample.get('产地', 'N/A')}")

    # 2. 打印产地统计结果
    print("\n🔹 热门产地TOP20：")
    print(f"总记录数: {data.origin_stats['total']}")
    for origin, count in zip(data.origin_stats['origins'], data.origin_stats['counts']):
        print(f"{origin}: {count}次 ({count / data.origin_stats['total']:.1%})")

    # 3. 打印价格趋势
    print("\n🔹 价格趋势分析：")
    print(f"数据范围: {data.pricetend['data_range']}")
    print(f"有效天数: {data.pricetend['total_days']}")

    # 打印价格摘要
    if data.pricetend['avg_prices']:
        avg_price = sum(data.pricetend['avg_prices']) / len(data.pricetend['avg_prices'])
        min_price = min(data.pricetend['min_prices'])
        max_price = max(data.pricetend['max_prices'])
        print(f"均价范围: {min_price:.2f}~{max_price:.2f} 元 (平均 {avg_price:.2f} 元)")

        # 打印最近5天的价格
        print("\n最近5天价格：")
        for date, price in zip(data.pricetend['dates'][-5:], data.pricetend['avg_prices'][-5:]):
            print(f"{date}: {price}元")

    # 4. 打印分类统计
    print("\n🔹 商品分类统计：")
    print("一级分类TOP5:")
    for l1 in data.categroy['top_l1']:
        total = sum(item['value'] for item in data.categroy['categories'][l1])
        print(f"- {l1} (共{total}种商品)")

        # 打印该分类下的二级分类TOP3
        top_l2 = sorted(data.categroy['categories'][l1], key=lambda x: x['value'], reverse=True)[:3]
        for l2 in top_l2:
            print(f"  ├ {l2['name']}: {l2['value']}种")

    print("\n" + "=" * 50)
    print("分析完成！")
    print("=" * 50)