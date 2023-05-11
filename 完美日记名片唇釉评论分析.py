# 导入所需库
import requests      # 用于发送网络请求
import pymysql       # 用于连接mysql数据库
import numpy as np   # 用于数据处理
import jieba         # 用于中文分词
from wordcloud import WordCloud
import PIL.Image as Image
import os

# 网络爬虫及数据存入
class perfect_diary_comment_spider(object):
    # 请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36 Edg/101.0.1210.39'
    }

    def __init__(self, file_name='pdc_raw',database_name='perfect_dairy',):
        # 实例化类的时候运行初始化函数
        # 打开文件
        self.file = open(f'data/final/{file_name}.txt', 'w', encoding='utf-8-sig')  # 新建一个txt文档存入色号和评论数据用于后续词云分析
        print(f'正在打开文件{file_name}.txt文件!')
        
        # 创建数据库
        cur_obj.execute(f'drop database if exists {database_name}')
        cur_obj.execute(f'create database {database_name}')
        mysql_obj.select_db(f'{database_name}')
        sql="""
        create table tb1 
        (
        id int primary key auto_increment,
        nickname varchar(200) not null,
        productColor varchar(200) not null,
        score int,
        comment varchar(500),
        creationTime varchar(20)
        )
        """
        cur_obj.execute(sql)
        print(f'成功创建{database_name}数据库！')

        
    def parse_one_page(self, url):
        '''
        单页面评论的爬取
        :url: 当前页面的url
        :return: 获取当前页面的数据写入数据库和txt文档
        '''
        # 发起请求
        response = requests.get(url, headers=self.headers)
        # 获取响应
        js_data = response.json()   # type(js_data) = dict
        # 提取评论列表
        comments_list = js_data['comments']

        for comment in comments_list:
            # 用户昵称
            nickname = comment.get('nickname')
            # 口红色号
            productColor = comment.get('productColor')
            # 评分
            score = comment.get('score')
            # 评论内容
            content = comment.get('content')
            content = ' '.join(content.split('\n'))  # 处理换行符
            # 评论时间
            creationTime = comment.get('creationTime')

            # 把数据写入数据库
            cur_obj.execute(
                'insert into tb1(id,nickname,productColor,score,comment,creationTime) value(0,("%s"),("%s"),("%d"),("%s"),("%s"))'%(nickname,productColor,score,content,creationTime))
            # 把数据写入文件
            self.file.write(f'{productColor}\t{content}\n')


    def parse_all_page(self):
        '''
        进行翻页操作获取想要页数的评论
        :input: 需要的页数数量
        :return: 获取全部页面评论
        '''
        pages_ = int(input('请输入需要获取的页数：'))
        for page_num in range(pages_):  # 需要抓取的每一页
            # 指定通用的url模板
            new_url = f'https://club.jd.com/comment/productPageComments.action?productId=100018482877&score=0&sortType=5&page={page_num}&pageSize=10&isShadowSku=0&rid=0&fold=1'
            print(f'正在获取第{page_num}页')

            # 调用parse_one_page函数
            self.parse_one_page(url=new_url)


    def commit_close_mysql(self):
        # 提交操作
        mysql_obj.commit()
        count = cur_obj.execute("select * from tb1")
        count
        # 断开连接
        cur_obj.close()
        mysql_obj.close()


    def close_files(self):
        self.file.close()
        print('爬虫结束，关闭文件！')


# 文本分词和词云分析
class txt_to_wrc(object):

    def __init__ (self, file_name = 'pdc_raw', outfile_name = 'pdc_output'):
        # 指定文档路径       
        self.inputs = open(f'data/final/{file_name}.txt','r',encoding='UTF-8-sig')
        self.outputs = open(f'data/final/{outfile_name}.txt','w+',encoding='UTF-8-sig')


    def stopwordslist(self,stopwordslist_name = 'hit_stopwords'):
        '''
        设置停用词表
        :stopwordslist_name: 选用的停用词表txt文档名
        :return: 将txt文档转为list类型数据
        '''
        stopwords = [i.strip() for i in open(f'./{stopwordslist_name}.txt', encoding = 'UTF-8-sig').readlines()]
        return stopwords


    def seg_depart(self,sentence):
        '''
        中文分词和去除停用词
        '''
        print("正在分词和去除停用词……")
        #对文档中的每一行中文分词
        sentence_depart = jieba.lcut(sentence.strip())
        # 创建停用词列表
        stopwords = self.stopwordslist()
        # 输出结果为output
        output = ''
        # 去除停用词
        for word in sentence_depart:
            if word not in stopwords:
                if word != '\t':
                    output += word
                    output += " "
        return output

    def write_into_txt(self):
        '''
        将分词和去停用词后的结果写入pdc_output
        ''' 
        for line in self.inputs:
            line_seg = self.seg_depart(line)
            self.outputs.write(line_seg + '\n')
        self.inputs.close()
        print("分词和去除停用词成功！")

        # 将光标移动至起始位置,省去这一步将导致数据读出为空
        self.outputs.seek(0,os.SEEK_SET)
        print(self.outputs.tell())    # 显示光标在文档中的位置，返回0为文档开头
        

    def generate_wcd(self,bg_pic_name = 'mouth',font_name = 'simhei'): 
        '''
        生成词云
        '''
        # 导入中文字体
        font_path = f'data/final/{font_name}.ttf'  
        # 读入背景图
        bg_pic = np.array(Image.open(f'{bg_pic_name}.jpg')) 

        wcd = WordCloud(
            font_path = font_path,
            mask = bg_pic,
            background_color="white",
            colormap="Reds",
            max_font_size = 120,
            stopwords = {'产品质感','产品颜色','产品外观','保湿效果','轻薄程度','持久效果','滋润效果','适合肤色','显色效果','颜色','HOT','NEW'},
            repeat = False, 
            max_words = 100
            )

        wcd.generate(self.outputs.read())
        wcd.to_file('data/final/wcd_image.png')
        self.outputs.close()
        
        
        


if __name__ == '__main__':   
    # 连接mysql数据库
    mysql_obj = pymysql.connect(host = 'localhost',user = 'root',password = 'lm020225',port = 3306,charset='utf8mb4') 
    cur_obj = mysql_obj.cursor()
    print('数据库连接成功！') 
  
    # 实例化perfect_diary_comment_spider对象
    perfect_dairy_spider = perfect_diary_comment_spider()
    # 开始爬虫
    perfect_dairy_spider.parse_all_page()
    # 向mysql提交操作并断开连接
    perfect_dairy_spider.commit_close_mysql()
    # 关闭文件
    perfect_dairy_spider.close_files()

    # 实例化txt_to_wrc对象
    txt_to_wrc1 = txt_to_wrc()
    # 分词和数据清洗
    txt_to_wrc1.write_into_txt()
    # 生成词云
    txt_to_wrc1.generate_wcd()
    


