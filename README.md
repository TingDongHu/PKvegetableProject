# 北京新发地市场信息采集可视化系统
爬取的网站链接：http://www.xinfadi.com.cn/priceDetail.html
![image](https://github.com/user-attachments/assets/ba6a7bb3-85ac-47a1-b92c-8aa35f9f217a)

## 模块划分
- 爬虫模块：Vegetable_Get.py
- 数据存储：SaveToMongo.py
- 数据分析统计：DataGet.py
- 可视化模块：app.py
## 配置环境
基于`requirement.txt`完成库配置后，需要修改`Vegetable_Get.py`中的`webdriver`的链接地址,以及`SaveToMongo.py`和`DataGet.py`中的本地MongoDB库的链接，确保数据可以正常存储和读取。
## 使用说明
运行`Vegetable_Get.py`文件从北京新发地网站抓取数据。
抓取的数据默认存储在csv文件中，抓取完成后运行SaveToMongo.py进行数据清洗和存储。
存储后运行app.py在网页端进行可视化。
## 技术栈说明
### 爬虫部分
爬虫使用Selenium库和Chrome浏览器驱动来抓取数据。基于Selenium框架实现北京新发地市场价格数据的自动化采集，采用模块化设计思路：首先通过精心配置的ChromeDriver初始化浏览器实例，注入反检测脚本并设置随机用户代理以规避反爬机制；随后模拟人类操作行为，包括随机延迟、平滑滚动和动作链点击，精准定位并触发页面查询功能。
### 可视化部分
通过re库、wordcloud库以及利用MongoDB中的aggregation管道函数等对爬取的到的市场信息的统计，再将统计以后的数据通过图表地方式展示在前端，即后端传数据，前端Echarts绘制图表。

## 运行测试结果
### MongoDB数据库的compass可视化工具的存储部分数据：
![image](https://github.com/user-attachments/assets/c5c69250-c3d1-4254-b7f5-ed1015b33c18)
### 可视化结果：
![image](https://github.com/user-attachments/assets/8ef34b02-076a-4b23-9a77-6b4e372f3045)

![image](https://github.com/user-attachments/assets/f13bebeb-9688-4542-af1a-e5cd11a7de21)

![image](https://github.com/user-attachments/assets/6c1936ab-17ea-4156-90e3-93deb364a54d)

![image](https://github.com/user-attachments/assets/05dc627c-9303-4d7d-ada2-52bebfd9b807)

![image](https://github.com/user-attachments/assets/b20892d0-d9be-4005-a9f8-98ff86d21732)

![image](https://github.com/user-attachments/assets/382cbef5-95bb-42b4-b341-ad4270a228fa)


