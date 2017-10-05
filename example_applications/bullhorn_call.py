import os, sys
os.environ['INTERFACE_CONF_FILE'] = '/home/jjorissen/interface_secrets.conf'
from bullhorn_interface import api
from mylittlehelpers import time_elapsed
import datetime, time, re, pandas
import fire


def process_df(df):
    def remove_titles(name):
        titles = ['JR', 'MD', 'DO', 'SR', 'NP', 'PA']
        split_name = name.split(' ')
        to_remove = []
        for n in split_name:
            temp_n = n.strip().upper()
            temp_n = " ".join(re.findall("[a-zA-Z]+", n)).upper()
            if temp_n in titles:
                to_remove.append(n)
        for n in to_remove:
            split_name.remove(n)
        return ' '.join(split_name)

    def last_name(name):
        split_name = name.split(' ')
        if len(split_name) > 1:
            return split_name[-1].strip().title()

    def first_name(name):
        split_name = name.split(' ')
        if len(split_name) > 1:
            return split_name[0].strip().title()

    def inner_name(name):
        split_name = name.split(' ')
        if len(split_name) > 2:
            return ' '.join(list(map(lambda x: x.strip().title(), split_name[1:len(split_name)-1])))

    df['Contact'] = df['Contact'].fillna('')
    df['Name No Title'] = df['Contact'].apply(remove_titles)
    df['Last Name'] = df['Name No Title'].apply(last_name)
    df['First Name'] = df['Name No Title'].apply(first_name)
    df['Inner Name'] = df['Name No Title'].apply(inner_name)
    return df


def check_bullhorn(pickle_number, path_to_jar):
  pickle_path = os.path.join(path_to_jar, f'{pickle_number}')
  df = pandas.read_pickle(pickle_path)
  os.remove(pickle_path)
  df = process_df(df)
  if int(pickle_number) == 0:
    interface = api.StoredInterface(username=api.BULLHORN_USERNAME, password=api.BULLHORN_PASSWORD, independent=True)
  else:
    interface = api.StoredInterface(username=api.BULLHORN_USERNAME, password=api.BULLHORN_PASSWORD, independent=False)
  df = df.reset_index()
  df['In Bullhorn'] = ''
  start = time.time()
  for index, row in df.iterrows():
    result = interface.api_search('Candidate', lastName=row["Last Name"], firstName=row["First Name"])
    if 'data' in result.keys():
      if len(result['data'])  > 0:
        df.loc[index, 'In Bullhorn'] = True
      else:
        df.loc[index, 'In Bullhorn'] = False
    print(index, time_elapsed(start))

  df.to_pickle(pickle_path)
  print('done')


if __name__ == '__main__':
  fire.Fire(check_bullhorn)