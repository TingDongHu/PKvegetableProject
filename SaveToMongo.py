import pandas as pd
from pymongo import MongoClient
from datetime import datetime, date
import traceback
from tqdm import tqdm
import re

# 配置信息
CSV_FILE = 'xinfadi_prices_selenium.csv'
MONGODB_URI = "mongodb://DBadmin:DBpwd@127.0.0.1:27017/admin"
DB_NAME = "xinfadi"
COLLECTION_NAME = "prices"
BATCH_SIZE = 1000  # 每批插入的数据量


def clean_price(price_str):
    """清洗价格字符串并转为浮点数"""
    if not price_str or pd.isna(price_str):
        return None

    # 移除非数字字符（如￥、$等符号和中文单位）
    cleaned = re.sub(r'[^\d.]', '', str(price_str))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def clean_date(date_str):
    """清洗日期字符串并转为datetime对象（时间设为00:00:00）"""
    if not date_str or pd.isna(date_str):
        return None

    date_str = str(date_str).strip()

    # 尝试多种日期格式
    date_formats = [
        '%Y-%m-%d',  # 2023-07-20
        '%Y/%m/%d',  # 2023/07/20
        '%Y年%m月%d日',  # 2023年07月20日
        '%m/%d/%Y',  # 07/20/2023
        '%m-%d-%Y'  # 07-20-2023
    ]

    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # 关键修改：返回datetime对象但时间设为00:00:00
            return datetime(dt.year, dt.month, dt.day)
        except ValueError:
            continue

    return None


def connect_to_mongodb():
    """建立MongoDB连接"""
    try:
        print("🔌 正在连接MongoDB...")
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000
        )
        client.admin.command('ping')
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        print(f"✅ 成功连接到MongoDB (数据库: {DB_NAME}, 集合: {COLLECTION_NAME})")
        return collection
    except Exception as e:
        print(f"❌ MongoDB连接失败: {str(e)}")
        print(f"🔍 错误详情:\n{traceback.format_exc()}")
        return None


def read_and_clean_csv(file_path):
    """读取并清洗CSV数据"""
    try:
        print(f"📂 正在读取和清洗CSV文件: {file_path}")
        chunks = pd.read_csv(
            file_path,
            encoding='utf_8_sig',
            dtype=str,
            keep_default_na=False,
            chunksize=BATCH_SIZE
        )

        cleaned_data = []
        for chunk in tqdm(chunks, desc="清洗数据进度"):
            # 替换空字符串为None
            chunk = chunk.replace({'': None})

            # 转换价格字段
            chunk['最低价'] = chunk['最低价'].apply(clean_price)
            chunk['平均价'] = chunk['平均价'].apply(clean_price)
            chunk['最高价'] = chunk['最高价'].apply(clean_price)

            # 转换日期字段（关键修改：使用datetime对象）
            chunk['发布日期'] = chunk['发布日期'].apply(clean_date)

            # 过滤掉完全无效的记录
            chunk = chunk[~(
                    chunk['最低价'].isna() &
                    chunk['平均价'].isna() &
                    chunk['最高价'].isna() &
                    chunk['发布日期'].isna()
            )]

            cleaned_data.extend(chunk.to_dict('records'))

        print(f"✅ 成功清洗 {len(cleaned_data)} 条有效记录")
        return cleaned_data
    except Exception as e:
        print(f"❌ 读取/清洗CSV失败: {str(e)}")
        print(f"🔍 错误详情:\n{traceback.format_exc()}")
        return None


def insert_to_mongodb(collection, data):
    """将清洗后的数据插入MongoDB"""
    if not data or collection is None:
        print("⚠️ 无有效数据或连接无效")
        return False

    try:
        print("⏳ 正在准备批量导入...")
        total_count = len(data)
        inserted_count = 0
        batch_count = (total_count // BATCH_SIZE) + 1

        with tqdm(total=total_count, desc="导入进度") as pbar:
            for i in range(batch_count):
                batch = data[i * BATCH_SIZE: (i + 1) * BATCH_SIZE]
                if not batch:
                    continue

                # 添加导入时间戳
                current_time = datetime.now()
                for record in batch:
                    record['import_time'] = current_time

                # 批量插入
                result = collection.insert_many(batch)
                inserted_count += len(result.inserted_ids)
                pbar.update(len(batch))

        print(f"💾 成功导入 {inserted_count}/{total_count} 条记录")

        # 创建优化索引
        print("🔍 正在创建优化索引...")
        collection.create_index([("品名", 1)], background=True)
        collection.create_index([("发布日期", 1)], background=True)
        collection.create_index([("最低价", 1)], background=True)
        collection.create_index([("平均价", 1)], background=True)
        collection.create_index([("最高价", 1)], background=True)
        collection.create_index([("import_time", 1)], background=True)
        print("✅ 索引创建完成")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {str(e)}")
        print(f"🔍 错误详情:\n{traceback.format_exc()}")
        return False


def main():
    print("\n" + "=" * 60)
    print("📊 CSV数据清洗导入工具 (MongoDB兼容版)")
    print("=" * 60)

    # 1. 读取并清洗数据
    cleaned_data = read_and_clean_csv(CSV_FILE)
    if cleaned_data is None:
        return

    # 2. 连接数据库
    collection = connect_to_mongodb()
    if collection is None:
        return

    # 3. 导入数据
    if not insert_to_mongodb(collection, cleaned_data):
        print("❌ 导入过程中出现错误")
    else:
        # 打印统计信息
        stats = {
            "总记录数": collection.count_documents({}),
            "有价格记录": collection.count_documents({"最低价": {"$exists": True}}),
            "有日期记录": collection.count_documents({"发布日期": {"$exists": True}})
        }
        print("\n📊 集合统计:")
        for k, v in stats.items():
            print(f"{k}: {v}")

        # 验证第一条记录的日期格式
        sample = collection.find_one({}, {"发布日期": 1})
        print(f"\n示例日期格式: {sample['发布日期']} (类型: {type(sample['发布日期'])})")

    print("=" * 60)
    print("🏁 程序执行完毕")
    print("=" * 60)


if __name__ == "__main__":
    main()