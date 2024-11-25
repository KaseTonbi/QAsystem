

from py2neo import Graph
class AnswerSearcher:
    def __init__(self):
        self.g = Graph("http://localhost:7474",auth=("neo4j", "123456"))
        self.num_limit = 25

    '''执行cyper 查询语句，并返回相应结果'''
    def serch_main(self,sqls):
        final_answers = []
        for sql_ in sqls:
            question_type = sql_['question_type']
            queries = sql_['sql']
            answers = []

            for query in queries:# sql语句
                ress = self.g.run(query).data() #获取查询结果数据
                # res=ress.data()
                answers += ress
            final_answer = self.answer_prettify(question_type,answers)
            if final_answer:
                final_answers.append(final_answer)
                # if len(final_answer)==1:
                #     final_answers.append(final_answer)
                # else:
                #     for ans in final_answer:
                #         final_answers.append(ans)
        return final_answers

    '''根据对应的question_type,调用相应的回复模板'''
    def answer_prettify(self,question_type,answers):
        final_answer = []
        if not answers:
            return ''
        # 疾病治疗方式
        if question_type == 'disease_cureway':
            desc = [i['n.name'] for i in answers]
            subject = answers[0]['m.name']
            set_desc = set(desc)
            list_desc = list(set_desc)
            final_answer = '{}可以通过扎以下穴位进行治疗：{}'.format(subject,'；'.join(list(set(desc))[:self.num_limit]))
        # 穴位治疗哪些疾病
        elif question_type == 'acupoint_disease':
            desc = [i['m.name'] for i in answers]
            subject = answers[0]['n.name']
            final_answer = '{0}主治的疾病有{1}'.format(subject, '；'.join(list(set(desc))[:self.num_limit]))
        elif question_type == 'acupoint_position':
            pos = answers[0]['m.position']
            sub = answers[0]['m.name']
            final_answer ='{0}的位置：{1}'.format(sub, pos)
            # position = [i['m.position'] for i in answers]
            # subject = [i['m.name'] for i in answers]
            # n = len(position)
            # i=0
            # while i<n:
            #     fin_answer = '{0}的位置：{1}'.format(subject[i], position[i])
            #     final_answer.append(fin_answer)
            #     i+=1
        return final_answer

if __name__=='__main__':
    searcher = AnswerSearcher()
    # print(searcher.serch_main([{'question_type': 'disease_cureway', 'sql': ["MATCH (m:Sym)-[r:select]->(n:Acupoint) where m.name = '头痛' return m.name, r.name, n.name"]}]))