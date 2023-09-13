import csv
import re
import json

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


rules_list = ['green', 'all']
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

    sorted_list = sorted(gather, key=lambda x: x[0])

    write_to_csv(sorted_list, f'{rule_name}.csv')
    write_to_m3u(sorted_list, f'{rule_name}.m3u')

