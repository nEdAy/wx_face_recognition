import os
import urllib3


def download_file(img_url, file_name, file_path='cache/faces'):
    # 保存文件到磁盘文件夹 file_path 中，默认为当前脚本运行目录下的 cache/faces 文件夹
    try:
        if not os.path.exists(file_path):
            print('文件夹', file_path, '不存在，重新建立')
            os.makedirs(file_path)
        # 下载图片，并保存到文件夹中
        http = urllib3.PoolManager()
        print(img_url)
        response = http.request('GET', img_url)
        save_path = '{}{}{}'.format(file_path, os.altsep, file_name)
        with open(save_path, 'wb') as f:
            f.write(response.data)
        response.release_conn()
        return save_path
    except IOError as e:
        print('文件操作失败', e)
    except Exception as e:
        print('错误 ：', e)
