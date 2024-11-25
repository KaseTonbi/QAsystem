
class QuestionParser:

    '''构建实体结点'''
    def build_entitydict(self,args):
        entity_dict = {}
        for arg,types in args.items(): #根据 类别 去创建实体  获取 disease 类别，arg 为 头痛
            for type in types:
                if type not in entity_dict:
                    entity_dict[type] = [arg]
                else:
                    entity_dict[type].append(arg)
        return entity_dict  #{'disease'：['头痛']}

    ''' 解析主函数'''

    def parser_main(self,res_classify):
        args = res_classify['args'] #经过 分类后处理的数据 {'头痛'：['disease']}
        # print(args)
        entity_dict = self.build_entitydict(args)  # 获取到实体类型以及具体的实体
        question_types = res_classify['question_types'] # 获取查询类型
        sqls = []
        for question_type in question_types:
            sql_ = {}
            sql_['question_type'] = question_type
            sql = []
            if question_type == 'disease_cureway':
                sql = self.sql_transfer(question_type,entity_dict.get('disease'))
            elif question_type == 'acupoint_disease':
                sql = self.sql_transfer(question_type, entity_dict.get('acupoint'))
            elif question_type =='acupoint_position':
                sql = self.sql_transfer(question_type, entity_dict.get('acupoint'))
            if sql:
                sql_['sql'] = sql
                sqls.append(sql_)
        return sqls

    ''' 针对不同的问题，分开进行处理'''
    def sql_transfer(self,question_type,entities):
        if not entities: # 如果实体为空，返回空
            return []

        # 查询语句

        # 查询疾病的治疗方式
        if question_type == 'disease_cureway':
            sql = [
                "MATCH (m:Sym)-[r:select]->(n:Acupoint) where m.name = '{0}' return m.name, r.name, n.name".format(
                    i) for i in entities]

        # 查询穴位 治疗的疾病
        elif question_type == 'acupoint_disease':
            sql = [
                "MATCH (m:Sym)-[r:select]->(n:Acupoint) where n.name = '{0}' return m.name, r.name, n.name".format(
                    i) for i in entities]
        elif question_type == 'acupoint_position':
            sql = ["MATCH (m:Acupoint) where m.name = '{0}' return m.name,m.position".format(i) for i in entities]

        return sql


if __name__=='__main__':
    handler = QuestionParser()