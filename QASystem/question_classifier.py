
import os
import ahocorasick  # pip install pyahocorasick
class QuestionClassifiler:
    def __init__(self):
        # self.cur_dir = '/'.join(os.path.abspath(__file__).split('/')[:-1]) #获取当前路径
        self.cur_dir  = '/'.join(os.path.abspath(__file__).split('/')[:-1])
        # 获取特征词路径
        self.disease_path = os.path.join(self.cur_dir,'dict/disease.txt')
        self.acupoint_path = os.path.join(self.cur_dir,'dict/acupoints.txt')

        # 加载特征词
        # for i in open(self.disease_path,'r',encoding='utf-8'):
        #     print(i.strip())  i.strip() 是为了去除换行
        self.disease_wds = [i.strip() for i in open(self.disease_path,'r',encoding='utf-8') if i.strip()]
        self.acupoint_wds = [i.strip() for i in open(self.acupoint_path,'r',encoding='utf-8') if i.strip()]
        self.region_wds = set(self.disease_wds+self.acupoint_wds)

        #构造领域 actree 多模板匹配
        self.region_tree = self.build_actree(list(self.region_wds)) #list(self.region_wds) 将各实体转换为 list

        #构建词典
        self.wdtype_dict = self.build_wdtype_dict()

        # 问句疑问句
        self.cureway_qwds = ['治疗','怎么治疗', '如何医治', '怎么医治', '怎么治', '怎么医', '如何治', '医治方式', '疗法', '咋治', '怎么办', '咋办','有什么治疗方法','治疗方案','治疗措施']
        self.cure_qwds = ['治疗什么', '作用','治啥', '治疗啥', '医治啥', '治愈啥', '主治啥', '主治什么', '有什么用', '有何用', '用处', '用途',
                          '有什么好处', '有什么益处', '有何益处', '用来', '用来做啥', '用来作甚','有啥用','有啥用处','功效','有用']
        self.position_qwds = ['在哪','位置','哪里','地方','位于']
        print('model init finished ......')
        return

    # 构建分类函数
    def classify(self,question):
        data = {}
        medical_dict = self.check_medical(question) # input：头痛怎么治疗？ medical_dict={'头痛'：['disease']}
        if not medical_dict: #若 medical 是空的 则返回空字典
            return {}

        data['args'] = medical_dict

        # 收集问句当中所涉及到的 实体类型
        types = []
        for type_ in medical_dict.values():
            types += type_

        question_types = []
        question_type = 'others'

        # 疾病 治疗方式
        if self.check_words(self.cureway_qwds,question) and 'disease' in types:
            question_type = 'disease_cureway'
            question_types.append(question_type)

        # 穴位治疗什么疾病
        if self.check_words(self.cure_qwds, question) and 'acupoint' in types:
            question_type = 'acupoint_disease'
            question_types.append(question_type)

        if self.check_words(self.position_qwds,question) and 'acupoint' in types:
            question_type = 'acupoint_position'
            question_types.append(question_type)
        # 将多个分类结果进行合并处理，组装成一个字典
        data['question_types'] = question_types
        return data

    # 问句过滤 获取实体以及类别
    def check_medical(self,question):
        region_wds = []
        for i in self.region_tree.iter(question):#iter(question) 有什么作用 ？作用就是获取问句里面对应的实体
            wd = i[1][1] # wd 最后是啥 wd最后是对应的实体   比如输入问句 头痛怎么治疗   wd = 头痛
            region_wds.append(wd)
        stop_wds = []
        for wd1 in region_wds: # 这里为什么要用双层循环？即 stop_words的作用是什么？
            for wd2 in region_wds:
                if wd1 in wd2 and wd1 != wd2:
                    stop_wds.append(wd1)
        final_wds = [i for i in region_wds if i not in stop_wds]
        final_dict = {i:self.wdtype_dict.get(i) for i in final_wds} # final_dict: {‘头痛’：['disease']}

        return final_dict



    # 构建领域树
    def build_actree(self,wordlist):
        actree = ahocorasick.Automaton() #多模板自动匹配算法，构建 实体字典树，快速匹配字符串中的多个子串；在 问句输入的时候进行 实体的快速匹配
        for index,word in enumerate(wordlist):
            actree.add_word(word,(index,word))
        actree.make_automaton()
        return actree

    # 构建词典  词对应的类型
    def build_wdtype_dict(self):
        wd_dict = dict() #{'口疮'：['disease'],'肋骨疼痛'：['disease']}
        for wd in self.region_wds:
            wd_dict[wd] = []
            if wd in self.disease_wds:
                wd_dict[wd].append('disease')
            if wd in self.acupoint_wds:
                wd_dict[wd].append('acupoint')
        return wd_dict

    # 基于特征词进行分类
    def check_words(self,wds,input):   # 对于 输入问句中 提到的 搜索关键字（比如：治疗方式）进行提取
        for wd in wds:
            if wd in input:
                return True
        return False

if __name__=='__main__':
    qas = QuestionClassifiler()
    question = input('用户:')
    qas.classify(question)