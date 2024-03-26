# ЭТОТ КОД ИСПОЛЬЗОВАТЬ ТОЛЬКО ОДИН РАЗ ДЛЯ ЗАПИСИ В ТАБЛИЦУ

import pandas as pd
import re
import sqlite3 as sql

from pyparsing import Regex 


df = pd.read_csv('ham_lyrics.csv', sep=';', usecols=['title', 'speaker', 'line'])
# print(df)


def find_lines(name, id):
    df_name = pd.DataFrame(columns = ['id_line', 'line', 'title', 'character'])
    for i, row in df.iterrows():
        mark = re.search(name, row['speaker'])
        n_mark = re.search(r'EXCEPT.+' + name, row['speaker'])
        if mark  and not n_mark:
            df_name.loc[len(df_name.index)] = [i, row['line'], row['title'], id]
        
    return df_name, name

def line_distrib(df_name):
    return df_name['title'].value_counts()

ham_lines, ham = find_lines(r'HAMILTON', 1)
burr_lines, burr = find_lines(r'BURR', 2)
ang_lines, angel = find_lines(r'ANGELICA', 3)
el_lines, eliza = find_lines(r'ELIZA', 4)
laf_lines, laf = find_lines(r'LAFAYETTE', 5)
laur_lines, laur = find_lines(r'LAURENS', 6)
mul_lines, mul = find_lines(r'MULLIGAN', 7)
wash_lines, wash = find_lines(r'WASHINGTON', 8)
peg_lines , peggy = find_lines(r'PEGGY', 9)
jef_lines, jef = find_lines(r'JEFFERSON', 10)
mad_lines, mad = find_lines(r'MADISON', 11)
king_lines, king = find_lines(r'KING GEORGE', 12)
maria_lines, maria = find_lines(r'MARIA', 13)
comp_lines, comp = find_lines(r'COMPANY', 14)
men_lines, men = find_lines(r'MEN', 15)
women_lines, women = find_lines(r'WOMEN', 16)
phil_lines, phil = find_lines(r'PHILIP', 17)
lee_l, lee = find_lines(r'LEE', 18)
doc_l, doc = find_lines(r'DOCTOR', 19)
seab_l, seab = find_lines(r'SEABURY', 20)
mart_l, marth = find_lines(r'MARTHA', 21)
dol_l, dol = find_lines(r'DOLLY', 22)
crowd_l, crowd = find_lines(r'CROWD', 23)
rey_l, rey = find_lines(r'JAMES REYNOLDS', 24)
eack_l, eack = find_lines(r'GEORGE EACKER', 25)
voters_l, voters = find_lines(r'VOTERS', 26)
mvot1_l, mvot1 = find_lines(r'MALE VOTER 1', 27)
mvot2_l, mvot2 = find_lines(r'MALE VOTER 2', 28)
fvot1_l, fvot1 = find_lines(r'FEMALE VOTER 1', 29)
fvot2_l, fvot2 = find_lines(r'FEMALE VOTER 2', 30)
rec_samp_l, rec_samp = find_lines(r'Recorded Samples', 31)


df_2 = pd.concat([ham_lines, burr_lines, ang_lines, el_lines, laf_lines, laur_lines, mul_lines,
                wash_lines, peg_lines, jef_lines, mad_lines, king_lines, maria_lines, comp_lines, men_lines, women_lines, 
                phil_lines, lee_l, doc_l, seab_l, mart_l, dol_l, crowd_l, rey_l, eack_l, voters_l, 
                mvot1_l, mvot2_l, fvot1_l, fvot2_l, rec_samp_l], ignore_index=True)
print(df_2)
df_3 = df_2.sort_values(by='id_line', ascending=True)
print(df_3)
con = sql.connect('instance/hamilton.db')


# df_3.to_sql(
#     name = 'lyrics',
#     con = con,
#     schema=None,
#     if_exists='append',
#     index=False,
#     index_label='id',
#     chunksize=None,
#     dtype=None,
#     method=None
# )