import pandas as pd
from urllib.request import urlopen
from urllib.error import HTTPError
import re

class txtFetcher(object):
    """
    docstring tbd
    """
    def __init__(self):
        self.encoding = ["utf-8", "ISO-8859-1", "latin1"]
        self.encoding_idx = 0 # default value
        self.encoding_final = self.encoding[self.encoding_idx] # default value
        self.flag_final = False
        self.flag_encoding = False
        self.lines_list = []
        self.first_line = False

    def verify_url(self, url):
        """
        check if an url belongs to offene-daten-konstanz.de
        """
        return "offenedaten-konstanz.de" in url

    def get_file_ending(self, url):
        """
        extract file ending from an url
        """
        return url.split(".")[::-1][0]

    def get_encoding(self, file):
        """
        extract encoding from first line if applicable
        """
        try:
            first_line = file.readline().decode(self.encoding[self.encoding_idx])
        except:
            print("false encoding")
            self.flag_encoding = True
            if self.encoding_idx < len(self.encoding)-1:
                self.encoding_idx += 1
                self.get_encoding(file)
            else:
                print("no matching encoding found. please review")

        if re.findall("encoding", first_line):
            self.first_line = True
            for i in re.finditer("encoding", first_line):
                text = first_line[i.end():]
                self.encoding_final = str(re.findall('"([^"]*)"', text)[0]).strip('[]')

    def read_line(self, line):
        """
        read single line
        """
        decoded_line = line.decode(self.encoding_final)
        for quoted_part in re.findall(r'\"(.*?)\"', decoded_line):  # replace 'space' in quotes with '@'
            decoded_line = decoded_line.replace(quoted_part, quoted_part.replace(" ", "@"))
        split_lines = decoded_line.split(' ')
        for i in range(len(split_lines)):
            for quoted_part in re.findall(r'\"(.*?)\"',
                                          split_lines[i]):  # replace '@' in quotes with 'space'
                split_lines[i] = split_lines[i].replace(quoted_part, quoted_part.replace("@", " "))
        self.lines_list.append(split_lines)

    def get_data(self, url):

        try:
            file = urlopen(url)
        except HTTPError:
            print("could not open url")
            self.flag_final = True

        if self.flag_final == False:
            try:
                self.get_encoding(file)
                self.encoding_idx = 0 # reset to default value
                for line in file:
                    try:
                        self.read_line(line)
                    except Exception as read_error:
                        print("false encoding")
                        self.flag_encoding = True
                        if self.encoding_idx < len(self.encoding) - 1:
                            self.encoding_idx += 1
                            self.encoding_final = self.encoding[self.encoding_idx]
                            self.read_line(line)
                        else:
                            print("no matching encoding found. please review")

            except:
                self.flag_final = True

            return self.lines_list

    def convert_df(self, data):

        df = pd.DataFrame(data)
        row, col = df.shape
        drop_cols = []
        for i in range(col):
            if not df.iloc[:,i].str.contains("=").any(): # if col does not contain data
                drop_cols.append(i)
        if len(drop_cols) != 0:
            df = df.drop(drop_cols, axis=1)  # drop respective cols

        row, col = df.shape
        col_name_ref = ''  # default value
        col_names = []

        for j in range(col):  # get col names and extract values
            for i in range(row):
                if i == 0:
                    col_name_ref = df.iloc[i, j].split("=")[0] # get col name
                split_element = df.iloc[i, j].split("=")
                col_name = split_element[0]

                if j == (col - 1): # handling last col
                    value = split_element[1].split("/>")[0][1:-1]
                else:
                    value = split_element[1][1:-1]

                if col_name_ref != col_name: # case of different col names
                    print("column names do not match. please review error")
                    break

                if value == "": # handling missing data
                    df.iloc[i, j] = "NaN"
                else:
                    df.iloc[i, j] = value

            col_names.append(col_name_ref)
        df.columns = col_names

        return df

    def load_data(self, url):

        if self.verify_url(url) and self.get_file_ending(url) == "txt":
            data = self.get_data(url)
        else:
            print(f"> 3rd-Party Url/Dataset detected and therefore skipped:\n> {url}")
        return self.convert_df(data), self.flag_final

url = "https://offenedaten-konstanz.de/sites/default/files/FAHRPLAENE.txt"
#url = "https://offenedaten-konstanz.de/sites/default/files/FAHRTEN.Txt" # dauert ca 1 min
#url = "https://offenedaten-konstanz.de/sites/default/files/FAHRTHALTEZEITEN.txt"
#url = "https://offenedaten-konstanz.de/sites/default/files/FAHRWEGE.txt"
#url = "https://offenedaten-konstanz.de/sites/default/files/FAHRZEITEN.txt"
#url = "https://offenedaten-konstanz.de/sites/default/files/FIRMENKALENDER.txt"
#url = "https://offenedaten-konstanz.de/sites/default/files/LINIEN.txt"
#url = "https://offenedaten-konstanz.de/sites/default/files/ORTE.txt"
#url = "https://offenedaten-konstanz.de/sites/default/files/VERBINDUNGEN.txt"

dsf_txt = txtFetcher()
result, flag = dsf_txt.load_data(url)
print(flag)
print(result)