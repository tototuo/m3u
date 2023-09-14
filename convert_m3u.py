import csv
import re
import json
import requests
import time
import os

def extract_info(file_name):
    with open(file_name, 'r') as file:
        content = file.read()

    pattern = re.compile(r'(.*),(.+)\n(.+)')
    logo_pattern = re.compile(r'tvg-logo="(.+?)"')
    group_pattern = re.compile(r'group-title="(.+?)"')
    
    results = []

    matches = pattern.findall(content)
    rules = rules_dict[file_name]

    for match in matches:
        logo_match = logo_pattern.search(match[0])
        group_match = group_pattern.search(match[0])
        logo = ''
        group = ''
        if logo_match:
            logo = logo_match.group(1)
        if group_match:
            group = group_match.group(1)
        name, url = match[1].strip(), match[2].strip()

        group = group.replace('•', '')

        skip, group, name, url, logo = apply_rules(rules, group, name, url, logo)
        if skip:
            continue
        results.append((group, name, url, logo))

    return results

def apply_rules(rules, group, name, url, logo):
    skip = False
    if 'GroupFilter' in rules:
        if rules['GroupFilter']['Mode'] == 'Include':
            include_list = rules['GroupFilter']['IncludeList']
            if group not in include_list:
                skip = True
        elif rules['GroupFilter']['Mode'] == 'Exclude':
            exclude_list = rules['GroupFilter']['ExcludeList']
            if group in exclude_list:
                skip = True

    if 'UrlFilter' in rules:
        if rules['UrlFilter']['Mode'] == 'Include':
            include_list = rules['UrlFilter']['IncludeList']
            for urlfilter in include_list:
                if urlfilter not in url:
                    skip = True
        elif rules['UrlFilter']['Mode'] == 'Exclude':
            exclude_list = rules['UrlFilter']['ExcludeList']
            for urlfilter in exclude_list:
                if urlfilter in url:
                    skip = True

    if 'GroupPrefix' in rules:
        group = rules['GroupPrefix'] + group
    if 'SkipIPV6' in rules and rules['SkipIPV6']:
        if is_ipv6(url):
            skip = True
    return skip, group, name, url, logo

def is_ipv6(url):
    pattern = re.compile(r'\[(([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4})]')
    return bool(pattern.search(url))

def write_to_csv(results, csv_file):
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['group', 'name', 'url', 'logo'])
        writer.writerows(results)

def write_to_m3u(results, m3u_file):
    with open(m3u_file, 'w', newline='') as file:
        file.write('#EXTM3U\n')
        for row in results:
            group = row[0]
            name = row[1]
            url = row[2]
            logo = row[3]
            file.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{name}\n{url}\n')

update_exsiting = True
gather_count = 300
limit = 30

def generate_douyu_indexes(cate_id):
    if os.path.exists(f"douyu_indexes_{cate_id}.json"):
        with open(f"douyu_indexes_{cate_id}.json", 'r') as f:
            exsit_indexes = json.load(f)
            if not update_exsiting:
                return exsit_indexes
    
    result = []
    offset = 0
    for loop_i in range(int(gather_count/limit)):
        response = requests.get(f'http://capi.douyucdn.cn/api/v1/live/{cate_id}?&limit={limit}&offset={offset}')
        html = response.content.decode('utf-8')
        #print(html)
        json_result = json.loads(html)['data']
        result.extend(json_result)
        offset += limit
        time.sleep(0.5)

    result = [i for i in result if i['cate_id'] == cate_id]

    current_get_names = [x['room_id'] for x in result]
    print(current_get_names)

    for item in exsit_indexes['data']:
        if item['room_id'] not in current_get_names:
            result.append(item)


    with open(f"douyu_indexes_{cate_id}.json","w") as f:
        json.dump({"data":result}, f, indent=2, ensure_ascii=False)
        print(f"已生成 douyu_indexes_{cate_id}.json文件...") #读取json文件

    return {"data":result}

def mannually_gather_douyu(gather, douyu_indexes):
    print('  ', douyu_indexes['data'][0]['game_name'])
    
    douyu_list = douyu_indexes['data']
    douyu_list = sorted(douyu_list, key=lambda x: int(x['fans']), reverse=True)
    for item in douyu_list:
        if int(item['fans']) < 1000:
            continue
        group = 'Douyu-'+item['game_name']
        name = item['nickname']
        url = 'https://tv.iill.top/douyu/'+item['room_id']
        logo = item['avatar_mid']
        gather.append((group,name,url,logo))
        #print(item['fans'])
    return gather

rules_list = ['green']
douyu_indexes1 = generate_douyu_indexes(1)  # 1 for lol
douyu_indexes208 = generate_douyu_indexes(208)  # 208 for movie
douyu_indexes1008 = generate_douyu_indexes(1008)  # 1008 for mina

for rule_name in rules_list:
    # load rule
    rule_filename = f'rules_{rule_name}.json'
    print(f'processing {rule_filename}...')
    rules_dict = {}
    with open(rule_filename, 'r') as f:
        data = json.load(f)
    for item in data['All']:
        rules_dict[item['Filename']] = item['Rules']

    gather = []
    for file, pattern in rules_dict.items():
        gather += extract_info(file)
    print("add douyu channels")
    gather = mannually_gather_douyu(gather, douyu_indexes1)
    gather = mannually_gather_douyu(gather, douyu_indexes208)
    gather = mannually_gather_douyu(gather, douyu_indexes1008)
    sorted_list = sorted(gather, key=lambda x: x[0]) # sort by group

    write_to_csv(sorted_list, f'{rule_name}.csv')
    write_to_m3u(sorted_list, f'{rule_name}.m3u')

