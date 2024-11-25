

import os
from py2neo import Graph,Node
import json

class MedicalGraph():
    def __init__(self):
        self.cur_dir = '/'.join(os.path.abspath(__file__).split('/')[:-1])
        self.data_path =os.path.join(self.cur_dir,'data\medical_2.1_add.json')
        self.g = Graph("http://localhost:7474",auth=("neo4j", "123456"))
        #self.g = Graph("http://localhost:7474", auth=("neo4j", "123456"),name='neo4j')  # 新一版本的 neo4j 连接方式

    # 读取文件
    def read_nodes(self):
        # 共 2 类结点
        acupoints = [] #穴位
        diseases = []

        # 穴位 信息
        acupoint_info = []

        #构建结点 实体 关系  只有 1 种 关系
        rel_disease_point=[] #疾病--穴位 之间的关系

        count = 0
        for data in open(self.data_path,'r',encoding='utf-8'):
            acupoint_dict = {} #针灸字典
            count+=1
            data_json = json.loads(data)
            point = data_json['name']
            acupoint_dict['name'] = point
            acupoints.append(point)

            if 'diseases' in data_json:
                for disease in data_json['diseases']:
                    # print(disease.strip("''")) #去掉 疾病携带的标点符号
                    dis = disease.strip("''")
                    if len(dis)!=0: # 有一个穴位 乳中 的疾病是空
                        diseases.append(dis)
                        rel_disease_point.append([dis,point])
            if 'position' in data_json: #创建 穴位的定位属性
                acupoint_dict['position'] = data_json['position']
            acupoint_info.append(acupoint_dict)
                    # print(rel_disease_point)
        # print(rel_disease_point)
        # exit()
        # 疾病和穴位实体已经进行了 去重
        return set(diseases),set(acupoints),acupoint_info,rel_disease_point
    #建立 穴位 结点： 带属性的结点
    def create_Acupoint(self,acu_info):
        count = 0
        for acu_dic in acu_info:
            node  = Node("Acupoint",name=acu_dic['name'],position=acu_dic['position'])
            self.g.create(node)
            count+=1
            print("正在创建第{}个结点{},位置在{}".format(count, acu_dic['name'],acu_dic['position']))

    # 建立节点  不带属性的结点
    def common_create_node(self,label,nodes):
        count = 0
        for node_name in nodes:
            node = Node(label,name=node_name)
            self.g.create(node)
            count+=1
            print("正在创建第{}个结点{}".format(count,node_name))
        return

    '''创建知识图谱 实体节点类型schema'''
    def create_graphnodes(self):
        Diseases,Points,acupoint_info,rel_disease_point = self.read_nodes()
        self.common_create_node('Sym',Diseases)
        print(len(Diseases))
        self.create_Acupoint(acupoint_info)
        print(len(Points))
        return

    '''创建实体 关系边 '''
    def create_graphrels(self):
        Diseases, Points, _,rel_disease_point = self.read_nodes()
        # print(len(rel_disease_point))
        self.create_relationship('Sym','Acupoint',rel_disease_point,'select','治疗穴位')

    ''' 创建关系 '''
    def create_relationship(self, start_node, end_node, edges, rel_type, rel_name): #rel_type ： 关系类别  rel_name：关系名称
        count = 0
        # 去重处理
        set_edges = []
        for edge in edges:
            set_edges.append('###'.join(edge)) #以 ### 进行分割
        # print("")
        all = len(set(set_edges))
        print("一共有{}个关系，下面开始建立：".format(all))
        for edge in set(set_edges):
            edge = edge.split('###')
            p = edge[0] # start node
            q = edge[1] # end node
            query = "match(p:%s),(q:%s) where p.name='%s'and q.name='%s' create (p)-[rel:%s{name:'%s'}]->(q)" % (
                start_node, end_node, p, q, rel_type, rel_name)
            try:
                self.g.run(query) # 执行 创建边的cyper 语句
                count += 1
                # print(rel_type, count, all)
                print("第{}个关系正在建立：{}与{}".format(count,p,q))
            except Exception as e:
                print(e)
        return

    '''导出数据'''
    def export_data(self):
        Disease,Points,_,rel = self.read_nodes()
        f_disease = open('../dict/disease.txt', 'w+',encoding='utf-8')
        f_points = open('../dict/acupoints.txt', 'w+',encoding='utf-8')

        f_disease.write('\n'.join(list(Disease)))
        f_points.write('\n'.join(list(Points)))

        f_points.close()
        f_disease.close()


if __name__=='__main__':
    build = MedicalGraph()
    print("step1:导入图谱节点中") #✔
    build.create_graphnodes()
    print("step2:导入图谱边中")
    build.create_graphrels()
    print("step3:导出数据")
    build.export_data()


    '''
    数据待处理情况：
    已经能够提取出来的穴位：
        疾病情况进行考虑：分号、顿号 可用split多字符分割进行，分割符与分隔符之间用'|'隔开，解决 1，3 情况 ✔
            1.正在创建第247个结点头痛、耳鸣、耳痛、小儿惊痫  正在创建第248个结点月经不调、症瘕、正在创建第269个结点下肢痿痹、遍身瘙痒
            2. 盗 汗 空格还行   257：攒竹 目赤 肿痛
            3. 103太溪：配然谷主治热病烦心，足寒清，多汗；配肾俞治肾胀；配支沟、然谷治心痛如锥刺。 分号；
            4. 7 百会： 提取错误 ❌ 解决办法 单独提一下看看为什么错 错误原因科室是写了 主治二字 所以在抓取的时候条件应为【主治】 已修改 ✔
            5. 创建疾病其中有个结点名称为空？✔
            6. 疾病名称重复： 项强不得顾   项强
            7. 【主治] 或【主治] 两个类型的，导致 10：神庭 提取错误 ] 头痛 ✔
            8 小便不利或失禁 手指及肘臂挛痛 这样的带 或/及 的提取情况
            9 目赤 肿痛 
            10 273：乳中 无主治疾病s 
           
    未能够提取出来的穴位：网页中含有不属于穴位的其他东西
     网页1： https://www.zhzyw.com/zyts/zyzj/jl/index_1.html
     网页2： https://www.zhzyw.com/zyts/zyzj/jl/index_13.html
    '''