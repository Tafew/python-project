import spacy
from nltk.tokenize import sent_tokenize
import string
import pandas
import math
import re
from collections import Counter
import pylev
from math import sqrt, pow
import numpy
import datetime
import openpyxl
import pandas as pd

nlp = spacy.load("en_core_web_sm")


def squared_sum(x):
    """ return 3 rounded square rooted value """
    return round(sqrt(sum([a * a for a in x])), 3)


def euclidean_distance(x, y):
    """ return euclidean distance between two lists """
    return sqrt(sum(pow(a - b, 2) for a, b in zip(x, y)))


WORD = re.compile(r"\w+")


def get_cosine(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
    sum2 = sum([vec2[x] ** 2 for x in list(vec2.keys())])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator


def text_to_vector(text):
    words = WORD.findall(text)
    return Counter(words)


def jaccard_similarity(x, y):
    """ returns the jaccard similarity between two lists """
    intersection_cardinality = len(set.intersection(*[set(x), set(y)]))
    union_cardinality = len(set.union(*[set(x), set(y)]))
    return intersection_cardinality / float(union_cardinality)


def cleaning(text):
    exclude = set(string.punctuation)
    exclude.remove('@')

    # remove new line and digits with regular expression
    text = re.sub(r'\n', '', text)
    text = re.sub(r'\d', '', text)

    # remove patterns matching url format
    url_pattern = r'((http|ftp|https):\/\/)?[\w\-]+(\.[\w\-]+)+([\w\-\.,@?^=%&amp;:/\+#]*[\w\-\@?^=%&amp;/\+#])?'
    text = re.sub(url_pattern, ' ', text)

    # remove non-ascii characters, all below the ordinal coding of 8000 are allowed, so times all emojis gone
    text = ''.join(character for character in text if ord(character) < 8000)

    # remove punctuations # unfortunately the @ sign goes with it, so explicitly remove the @ sign from the
    # exclude list
    text = ''.join(character for character in text if character not in exclude)

    # standardize white space
    text = re.sub(r'\s+', ' ', text)

    # drop capitalization
    text = text.lower()
    # now remove all twitter usernames, they have the structure @username,
    # so explicitly leave the @ above to identify the usernames
    text = re.sub('@[^\s]+', '', text)

    # remove white space, this is the last step, because after removing the
    # usernames there are often empty characters left
    text = text.strip()

    return text


def sentence_extractor(string_):
    sentences_list = []
    data = sent_tokenize(string_)
    for sentence in data:
        txt = ""
        sentence = re.sub('<[^>]+>', '', sentence).strip()
        if "Von:" not in sentence and \
                "An:" not in sentence and \
                "From:" not in sentence and \
                "Web:" not in sentence and \
                len(sentence.split()) < 30:
            for word in sentence.split():
                if word[0].isalpha() and \
                        ("@" not in word) and \
                        (".com" not in word) and \
                        ("http" not in word) and \
                        ("www" not in word) and \
                        len(word) < 24:
                    pass
                else:
                    word = ""
                txt += " {}".format(word).replace(":", "")
        if txt and len(txt.split()) > 2 and (txt[-1] == "!" or txt[-1] == "." or txt[-1] == "?"):
            txt = cleaning(txt)
            sentences_list.append(txt.strip())
    return sentences_list


def sentence_formatting(_input, _output):
    email_num = 0
    data = pd.read_csv(_input)
    data_lines = data.values.tolist()
    line_num = 0
    print("sentence_formatting function is running")
    for line in data_lines:
        try:
            for i in sentence_extractor(line[4]):
                try:
                    if line_num % 500 == 0:
                        print(f"Sorted and formatted sentences {line_num}")
                    line_num += 1
                    doc = nlp(str(i))
                    propn = 0
                    #               propn: proper noun
                    verb = 0
                    #               verb:  Word used to describe an action
                    adj = 0
                    #               adjective: A word naming an attribute of a noun, such as sweet, red
                    noun = 0
                    #               noun: A word used to identify any of a class of people, places, or things
                    for token in doc:
                        if token.pos_ == "PROPN":
                            propn += 1
                        elif token.pos_ == "VERB":
                            verb += 1
                        elif token.pos_ == "ADJ":
                            adj += 1
                        elif token.pos_ == "NOUN":
                            noun += 1
                    finished_line = f"{email_num}," \
                                    f"DateTime: {line[0]}," \
                                    f" From: {line[1]}," \
                                    f" To: {line[2]}," \
                                    f" Sentence:  {i.strip()}," \
                                    f" PROPN: {propn}," \
                                    f" VERB: {verb}," \
                                    f" ADJ: {adj}," \
                                    f" NOUN: {noun}," \
                                    f"{line[3]}\n"
                    with open(_output, "a", encoding="charmap") as a:
                        a.write(finished_line)
                except:
                    pass
        except:
            pass
        email_num += 1


def grouping_sentences(_input, _output):
    sen = []
    print("grouping_sentences function is running")
    line_num = 0
    with open(_input, "r", encoding="charmap") as d:
        data_lines = d.readlines()
        for line in data_lines:
            sentences = []
            if line_num % 500 == 0:
                print(f"Grouping is up to {line_num} lines")
            line_num += 1
            for line_2 in data_lines:
                if jaccard_similarity(line.split(",")[4].split(), line_2.split(",")[4].split()) > 0.2:
                    if line_2.split(',')[4] not in sen:
                        try:
                            sentences.append(f"{line.split(',')[0]},"
                                             f"{jaccard_similarity(line.split(',')[4].split(), line_2.split(',')[4].split())},"
                                             f"{get_cosine(text_to_vector(line.split(',')[4]), text_to_vector(line_2.split(',')[4]))},"
                                             f"{pylev.levenshtein(line.split(',')[4].split(), line_2.split(',')[4].split())},"
                                             f"{euclidean_distance(nlp(line.split(',')[4]).vector, nlp(line_2.split(',')[4]).vector)},"
                                             f"{line_2}\n")
                            sen.append(line_2.split(',')[4])
                        except:
                            pass
            if len(sentences) > 1:
                for sentence in sentences:
                    with open(_output, "a", encoding="charmap") as writer:
                        writer.write(sentence)


def test_function(_input, _output, number_of_sentences):
    sen = []
    begin_time = datetime.datetime.now()
    print("grouping_sentences function is running")
    line_num = 0
    with open(_input, "r", encoding="charmap") as d:
        data_lines = d.readlines()
        num_of_sentances = 0;
        for line in data_lines:
            sentences = []
            num_of_sentences_in_group = 0
            if num_of_sentances >= number_of_sentences:
                time_for_running = datetime.datetime.now() - begin_time
                print(
                    f"{int(number_of_sentences / time_for_running.total_seconds() * 60)} sentences per minute are grouped")
                print(f"{int(number_of_sentences / time_for_running.total_seconds())} sentences per second are grouped")
                break
            line_num += 1
            for line_2 in data_lines:
                if jaccard_similarity(line.split(",")[4].split(), line_2.split(",")[4].split()) > 0.2:
                    if line_2.split(',')[4] not in sen:
                        try:
                            sentences.append(f"{line.split(',')[0]},"
                                             f"{jaccard_similarity(line.split(',')[4].split(), line_2.split(',')[4].split())},"
                                             f"{get_cosine(text_to_vector(line.split(',')[4]), text_to_vector(line_2.split(',')[4]))},"
                                             f"{pylev.levenshtein(line.split(',')[4].split(), line_2.split(',')[4].split())},"
                                             f"{euclidean_distance(nlp(line.split(',')[4]).vector, nlp(line_2.split(',')[4]).vector)},"
                                             f"{line_2}\n")
                            sen.append(line_2.split(',')[4])
                            num_of_sentences_in_group += 1

                        except:
                            pass
            if len(sentences) > 1:
                num_of_sentances += num_of_sentences_in_group
                for sentence in sentences:
                    with open(_output, "a", encoding="charmap") as writer:
                        writer.write(sentence)


def write_sentences_in_excel(input_, output_):
    print("write_sentences_in_excel function is running")
    with open(input_, "r", encoding="charmap") as d:
        number_of_sentences = 1
        sentences = d.readlines()
        emails = [sentences[0].split(",")[7].replace('"', "").replace("From:", "").replace('"', "").strip().lower(),
                  sentences[0].split(",")[8].replace('"', "").replace("To:", "").replace('"', '').strip().lower()]
        db = pandas.DataFrame({
            "date":
                [sentences[0].split(",")[6].replace('"', "").replace("DateTime:", "")],
            "email_id": [sentences[0].split(",")[0].replace('"', "")],
            "from(email index)": [
                emails.index(
                    sentences[0].split(",")[7].replace('"', "").replace("From:", "").replace('"', "").strip().lower()
                )],
            "to(email index)": [
                emails.index(
                    sentences[0].split(",")[8].replace('"', "").replace("To:", "").replace('"', '').strip().lower()
                )],
            "sentence": [sentences[0].split(",")[9].replace("Sentence:", "").strip()],
            "propn": [sentences[0].split(",")[10].replace("PROPN:", "")],
            "verb": [sentences[0].split(",")[11].replace("VERB:", "")],
            "adjective": [sentences[0].split(",")[12].replace("ADJ:", "")],
            "noun": [sentences[0].split(",")[13].replace("NOUN:", "")],
            "jaccard_similarity": [numpy.round(float(sentences[0].split(",")[1]), 4)],
            "cosine_similarity": [numpy.round(float(sentences[0].split(",")[2]), 4)],
            "levenshtein_distance": [sentences[0].split(",")[3]],
            "euclidean_distance": [numpy.round(float(sentences[0].split(",")[4]), 4)]

        })
        writer = pandas.ExcelWriter(output_, engine='xlsxwriter')
        db = db[
            [
                "date", "email_id", "from(email index)",
                "to(email index)", "sentence", "propn",
                "verb", "adjective", "noun",
                "jaccard_similarity", "cosine_similarity",
                "levenshtein_distance", "euclidean_distance"
            ]
        ]
        num = 0
        number_of_sentences = 1
        for sentence in sentences:
            try:
                if sentences[0] != sentence:
                    email_1 = sentence.split(",")[7].replace('"', "").replace("From:", "").replace('"',
                                                                                                   '').strip().lower()
                    if ";" in email_1:
                        email_1 = email_1.split(';')[0].strip()
                    email_2 = sentence.split(",")[8].replace('"', "").replace("To:", "").replace('"',
                                                                                                 '').strip().lower()
                    if ";" in email_2:
                        email_2 = email_2.split(';')[0].strip()
                    if email_1 not in emails:
                        emails.append(email_1)
                    if email_2 not in emails:
                        emails.append(email_2)
                    new_db = pandas.DataFrame({
                        "date": [sentence.split(",")[6].replace('"', "").replace("DateTime:", "")],
                        "email_id": [sentence.split(",")[0].replace('"', "")],
                        "from(email index)": [
                            emails.index(email_1)
                        ],
                        "to(email index)": [
                            emails.index(email_2)
                        ],
                        "sentence": [sentence.split(",")[9].replace("Sentence:", "").strip()],
                        "propn": [sentence.split(",")[10].replace("PROPN:", "")],
                        "verb": [sentence.split(",")[11].replace("VERB:", "")],
                        "adjective": [sentence.split(",")[12].replace("ADJ:", "")],
                        "noun": [sentence.split(",")[13].replace("NOUN:", "")],
                        "jaccard_similarity": [numpy.round(float(sentence.split(",")[1]), 4)],
                        "cosine_similarity": [numpy.round(float(sentence.split(",")[2]), 4)],
                        "levenshtein_distance": [sentence.split(",")[3]],
                        "euclidean_distance": [numpy.round(float(sentence.split(",")[4]), 4)]

                    })
                    if number_of_sentences % 100 == 0:
                        print(f"{number_of_sentences} sentences are recorded")
                    db = pandas.concat([db, new_db], ignore_index=True, axis=0)
                    num += 1
                    number_of_sentences += 1
            except:
                pass
        db.to_excel(writer, sheet_name='Sheet1', startrow=1, header=False, index=False)
        worksheet = writer.sheets['Sheet1']
        (max_row, max_col) = db.shape
        column_settings = [{'header': column} for column in db.columns]
        worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})
        worksheet.set_column(0, max_col - 1, 12)
        writer.save()
        number_of_emails = 1
        db_2 = pandas.DataFrame({
            "index": [emails.index(emails[0])],
            "email": [emails[0]]
        })
        new_writer = pandas.ExcelWriter("tbl_email_address.xlsx", engine='xlsxwriter')
        db_2 = db_2[
            ["index", "email"]
        ]
        num = 0
        for email in emails:
            try:
                if number_of_emails % 100 == 0:
                    print(f"{number_of_emails} email addresses are recorded")
                number_of_emails += 1
                new_db_2 = pandas.DataFrame({
                    "index": [emails.index(email)],
                    "email": [email]
                })
                db_2 = pandas.concat([db_2, new_db_2], ignore_index=True, axis=0)
                num += 1
            except:
                pass
        db_2.to_excel(new_writer, sheet_name='Sheet1', startrow=1, header=False, index=False)
        worksheet = new_writer.sheets['Sheet1']
        (max_row, max_col) = db_2.shape
        column_settings = [{'header': column} for column in db_2.columns]
        worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})
        worksheet.set_column(0, max_col - 1, 12)
        new_writer.save()

        sentence_list = []
        email_ids = []
        email_ids.append(sentences[0].split(",")[0].replace('"', ""))
        for s in sentences:
            if sentences[0].split(",")[0].replace('"', "") == s.split(",")[0].replace('"', "") and s.split(",")[
                9].replace(
                "Sentence:", "").strip() not in sentence_list:
                sentence_list.append(s.split(",")[9].replace("Sentence:", "").strip())
        email_1 = sentences[0].split(",")[7].replace('"', "").replace("From:", "").replace('"',
                                                                                           '').strip().lower()
        if ";" in email_1:
            email_1 = email_1.split(';')[0].strip()
        email_2 = sentences[0].split(",")[8].replace('"', "").replace("To:", "").replace('"',
                                                                                         '').strip().lower()
        if ";" in email_2:
            email_2 = email_2.split(';')[0].strip()
        db_3 = pandas.DataFrame({
            "email_id": [sentences[0].split(",")[0].replace('"', "")],
            "email_date": [sentences[0].split(",")[6].replace('"', "").replace("DateTime:", "").split()[0]],
            "email_time": [sentences[0].split(",")[6].replace('"', "").replace("DateTime:", "").split()[1]],
            "email_subject": [sentences[0].split(",")[14]],
            "from_id": [
                emails.index(email_1)
            ],
            "to_id": [
                emails.index(email_2)
            ],
            "body": [str(sentence_list).replace("]", "").replace("[", "")]
        })
        new_writer_1 = pandas.ExcelWriter("tbl_email.xlsx", engine='xlsxwriter')
        db_3 = db_3[
            ["email_id", "email_date", "email_time", "email_subject", "from_id", "to_id", "body"]
        ]
        num = 0
        for sentence in sentences:
            sentence_list = []
            try:
                if sentence.split(",")[0].replace('"', "") not in email_ids:
                    email_ids.append(sentence.split(",")[0].replace('"', ""))
                    for s in sentences:
                        if sentence.split(",")[0].replace('"', "") == s.split(",")[0].replace('"', "") and s.split(",")[
                            9].replace("Sentence:", "").strip() not in sentence_list:
                            sentence_list.append(s.split(",")[9].replace("Sentence:", "").strip())
                    if sentences[0] != sentence:
                        email_1 = sentence.split(",")[7].replace('"', "").replace("From:", "").replace('"',
                                                                                                       '').strip().lower()
                        if ";" in email_1:
                            email_1 = email_1.split(';')[0].strip()
                        email_2 = sentence.split(",")[8].replace('"', "").replace("To:", "").replace('"',
                                                                                                     '').strip().lower()
                        if ";" in email_2:
                            email_2 = email_2.split(';')[0].strip()
                        new_db_3 = pandas.DataFrame({
                            "email_id": [sentence.split(",")[0].replace('"', "")],
                            "email_date": [sentence.split(",")[6].replace('"', "").replace("DateTime:", "").split()[0]],
                            "email_time": [sentence.split(",")[6].replace('"', "").replace("DateTime:", "").split()[1]],
                            "email_subject": [sentence.split(",")[14]],
                            "from_id": [
                                emails.index(email_1)
                            ],
                            "to_id": [
                                emails.index(email_2)
                            ],
                            "body": [str(sentence_list).replace("]", "").replace("[", "")]
                        })
                        db_3 = pandas.concat([db_3, new_db_3], ignore_index=True, axis=0)
                        num += 1
            except:
                pass
        db_3.to_excel(new_writer_1, sheet_name='Sheet1', startrow=1, header=False, index=False)
        worksheet = new_writer_1.sheets['Sheet1']
        (max_row, max_col) = db_3.shape
        column_settings = [{'header': column} for column in db_3.columns]
        worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})
        worksheet.set_column(0, max_col - 1, 12)
        new_writer_1.save()


def communication_streams(input_, output_):
    data = pd.read_excel(input_)
    list = data.values.tolist()
    sorted_list = []
    com_s = 0
    sorted_communication_stream = []
    for i in list:
        for j in list:
            if (i[4] == j[4] or j[4] == j[5]) and (i[5] == j[5] or i[5] == j[4]) and j[
                0] not in sorted_communication_stream:
                sorted_list.append((com_s, j))
                sorted_communication_stream.append(j[0])
        com_s += 1
    db = pandas.DataFrame({
        "id": [sorted_list.index(sorted_list[0])],
        "comm_stream_id": [sorted_list[0][0]],
        "email_id": [sorted_list[0][1][0]]
    })
    new_writer_1 = pandas.ExcelWriter(output_, engine='xlsxwriter')
    db = db[
        ["id", "comm_stream_id", "email_id"]
    ]
    num = 0
    for comunication_stream in sorted_list:
        if comunication_stream != sorted_list[0]:
            try:
                new_db = pandas.DataFrame({
                    "id": [sorted_list.index(comunication_stream)],
                    "comm_stream_id": [comunication_stream[0]],
                    "email_id": [comunication_stream[1][0]],

                })
                db = pandas.concat([db, new_db], ignore_index=True, axis=0)
                num += 1
            except:
                pass
    db.to_excel(new_writer_1, sheet_name='Sheet1', startrow=1, header=False, index=False)
    worksheet = new_writer_1.sheets['Sheet1']
    (max_row, max_col) = db.shape
    column_settings = [{'header': column} for column in db.columns]
    worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})
    worksheet.set_column(0, max_col - 1, 12)
    new_writer_1.save()


def old_sentence_formatting(_input, _output):
    email_num = 0
    with open(_input, "r", encoding="charmap") as data:
        data_lines = data.readlines()
        line_num = 0
        print("sentence_formatting function is running")
        for line in data_lines:
            try:
                for i in sentence_extractor(line.split(",")[4]):
                    try:
                        if line_num % 500 == 0:
                            print(f"Sorted and formatted sentences {line_num}")
                        line_num += 1
                        doc = nlp(str(i))
                        propn = 0
                        #               propn: proper noun
                        verb = 0
                        #               verb:  Word used to describe an action
                        adj = 0
                        #               adjective: A word naming an attribute of a noun, such as sweet, red
                        noun = 0
                        #               noun: A word used to identify any of a class of people, places, or things
                        for token in doc:
                            if token.pos_ == "PROPN":
                                propn += 1
                            elif token.pos_ == "VERB":
                                verb += 1
                            elif token.pos_ == "ADJ":
                                adj += 1
                            elif token.pos_ == "NOUN":
                                noun += 1
                        finished_line = f"{email_num}," \
                                        f"DateTime: {line.split(',')[0]}," \
                                        f" From: {line.split(',')[1]}," \
                                        f" To: {line.split(',')[2]}," \
                                        f" Sentence:  {i.strip()}," \
                                        f" PROPN: {propn}," \
                                        f" VERB: {verb}," \
                                        f" ADJ: {adj}," \
                                        f" NOUN: {noun}," \
                                        f"{line.split(',')[3]}\n"
                        with open(_output, "a", encoding="charmap") as a:
                            a.write(finished_line)
                    except:
                        pass
            except:
                pass
            email_num += 1


def final_function(_input, _output):
    try:
        sentence_formatting(_input, "file.txt")
    except:
        old_sentence_formatting(_input, "file.txt")
    grouping_sentences("file.txt", "sentence_in_groups.txt")
    write_sentences_in_excel("sentence_in_groups.txt", _output)
    communication_streams('tbl_email.xlsx', 'tbl_communication_stream.xlsx')

final_function("data.csv", "tbl_sentence.xlsx")