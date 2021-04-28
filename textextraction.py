# -*- coding: utf-8 -*-
"""2021-04-24 Text Extraction.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12g45RkbnkTVWytRdBSqbw6JtEJS5aNpB
"""

pip install tika

from tika import parser # pip install tika

from google.colab import drive

drive.mount('/content/gdrive')

raw = parser.from_file('/content/gdrive/My Drive/Signavio_Test/example.pdf')

import re

print(raw['content'])

titlematches = re.findall(r'(.+Procedure[^\n]+\n)', raw['content'], flags = re.IGNORECASE)

title = titlematches[0]

print(title)

datematches = re.findall(r'(.+Date[^\n]+\n)', raw['content'], flags = re.IGNORECASE)

date = datematches[0]

print(datematches)

ownermatches = re.findall(r'(.+Owner[^\n]+\n)', raw['content'], flags = re.IGNORECASE)

print(ownermatches)

contributormatches = re.findall(r'(.+Contributor[^\n]+\n)', raw['content'], flags = re.IGNORECASE)

print(contributormatches)

def word_count(str):
    counts = dict()
    words = str.split()

    for word in words:
        if word in counts:
            counts[word] += 1
        else:
            counts[word] = 1

    return counts

raw['content'] = raw['content'].lower()
wordcounts = word_count(raw['content'])

sortedwordcounts = sorted(wordcounts.items(), key=lambda x: x[1], reverse=True)

sortedwordcounts

#check for word pairs where side by side words make one pair
text = raw['content']
words = text.split() #note that split without arguments splits on whitespace
pairs = [words[i]+' '+words[i+1] for i in range(len(words)-1)]
print(pairs)

pairedwords = dict()
for i in pairs:
  pairedwords[i]=raw['content'].count(i)

pairedwords

sortedwordpairs = sorted(pairedwords.items(), key=lambda x: x[1], reverse=True)

sortedwordpairs