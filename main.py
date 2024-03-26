from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import matplotlib.pyplot as plt
import pandas as pd
import spacy
import random
nlp = spacy.load("en_core_web_sm")



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hamilton.db'
db = SQLAlchemy(app)

class Lyrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_line = db.Column(db.Integer, nullable=False)
    line = db.Column(db.String(200), nullable=False)
    title = db.Column(db.Integer)
    character = db.Column(db.Integer)
    quiz = db.Column(db.Integer)
    
    cr = db.relationship('Characters', backref='lyrics', uselist=False)
    tr = db.relationship('Songs', backref='lyrics', uselist=False)
    
    
class Characters(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('lyrics.character'), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    n_lines = db.Column(db.Integer)
    n_words = db.Column(db.Integer)

    def __repr__(self):
        return f'{self.name}'

class Answers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    line = db.Column(db.String(300))
    character = db.Column(db.String(100), nullable=False)
    correct_c = db.Column(db.String(100))
    char_right = db.Column(db.Integer)
    song = db.Column(db.String(100), nullable=False)
    correct_s = db.Column(db.String(100))
    song_right = db.Column(db.Integer)


    def __repr__(self):
        return f'{self.line}'
    
class Songs(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('lyrics.title'), primary_key=True)
    song_name = db.Column(db.String(100))


class Top_words(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(50))
    quant = db.Column(db.Integer)                   # ЧТОБЫ СТРАНИЦА С ОБЩЕЙ СТАТИСТИКОЙ НЕ ГРУЗИЛАСЬ ДОЛГО, НУЖНАЯ ИНФОРМАЦИЯ 
                                                    # ПОСЧИТАНА ОДИН РАЗ И ТЕПЕРЬ ХРАНИТСЯ В ТАБЛИЦАХ
class Word_stat(db.Model):                          # ИНАЧЕ ПРИШЛОСЬ БЫ КАЖДЫЙ РАЗ ПРОХОДИТЬСЯ ПО ВСЕМУ ТЕКСТУ МЮЗИКЛА
    id = db.Column(db.Integer, primary_key=True)
    character = db.Column(db.String(50))
    word = db.Column(db.String(50))
    quant = db.Column(db.Integer)


def titles():                # ФУНКЦИЯ, КОТОРАЯ ВЫВОДИТ НАЗВАНИЯ ПЕСЕН НА ПАНЕЛЬ СБОКУ
    sor = Songs.query.all()
    titles = []
    for s in sor:
        titles.append((s.id, s.song_name))
    return titles


@app.route('/')
def base():    
    return render_template('home.html', titles=titles())

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        answr = {}
        right = []
        for i in range(1, 6):
            line = request.form[r'line_' + str(i)]
            char_info = request.form[r'guess_char' + str(i)].split('.')     # ИЗ РАДИОКНОПКИ ВОЗВРАЩАЕТСЯ НАБОР РАЗНОЙ ИНФОРМАЦИИ,
            song_info = request.form[r'guess_song' + str(i)].split('.')     # РАЗДЕЛЕННОЙ ТОЧКОЙ, ПОЭТОМУ ДЕЛАЕМ ИЗ СТРОКИ СПИСОК

            if len(char_info) == 3:
                character = char_info[0]            # ПЕРСОНАЖ, КОТОРОГО ВЫБРАЛ ПОЛЬЗОВАТЕЛЬ
                char_right = int(char_info[1])      # ПРАВИЛЬНЫЙ ОТВЕТ. С ПЕСНЯМИ ВСЕ ТО ЖЕ
                correct_c = char_info[2]            # 0 ИЛИ 1 В ЗАВИСИМОСТИ ОТ ПРАВИЛЬНОСТИ ОТВЕТА
            else:
                character = ''
                char_right = 0
                correct_c = char_info[1]
            
            
            if len(song_info) == 3:
                song = song_info[0]
                song_right = int(song_info[1])
                correct_s = song_info[2]
            else:
                song = ''
                song_right = 0
                correct_s = song_info[1]

            answr[line] = [[song, song_right], [character, char_right]]     # ЭТО ПОНАДОБИТСЯ ПРИ ВЫВЕДЕНИИ РЕЗУЛЬТАТОВ КВИЗА
            right.append([correct_s, correct_c])                            # ПОЛЬЗОВАТЕЛЮ. ЕГО ОТВЕТЫ И ПРАВИЛЬНЫЕ                  
                

            try:
                a = Answers(line=line, character=character, correct_c=correct_c, char_right=char_right,
                        song=song, correct_s=correct_s, song_right=song_right)
                db.session.add(a)
                db.session.commit()
            except:
                db.session.rollback()
                print('Ошибка добавления в базу данных')
                    
                    
        return render_template('sent.html', titles=titles(), answr=answr, right=right)
        
    else:   
        q = Lyrics.query.filter_by(quiz=1).all()                            # СТРОЧКИ, ПОДХОДЯЩИЕ ДЛЯ КВИЗА, ОТМЕЧАЛИСЬ ЕДИНИЦЕЙ
        for_quiz = {}
        for l in q:
            if l.line not in for_quiz:                                      # ПРОВЕРКА, ЧТО ЭТОЙ СТРОЧКИ ЕЩЕ НЕТ В ОТОБРАННЫХ ДЛЯ КВИЗА
                for_quiz[l.line] = {l.tr.song_name: [l.cr.name]}
            else:
                if l.tr.song_name not in for_quiz[l.line]:                  # ПРОВЕРКА, ЧТО ЭТОЙ ПЕСНИ ЕЩЕ НЕТ В ДАННЫХ ЭТОЙ СТРОЧКИ
                    for_quiz[l.line] = {l.tr.song_name: [l.cr.name]}        # (ПОДРАЗУМЕВАЕТСЯ, ЧТО СТРОКИ МОГУТ ВСТРЕЧАТЬСЯ В РАЗНЫХ ПЕСНЯХ)
                else:
                    if l.cr.name not in for_quiz[l.line][l.tr.song_name]:   # А ЕЩЕ СТРОКИ МОГУТ ПОВТОРЯТЬСЯ ВНУТРИ ОДНОЙ ПЕСНИ, ПОЭТОМУ
                        for_quiz[l.line][l.tr.song_name].append(l.cr.name)  # ТОЧНО ТАК ЖЕ ПРОВЕРЯЕМ ПЕРСОНАЖА
        
        
        quiz5 = {}
        right = []
        while len(quiz5) < 5:
            k = random.randint(0, (len(for_quiz) - 1))
            if list(for_quiz)[k] not in quiz5.keys(): 
                quiz5[list(for_quiz)[k]] = list(for_quiz[list(for_quiz)[k]].items())
                                                                # ЭТА СИСТЕМА ПОМОГАЕТ КАЖДЫЙ РАЗ РАСПОЛАГАТЬ ПРАВИЛЬНЫЕ ОТВЕТЫ
                temp_s = [[0, 0], [0, 0], [0, 0]]               # В РАЗНОМ ПОРЯДКЕ. TEMP_S - ПОРЯДОК ВАРИАНТОВ ОТВЕТОВ (1 СПИСОК
                ids1 = [0, 1, 2]                                # ВНУТРИ == 1 ВАРИАНТ). ПРАВИЛЬНЫЙ РАСПОЛАГАЕТСЯ НА МЕСТЕ t. ЧТОБЫ
                t = random.randint(0, 2)                        # ЭТО МЕСТО ПОТОМ НЕ ЗАНЯЛ НЕПРАВИЛЬНЫЙ, t УБИРАЕТСЯ ИЗ СПИСКА IDS1
                ids1.pop(t)                                     # (IDS1 СООТВЕТСТВУЮЕТ ПОЗИЦИЯМ В TEMP_S)

                temp_s[t][0] = quiz5[list(for_quiz)[k]][0][0]
                temp_s[t][1] = 1

                fs = Songs.query.filter(Songs.song_name != quiz5[list(for_quiz)[k]][0][0]).all()
                fake_1 = random.randint(0, (len(fs) - 1))       # РАНДОМНО ВЫБИРАЕТСЯ ЛЮБОЕ НАЗВАНИЕ ПЕСНИ, НЕ РАВНОЕ ВЕРНОМУ, И
                temp_s[ids1[0]][0] = fs.pop(fake_1).song_name   # РАСПОЛАГАЕТСЯ НА СВОБОДНОМ МЕСТЕ В TEMP_S (УБИРАЯСЬ ПРИ ЭТОМ ИЗ
                fake_2 = random.randint(0, (len(fs) - 1))       # СПИСКА fs, ЧТОБЫ СРЕДИ НЕПРАВИЛЬНЫХ ОТВЕТОВ НЕ БЫЛО 2 ОДИНАКОВЫХ).
                temp_s[ids1[1]][0] = fs[fake_2].song_name

                quiz5[list(for_quiz)[k]].append(temp_s)

                temp_c = [[0, 0], [0, 0], [0, 0]]               # С ВАРИАНТАМИ ОТВЕТА ДЛЯ ПЕРСОНАЖЕЙ ВСЁ РАБОТАЕТ ТОЧНО ТАК ЖЕ.
                ids2 = [0, 1, 2]
                n = random.randint(0, 2)
                ids2.pop(n)

                temp_c[n][0] = quiz5[list(for_quiz)[k]][0][1]
                temp_c[n][1] = 1

                fc = Characters.query.filter(Characters.name != ''.join(quiz5[list(for_quiz)[k]][0][1])).all()[:16]
                f1 = random.randint(0, (len(fc) - 1))
                temp_c[ids2[0]][0] = fc.pop(f1).name
                f2 = random.randint(0, (len(fc) - 1))
                temp_c[ids2[1]][0] = fc.pop(f2).name

                quiz5[list(for_quiz)[k]].append(temp_c)

                right.append([quiz5[list(for_quiz)[k]][0][0], ''.join(quiz5[list(for_quiz)[k]][0][1])]) # ВЕРНЫЙ ОТВЕТ ДОП-НО
                                                                                                        # СОХРАНЯЕМ ОТДЕЛЬНО
        return render_template('quiz.html', titles=titles(), quiz5=quiz5, right=right)


@app.route('/numbers')
def numbers():
    song_id = int(request.args.get('n'))        # ЭТОТ НОМЕР ПЕРЕДАЕТСЯ В АДРЕС СТРАНИЦЫ, ТЕМ САМЫМ ВЫБИРАЕТСЯ
    if song_id == 0:                            # ЛИБО СТРАНИЦА С НУЖНОЙ ПЕСНЕЙ ИЗ СПИСКА СБОКУ, ЛИБО СТРАНИЦА С ОБЩЕЙ СТАТИСТИКОЙ.
        name = 'Статистика по мюзиклу'          
        length = 3631
        w_sum = 24356                           # ПЕРЕМЕННЫЕ W_SUM И LENGTH БЫЛИ ЗАРАНЕЕ ПОСЧИТАНЫ (ЧТОБЫ СТРАНИЦА НЕ ГРУЗИЛАСЬ ДОЛГО),
        text = {}                               # А TEXT И TOKS ЗАЯВЛЕНЫ ПУСТЫМИ, ЧТОБЫ ПРОГРАММА НЕ ВЫДАВАЛА ОШИБКУ
        toks = 0                                # (ОНИ НУЖНЫ ДЛЯ ЧАСТИ ELSE И ПЕРЕДАЮТСЯ В HTML)

        name_list = {}
        chars = Characters.query.all()
        for c in chars:
            name_list[c.name] = [c.n_lines, c.n_words, round((c.n_lines / length) * 100, 2), round((c.n_words / w_sum) * 100, 2)]

        name_list = sorted(name_list.items(), key=lambda x: x[1], reverse=True)

        words = {}
        word_stat = Top_words.query.all()
        for w in word_stat:
            words[w.word] = [w.quant, round((w.quant / w_sum) * 100, 2)]


        # СЛЕДУЮЩИМ КУСКОМ КОДА Я ЗАПИСАЛА В СООТВЕТСТВУЮЩУЮ ТАБЛИЦУ ТОП-25 СЛОВ НА КАЖДОГО ПЕРСОНАЖА
        # ТАК КАК ЭТО НЕ ИЗМЕНЯЮЩАЯСЯ ИНФОРМАЦИЯ, ЭТА ЧАСТЬ КОДА ЗАПУСКАЛАСЬ ТОЛЬКО ОДИН РАЗ

        # for char in Characters.query.filter(Characters.n_words > 24).all():
        #     c = Lyrics.query.filter_by(character = char.id)
        #     word_stat = {}
        #     for l in c:
        #         txt = nlp(l.line)
        #         for toc in txt:
        #             if toc.lemma_ not in word_stat and not toc.is_stop and not toc.is_punct and toc.pos_ != 'PROPN' and toc.pos_ != "INTJ":
        #                 word_stat[toc.lemma_] = 1
        #             elif toc.lemma_ in word_stat and not toc.is_stop and not toc.is_punct and toc.pos_ != 'PROPN' and toc.pos_ != "INTJ":
        #                 word_stat[toc.lemma_] += 1

        #     word_stat = sorted(word_stat.items(), key=lambda x: x[1], reverse=True)[:25]


        #     for t in word_stat:
        #         try:
        #             a = Word_stat(character=char.name, word=''.join(t[0]),
        #                     quant=t[1])
        #             db.session.add(a)
        #             db.session.commit()
        #         except:
        #             db.session.rollback()
        #             print('Ошибка добавления в базу данных')
            



        
        # А ЗДЕСЬ Я ДЕЛАЛА ГРАФИКИ ДЛЯ 17 ПЕРСОНАЖЕЙ (САМЫХ ЗНАЧИМЫХ)
        # СНОВА ОДНОРАЗОВЫЙ КОД, ПОЭТОМУ БОЛЬШАЯ ЧАСТЬ ЗАКОММЕНТИРОВАНА

        # colors = ['seagreen', 'maroon', 'lightsalmon', 'skyblue', 'slateblue', 
        #           'darksalmon', 'brown', 'royalblue', 'moccasin', 'darkmagenta', 'rosybrown', 
        #           'gold', 'firebrick', 'palevioletred', 'darkolivegreen', 'mediumseagreen', 'steelblue']
            
            
        names_in_stat = []                  # ТЕМ НЕ МЕНЕЕ ЗДЕСЬ ТАКЖЕ СОЗДАЕТСЯ СПИСОК С ИМЕНАМИ,
                                            # КОТОРЫЙ ВЫВОДИТСЯ В HTML ПЕРЕД КАЖДЫМ ГРАФИКОМ. ПОЭТОМУ ОН НЕ ЗАКОММЕНТИРОВАН.
        for n in Characters.query.all():
            # fig = plt.figure(figsize=(10, 8))
            # ax = fig.add_subplot()
            if n.id < 18:
                # stat = Word_stat.query.filter_by(character = n.name).all()
                names_in_stat.append(n.name)
                
                # y = []
                # x = []
                # for s in stat:
                #     y.append(s.quant)
                #     x.append(s.word)

                # rect = ax.barh(x, y, color=colors[n.id - 1])
                # ax.bar_label(rect, fmt='{:,.0f}')
                # plt.title(n.name)
                # plt.xlabel('Сколько раз персонаж сказал слово')
                # plt.ylabel('Топ-25 слов персонажа')
                # plt.savefig(f'static/top_words{n.id}.png')

    else:
        song = Lyrics.query.order_by(Lyrics.id_line).filter_by(title = song_id)
        text = {}
        txt_df = {'name': [],
                  'lines': [],
                  'words': []}
        tokens = {}
        w_sum = 0

        for l in song:           
            if l.id_line not in text:                           # ЗДЕСЬ СОБИРАЕМ ТЕКСТ ПЕСНИ. В БАЗЕ ДАННЫХ СТРОЧКИ ПОВТОРЯЮТСЯ, ЕСЛИ
                text[l.id_line] = [l.line, [l.cr.name]]         # НЕСКОЛЬКО ПЕРСОНАЖЕЙ ПОЮТ ОДНОВРЕМЕННО (ПО ЗАПИСИ НА ПЕРСОНАЖА). НО
            else:                                               # У ТАКИХ СТРОЧЕК ОДИНАКОВЫЙ ID_LINE (!= ID), БЛАГОДАРЯ ЭТОМУ СТРОЧКИ
                text[l.id_line][1].append(l.cr.name)            # СТАКУЮТСЯ, А ПЕРСОНАЖИ К КАЖДОЙ СТРОКЕ СОБИРАЮТСЯ В СПИСОК
                                                                
            txt_df['name'].append(l.cr.name)                    # ЭТОТ СЛОВАРЬ ХРАНИТ СТРОЧКИ УЖЕ ПО-ОТДЕЛЬНОСТИ НА КАЖДОГО ПЕРСОНАЖА
            txt_df['lines'].append(l.line)                      # НУЖЕН, ЧТОБЫ ПОСЧИТАТЬ КОЛИЧЕСТВО СЛОВ И СТРОК У КАЖДОГО ИЗ НИХ
            txt_df['words'].append(0)
            for w in nlp(l.line):
                if w.pos != 'PUNCT':                            
                    txt_df['words'][-1] += 1

        for k in text.keys():
            doc = nlp(text[k][0])
            for tok in doc:
                w_sum += 1                                      # СЧИТАЕМ ОБЩЕЕ ЧИСЛО СЛОВ В ПЕСНЕ (ВКЛЮЧАЯ СТОП-СЛОВА)
                if not tok.is_punct and tok.lemma_ not in tokens and not tok.is_stop and tok.pos_ != 'PROPN' and tok.pos_ != 'INTJ':
                    tokens[tok.lemma_] = 1                      # IF СЧИТАЕТ ТОП СЛОВ В ПЕСНЕ
                elif not tok.is_punct and not tok.is_stop and tok.pos_ != 'PROPN' and tok.pos_ != 'INTJ':
                    tokens[tok.lemma_] += 1
        
        toks = sorted(tokens.items(), key=lambda x: x[1], reverse=True)[:10]

        df_stat = pd.DataFrame(txt_df)
        words = df_stat.groupby('name')['words'].sum()          # СОБИРАЕМ ТАБЛИЦУ 'ПЕРСОНАЖ - КОЛИЧЕСТВО СЛОВ В ПЕСНЕ'
        words = words.reset_index()                             
        words.columns = ['name', 'n_words']

        name_stat = df_stat['name'].value_counts().to_frame()   # ТАБЛИЦА 'ПЕРСОНАЖ - КОЛИЧЕСТВО СТРОК В ПЕСНЕ'
        name_stat = name_stat.reset_index()                     
        name_stat.columns = ['name', 'n_lines']
        name_list = name_stat.values.tolist()

        name = titles()[song_id-1][1]
        length = len(text)
        names_in_stat = {}      # СНОВА ПУСТАЯ ПЕРЕМЕННАЯ, ИСПОЛЬЗ-Я В ПРЕДЫД-Й ЧАСТИ IF. ЗДЕСЬ НУЖНА ЧТОБЫ ПРОГРАММА НЕ УПАЛА

    return render_template('numbers.html', titles=titles(), song_id=song_id, name=name, text=text, length=length, 
                           name_list=name_list, n_char=len(name_list), words=words, toks=toks, w_sum=w_sum, names_in_stat=names_in_stat) 


@app.route('/quiz_stat')
def quiz_stat():
    qs = {'characters': {}, 
          'songs' : {}}
    ans = Answers.query.all()
    for a in ans:       # ДАННЫЕ СОБИРАЮТСЯ В ФОРМАТЕ "ПРАВИЛЬНЫЙ ОТВЕТ: N_ПОПАЛОСЬ В КВИЗЕ, N_ВЫБРАНО КАК ПРАВИЛЬНЫЙ ОТВЕТ, ПРОЦЕНТ"
        if a.correct_c not in qs['characters']:
            qs['characters'][a.correct_c] = [1, a.char_right, round((a.char_right / 1) * 100, 1)]
        else:
            qs['characters'][a.correct_c][0] += 1
            qs['characters'][a.correct_c][1] += a.char_right
            qs['characters'][a.correct_c][2] = round((qs['characters'][a.correct_c][1] / qs['characters'][a.correct_c][0]) * 100, 1)
        
        if a.correct_s not in qs['songs']:
            qs['songs'][a.correct_s] = [1, a.song_right, round((a.song_right / 1) * 100, 1)]
        else:
            qs['songs'][a.correct_s][0] += 1
            qs['songs'][a.correct_s][1] += a.song_right
            qs['songs'][a.correct_s][2] = round((qs['songs'][a.correct_s][1] / qs['songs'][a.correct_s][0]) * 100, 1)

    
    q_char = sorted(qs['characters'].items(), key=lambda x: x[1][2], reverse=True)
    q_songs = sorted(qs['songs'].items(), key=lambda x: x[1][2], reverse=True)

    for char in q_char:                     # ЦИКЛ СОЗДАЕТ ГРАФИКИ ПО ПЕРСОНАЖАМ В КВИЗЕ
        fig = plt.figure(figsize=(6, 4))
        ax = fig.add_subplot()
        data = [char[1][1], char[1][0] - char[1][1]]
        labels = [f'Угадали ({char[1][1]})', f'Не угадали ({char[1][0] - char[1][1]})']
        colors = ['mediumseagreen', 'indianred']

        ax.pie(data, colors=colors, autopct='%.2f%%')
        plt.title(char[0])
        plt.legend(labels, loc='upper right')
        plt.savefig(f'static/char_guess_{char[0]}.png')

    for son in q_songs:                     # ЦИКЛ СОЗДАЕТ ГРАФИКИ ПО ПЕСНЯМ В КВИЗЕ
        fig = plt.figure(figsize=(6, 4))
        ax = fig.add_subplot()
        data = [son[1][1], son[1][0] - son[1][1]]
        labels = [f'Угадали ({son[1][1]})', f'Не угадали ({son[1][0] - son[1][1]})']
        colors = ['mediumseagreen', 'indianred']

        ax.pie(data, colors=colors, autopct='%.2f%%')
        plt.title(son[0])
        plt.legend(labels, loc='upper right')
        plt.savefig(f'static/song_guess_{son[0]}.png')

   

    return render_template('quiz_stat.html', titles=titles(), q_char=q_char, q_songs=q_songs)

if __name__ == '__main__':
    # СЛЕДУЮЩИЕ 2 СТРОЧКИ НУЖНО ЗАПУСКАТЬ ТОЛЬКО 1 РАЗ ДЛЯ СОЗДАНИЯ БАЗЫ ДАННЫХ

    # with app.app_context():
    #     db.create_all()
    app.run()
