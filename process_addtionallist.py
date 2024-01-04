filename = "additional_list.txt"  # 替换为你要处理的txt文件名
data_dict = {}
current_genre = None

with open(filename, "r") as file:
    for line in file:
        line = line.strip()
        
        if not line or line.startswith("#"):
            continue
        
        if "#genre#" in line:  # 格式2：name,url
            genrename = line.split(",")[0]
            current_genre = genrename
            data_dict[current_genre] = []
        else:
            splitresult = line.split(",")
            if current_genre is not None:
                data_dict[current_genre].append(splitresult)

with open("red2.m3u", "w") as file:
    file.write('#EXTM3U\n')
    for key in data_dict.keys():
        for value in data_dict[key]:
            print(value)
            file.write(f'#EXTINF:-1 group-title="{key}",{value[0]}\n{value[1]}\n')