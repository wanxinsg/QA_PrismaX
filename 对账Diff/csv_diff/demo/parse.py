import csv
import os
file_path = '/QA/Knowlege_PrismaX/对账Diff/csv_diff/demo/data.csv'
output = []

# 标准库解析，基本读取示例
# with open(file_path, newline = "",encoding='utf-8') as f:
#     reader = csv.reader(f)
#     for row in reader:
#         output.append(row)
        
# print(output[0])

#跳过表头，用DictReader
# with open(file_path, newline = "",encoding='utf-8') as f:
#     reader = csv.DictReader(f)
#     for row in reader:
#         output.append(row)
# print(output)

#指定分隔符或者引号
# reader = csv.DictReader(f,delimiter=';')

#自动检测分隔符用Sniffer
with open(file_path,"r",encoding='utf-8') as f:
    sample = f.read(1024)
    f.seek(0)
    dialect = csv.Sniffer().sniff(sample)
    reader = csv.reader(f,dialect)
    for row in reader:
        output.append(row)
print(output[0])

addtional_data = [
    {"name": "Wanxin", "age": 41, "city": "SG"},
    {"name": "Bob", "age": 25, "city": "Paris"},
]


with open(file_path, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "age", "city"])
    writer.writerows(addtional_data)
