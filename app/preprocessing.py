from pymorphy2 import MorphAnalyzer

puncts = ''
morph = MorphAnalyzer()


def del_puncts(text, puncts=puncts):
    return ''.join([symbol if symbol not in puncts else ' ' for symbol in text.replace('\t', ' ').replace('\n', ' ')])


def get_tokens(text, morph=morph):
    return ' '.join([morph.parse(word)[0].normal_form for word in text.split() if word != ''])
