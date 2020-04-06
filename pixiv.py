'pixiv.py 1.0.0'
import os
import sys
import math
import json
import urllib
import requests


def DownLoad(url, path, pid, page_count, stats):
    '下载'
    global last
    last -= 1
    # 两种储存方式：direct、sort
    # direct会将图片以id_p0.jpg...的形式储存
    # sort  会将图片以p0.jpg...的形式储存在对应id文件夹中
    if method == 'sort':
        path = path + pid + '\\'
    for i in range(page_count):
        print(' >>>开始[' + pid + ']的第 ' + str(i+1) + ' 个下载')
        det = url[-4:]  # 取出图片后缀
        if method == 'sort':
            File = 'p' + str(i) + det
        elif method == 'direct':
            File = pid + '_p' + str(i) + det
        else:
            print('请检查method参数项')
            break
        # 检验文件夹是否存在
        pathExists = os.path.exists(path)
        if not pathExists:
            os.makedirs(path)
        # 检验文件是否已下载
        fileExists = os.path.exists(path + File)
        if not fileExists:
            urllib.request.urlretrieve(url.replace('_p0', '_p' + str(i)), path + File)
            print('   >下载完成')
        else:
            print('   >已存在')


def judge(stats):
    '判断是否符合初设条件'
    return views <= stats['views_count'] and\
        score <= stats['scored_count'] and\
        conts <= stats['commented_count'] and\
        likes <= stats['favorited_count']['public'] +\
        stats['favorited_count']['private']


# https://api.imjad.cn/pixiv/v1/?type=member_illust&id=17029152
def Traversal(utype, uid, path):
    '遍历Json'
    print('初始化完成', end='')
    # 统计r18相册数和已遍历相册数
    r18 = 0
    rnt = 0
    cnt = 0
    dnt = 0
    # pixiv api
    web = 'https://api.imjad.cn/pixiv/v1/?'
    # cmd标题
    title = 'title type=' + str(utype) + ',id=' + str(uid).replace('&', ',')
    # 获取Json
    resp = requests.get(url=web + 'per_page=1&' + 'type=' + str(utype) + '&id=' + str(uid))
    data = json.loads(resp.text)
    # 总相册数
    total = int(data['pagination']['total'])
    title = title + ',total=' + str(total)
    # 需要遍历Json页数
    pages = math.ceil(total/N)
    # top为Open时才更改cmd标题(太卡了)
    print(',总相册数:', total, '总页数:', pages)
    if top == 'Open':
        os.system(title)
    # 以页为单位遍历
    for i in range(1, pages+1):
        url = web + 'per_page=' + str(N) + '&type=' + str(utype) + '&id=' + str(uid) + '&page=' + str(i)
        print('正从"' + url + '"获取第 ' + str(i) + ' 份Json')
        resp = requests.get(url=url)
        data = json.loads(resp.text)
        # 当前页含有相册数
        count = int(data['count'])
        # 遍历每一个相册
        for j in range(count):
            cnt += 1
            if top == 'Open':
                os.system(title + ',cnt=' + str(cnt))
            mask = data['response'][j]
            stats = mask['stats']
            # echo为Open时才输出这个相册的喜爱程度
            if cfg['judge']['echo'] == 'Open':
                print('[' + str(mask['id']) + ']' + '得分:%5d 观看:%5d 喜爱:%5d 评论:%5d' % (stats['scored_count'], stats['views_count'], stats['favorited_count']['public'] + stats['favorited_count']['private'], stats['commented_count']))
            if not judge(mask['stats']):
                continue
            pid = str(mask['id'])  # 相册id
            age = mask['age_limit']  # r18/all-age
            pic = mask['image_urls']['large']  # 大图地址
            # 替换为国内镜像
            pic = pic.replace("i.pximg.net", "tc-pximg01.techorus-cdn.com")
            # 相册内作品数
            page_count = int(mask['page_count'])
            if age == 'r18':
                rnt += 1
            # 根据条件判断是否下载
            if R18 == 'Only':
                if age == 'all-age':
                    continue
                else:
                    r18 += 1
                    dnt += 1
                    DownLoad(pic, path, pid, page_count, mask['stats'])
            elif R18 == 'Open':
                if age == 'r18':
                    r18 += 1
                dnt += 1
                DownLoad(pic, path, pid, page_count, mask['stats'])
            else:
                if age == 'r18':
                    continue
                else:
                    dnt += 1
                    DownLoad(pic, path, pid, page_count, mask['stats'])
            if last <= 0:
                break
        if last <= 0:
            break
    print('已遍历R18相册总数:%3d 已遍历相册总数:%3d' % (rnt, cnt), end=' ')
    print('R18占已遍历相册比: ' + str(rnt / cnt * 100) + '%')
    print('已下载R18相册数量:%3d 已下载相册数量:%3d' % (r18, dnt), end=' ')
    print('R18占已下载相册比: ' + str(r18 / dnt * 100) + '%')
    return


def reader():
    '读取配置文件'
    global cfg
    ctmp = cfg
    select = cfg['select']
    mcount = cfg['count']
    # select是数字,直接进入,是字符就找这个name
    if isinstance(select, int):
        if 0 <= select and select < mcount:
            cfg = cfg['manner'][select]
            return True
        else:
            print('请检查select/count参数项')
            return False
    elif isinstance(select, str):
        for i in range(mcount):
            if cfg['manner'][i]['name'] == select:
                cfg = cfg['manner'][i]
                return True
        # 如果遍历了一遍没找到要返回False
        if ctmp == cfg:
            print('请检查select参数项')
            return False
    else:
        print('请检查select参数项')
        return False


# 定义一些全局变量
R18 = 'Off'
top = 'Off'
method = 'direct'
N = 30
last = -1
score = -1
views = -1
likes = -1
conts = -1
# 检测配置文件,存在则文件读取,否则手动输入
fileExists = os.path.exists('config.json')
if not fileExists:
    utype, uid, R18, top, path, method, N, last, score, views, likes, conts = input().split()
    N = int(N)
    last = int(last)
    score = int(score)
    views = int(views)
    likes = int(likes)
    conts = int(conts)
else:
    with open("config.json", encoding="utf-8") as f:
        cfg = json.load(f)
    f.close()
    if reader():
        uid = cfg['id']
        R18 = cfg['R18']
        top = cfg['top']
        last = cfg['last']
        path = cfg['path']
        utype = cfg['type']
        N = cfg['per_page']
        method = cfg['method']
        score = cfg['judge']['score']
        views = cfg['judge']['views']
        likes = cfg['judge']['likes']
        conts = cfg['judge']['comments']
    else:
        print('读取失败')
        os.system('pause')
        sys.exit()
# 遍历Json
Traversal(utype, uid, path)
os.system('pause')
