
from flask import Flask, render_template, jsonify
from DataGet import DataGet

app = Flask(__name__)

# 初始化数据获取类
data_getter = DataGet()

@app.route('/')
@app.route('/index/')
def index():
    # 直接获取数据并传递给模板
    samples = data_getter.get_random_samples()
    return render_template('index.html', samples=samples)


@app.route('/priceoftime/')
def price_trend():
    try:
        price_data = data_getter.get_price_trend()
        print("价格趋势数据:", price_data)

        # 计算统计信息
        stats = {
            'avg_avg_price': round(sum(price_data['avg_prices']) / len(price_data['avg_prices']), 2),
            'max_price': round(max(price_data['max_prices']), 2),
            'min_price': round(min(price_data['min_prices']), 2)
        } if price_data['avg_prices'] else None

        return render_template(
            'price_trend.html',
            dates=price_data['dates'],
            avg_prices=price_data['avg_prices'],
            min_prices=price_data['min_prices'],
            max_prices=price_data['max_prices'],
            data_range=price_data['data_range'],
            total_days=price_data['total_days'],
            stats=stats
        )

    except Exception as e:
        print(f"价格趋势数据获取失败: {str(e)}")
        return render_template(
            'price_trend.html',
            error=str(e),
            dates=[],
            avg_prices=[],
            min_prices=[],
            max_prices=[],
            data_range='',
            total_days=0
        )

# 同时保留页面路由和API路由
@app.route('/wordcloud/')
def wordcloud():
    origin_data = data_getter.get_origin_stats()
    return render_template('wordcloud.html',
                         origins=origin_data['origins'],
                         counts=origin_data['counts'],
                         total=origin_data['total'])

# 新增API路由
@app.route('/api/origin-stats')
def origin_stats_api():
    origin_data = data_getter.get_origin_stats()
    return jsonify({
        'status': 'success',
        'data': {
            'origins': origin_data['origins'],
            'counts': origin_data['counts'],
            'total': origin_data['total']
        }
    })
@app.route('/priceofitem/')
def price_item():
    # 获取分类数据
    category_data = data_getter.get_category_stats()
    return render_template('price_item.html',
                         categories=category_data['categories'],
                         top_l1=category_data['top_l1'])

@app.route('/market/')
def market():
    # 获取分类统计数据
    category_stats = data_getter.get_category_stats()
    print(category_stats)
    return render_template('market.html',
                         categories=category_stats['categories'],
                         top_l1=category_stats['top_l1'])

if __name__ == "__main__":
    app.run(debug=True)