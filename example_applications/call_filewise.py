import os
import pandas
import subprocess
import fire
import math
import time
import sys
import re


def consolidate_when_done(path_to_jar, num_terms):
    done = False
    time.sleep(5)
    while not done:
        if len(os.listdir(path_to_jar)) >= num_terms:
            final_df = pandas.DataFrame()
            for file in os.listdir(path_to_jar):
                final_df = final_df.append(pandas.read_pickle(os.path.join(path_to_jar, file)))
            final_df.to_excel(os.path.join(path_to_jar, 'sorted.xlsx'))
            done = True
        else:
            consolidate_when_done(path_to_jar, num_terms)


def term_call(call_file="bullhorn_call.py", excel_file='/home/jjorissen/Documents/BullhornActDocs/EM.xlsx',
              path_to_jar='../ACT_EM_pickle_jar', num_terms=5):
    file = os.path.abspath(excel_file)
    path_to_jar = os.path.abspath(path_to_jar)
    for file in os.listdir(path_to_jar):
        os.remove(os.path.join(path_to_jar, file))

    try:
        df = pandas.read_excel(file)
    except:
        df = pandas.read_csv(file)

    df = df.reset_index()
    slice_length = math.ceil(df.shape[0] / num_terms)
    dfs = []
    for i in range(num_terms):
        beginning = i * slice_length + (1 if i else 0)
        ending = (i + 1) * slice_length
        dfs.append(df.iloc[beginning:ending])

    for i in range(len(dfs)):
        dfs[i].to_pickle(os.path.join(path_to_jar, f'{i}'))

    for i in range(num_terms):
        subprocess.Popen(['xterm', '-T', f"{i} {call_file}",
                          '-n', f"{i} {call_file}",
                          '-hold', '-e', 'python',
                          f'{call_file}',
                          f'--pickle_number', f'{i}',
                          f'--path_to_jar', f'{path_to_jar}'])

    consolidate_when_done(path_to_jar, num_terms)

if __name__ == "__main__":
    fire.Fire(term_call)
