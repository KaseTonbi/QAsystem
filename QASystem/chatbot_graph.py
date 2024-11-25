
from question_parser import *
from question_classifier import *
from answer_search import *

''' 问答类'''
class ChatBotGraph:
    def __init__(self):
        self.classifier = QuestionClassifiler()
        self.parser = QuestionParser()
        self.searcher = AnswerSearcher()
    def chat_main(self,sent):
        answer = '您好，这个问题未查询到'
        res_classify = self.classifier.classify(sent) #✔
        # print(res_classify)  {'args': {'头痛': ['disease']}, 'question_types': ['disease_cureway']}
        if not res_classify:
            return answer
        res_sql = self.parser.parser_main(res_classify)
        # print(res_sql)
        final_answers = self.searcher.serch_main(res_sql)
        # print(final_answers)
        if not final_answers:
            return answer
        else:
            return '\n'.join(final_answers)
if __name__=='__main__':
    handler = ChatBotGraph()
    print("您好，我是中医针灸智能助理小诺")
    while 1:
        question = input('用户：')
        answer = handler.chat_main(question)
        print('小诺：',answer)