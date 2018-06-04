import os
import urllib3


def download_file(img_url, file_name, dir_path='cache/faces'):
    # 保存文件到磁盘文件夹 file_path 中，默认为当前脚本运行目录下的 cache/faces 文件夹
    try:
        if not os.path.exists(dir_path):
            print('文件夹', dir_path, '不存在，重新建立')
            os.makedirs(dir_path)
        # 下载图片，并保存到文件夹中
        http = urllib3.PoolManager()
        print(img_url)
        response = http.request('GET', img_url)
        save_path = '{}{}{}'.format(dir_path, os.sep, file_name)
        with open(save_path, 'wb') as f:
            f.write(response.data)
        response.release_conn()
        return save_path
    except IOError as e:
        print('文件操作失败', e)
    except Exception as e:
        print('错误 ：', e)
