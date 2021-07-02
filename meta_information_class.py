import nltk, re, string, collections, spacy
from tika import parser 
from collections import Counter
from datetime import datetime, date
import pandas as pd
from nltk.util import ngrams
import datefinder
import pprint
import itertools    


class extract_meta_information():
    def __init__(self, file):
        """
        Params:
        text = process document as string
        keywords_list = most common keywords to identify process name, documents and date (based on keywords matrix)
        """
        self.text = parser.from_file(file)['content']
        self.keywords_names_list = ['procedure', 'process', 'sop', 'policy', 'manual', 'step']
        self.keywords_description_list = ['introduction', 'purpose', 'scope']
        self.keywords_docs_list = ['purchase', 'order', 'form', 'request', 'invoice', 'documents', 'document', 'documentation']
        self.keywords_date_list = ['issued date','issue-date','effective-date', 'implementation-date','updated', 'adopted' ,'revised',"review date","revision date","version","last revision","issued","effective date","date"]

        
    def preprocessing_text_date(self):
        cleaned_text = self.text.strip()
        cleaned_text = cleaned_text.replace('  ', '')
        cleaned_text = cleaned_text.replace(' \n',' ')
        cleaned_text = cleaned_text.lower()

        return cleaned_text

    def calcu (self, df_date):
        # This function is used to find date from the string
        #cleaned_text = self.preprocessing_text_date()
        matches = datefinder.find_dates(df_date)
        for match in matches:
            return match

    #Process Name
    def process_name_keywords(self):
        # search process name based on selected keywords from keywords_list
        # regex: line containing keyword, line break
        try: 
            self.name_keywords = re.search(r'(.+({})[^\n])'.format('|'.join(self.keywords_names_list)), self.text, re.IGNORECASE).group(1)
            return(self.name_keywords)
        except:
            #print("Keywords not found in document")
            pass
            
    def process_name_title(self):
        # search process name based on keyword 'Title'
        # regex: Title, any special character, name, line break
        try:
            self.name_title = re.search(r'((?<=Title(\W)).+[^\n])', self.text, re.IGNORECASE).group(1)
            return(self.name_title)
        except:
            #print("Keyword {} not found in document".format("'Title'"))
            pass 

    def process_name_first_line(self):
        try:
        # extract first line of document 
        # regex: last line break of first string, name, line break
            self.name_first = re.search(r'([^\n].+[^\n])', self.text).group(1)
            return(self.name_first)
        except:
            pass

    def extract_process_names(self):
        # check which process name appear how often
        functions = [self.process_name_keywords(), self.process_name_title(), self.process_name_first_line()]
        names_all = [func for func in functions if func is not None]

        cleaned_lst = [string.lstrip().rstrip() for string in names_all]  # remove leading and end whitespaces
        most_common_names = Counter(cleaned_lst).most_common() # most common substrings out of every method 

        return(most_common_names)
    
    # Process Documents
    # using spacy model, ngrams and keywords
    def extract_documents(self):
    
        # Convert to lowercases
        doc = self.text.lower()
        # Replace all none alphanumeric characters with spaces
        doc = re.sub("[^a-zA-Z]+", " ", doc)

        # apply spacy model (english) that checks whether the doc contains annotation on a token attribute
        nlp = spacy.load('en_core_web_sm',disable=['ner','textcat'])
        doc_spacy = nlp(doc)

        # determine relevant words: 
        # conditions: 1.token == noun, 2. token == noun or adposition, 3. token == noun 
        indices_ngram2 = []
        indices_ngram3 = []
        doc_splitted = str(doc_spacy).split(" ")
        for idx, (token1, token2, token3) in enumerate(zip(doc_spacy, doc_spacy[1:], doc_spacy[2:])):
            # don't take tokens into account which have consists of less then two letters and consist of same words
            if str(token1) != str(token2) and str(token1) != str(token3) and str(token2) != str(token3):
                if len(str(token1)) >= 2 and len(str(token2)) >= 2 and len(str(token3)) >= 2: 

                    if (token1.pos_ == "NOUN") and (token2.pos_ == "NOUN"):
                        indices_ngram2.append(idx)

                    if (token1.pos_ == "NOUN") and (token2.pos_ == "NOUN" or token2.pos_ == "ADP") and (token3.pos_ == "NOUN"):
                        indices_ngram3.append(idx)


        ngrams_process_docs = [2,3]
        for ngram in ngrams_process_docs:
            # generate ngrams (bigrams and trigrmms) starting with a noun word, ngram contains at least one keyword
            ngrams2 = [str(doc_spacy[index:index+2]) for index in indices_ngram2 if any(elem in self.keywords_docs_list for elem in str(doc_spacy[index:index+2]).split())]
            ngrams3 = [str(doc_spacy[index:index+3]) for index in indices_ngram3 if any(elem in self.keywords_docs_list for elem in str(doc_spacy[index:index+3]).split())]

            # count ngrams 
            most_common_ngrams2 = Counter(ngrams2).most_common()
            most_common_ngrams3 = Counter(ngrams3).most_common()

    
        return([most_common_ngrams2, most_common_ngrams3])
    
    
    def extract_date(self):
        # This function is used to find diffenet date attributes in the process documents
        
        cleaned_text = self.preprocessing_text_date()
        # searched those keywords in each line and return only those lines
        header = [ t for t in cleaned_text.split('\n') if any([key in t for key in self.keywords_date_list])]

        #Put the output in a dataframe with keywords and the date value that it corresponds to
        df = pd.DataFrame(header,columns=['content'])

        #Only keep the rows that has atleast 2 digit numbers in the content column
        df = df[df['content'].str.contains('\d\d')]

        # delete all the duplicates
        df=df.drop_duplicates(subset=None, keep='first', inplace=False)

        # create a column that shows the keywords which corresponds to the date value
        df['extract'] = df.content.str.extract('({})'.format('|'.join(self.keywords_date_list)), flags=re.IGNORECASE, expand=False).str.lower().fillna('')

        # Just keep the rows that has value in the column 
        df=df[df.extract != ''] 

        #Create a date column that has value after the word in the column Extract
        df['date']=df.apply(lambda x: x['content'].split(x['extract'])[1], axis=1)

        #Drop the table content
        df=df.drop('content',axis=1)

        # needs to be modified . jus tfor one use case
        df['date'] = [x.split('last revision')[0] for x in df['date']]
        df = df[df['date'].str.contains('\d\d')]
        
        #df['date'] = self.calcu(df.date)
        # we use function calcu
        df['date'] = df.date.apply(self.calcu)

        df=df.drop_duplicates(subset=None, keep='first', inplace=False).sort_values(['date'], ascending=[True]).reset_index(drop = True)
        df.date = df.date.astype(str)
        today = datetime.today().strftime('%Y-%m-%d')

        # date should be less than today because the datefinder sometimes take any numbers and give a random dates
        df = df[(df['date'] <= today)]

        return list(df[['extract', 'date']].itertuples(index=False, name=None))

    def find_linked_processes(self):
        try:
            #look for term related documents
            linkeddocs = re.findall(r'(.+RELATED DOCUMENTS[^\n]+\n)', self.text, flags = re.IGNORECASE)
            #convert first entry of the list to string
            string = str(linkeddocs[0])

            #get all lines after the string
            relateddocs = self.text[self.text.find(string):]

            #as there seems to be some odd whitespaces, I remove all whitespaces
            relateddocsnospaces = relateddocs.replace(" ", "")

            #I split the string for every \n, one time without white spaces and one time with white spaces
            relateddocssplitnospaces = relateddocsnospaces.split("\n")
            relateddocssplit = relateddocs.split("\n")

            #I check for all linked process documents based on when there are more linbreaks than 1
            for line in range(len(relateddocssplitnospaces)):
                if relateddocssplitnospaces[line] == "" and relateddocssplitnospaces[line+1] == "":
                    position = line
                    break
            
             #I split the list on the above solution
            finalrelateddocs = relateddocssplit[0:position]

            #I remove empty strings
            finallist = list(filter(None, finalrelateddocs))

            #return finallist
            return finallist
        
        except: 
            return [None]

    def find_linked_processes1(self):
        try:
            #Find all sentences which include for more information
            fmi = re.findall(r'([^.]*For more information[^.]+.)', self.text, flags = re.IGNORECASE)

            #remove line breaks
            fmiclean = []
            for element in fmi:
                fmiclean.append(element.replace("\n",""))
            return fmiclean
        except: 
            return [None]
    
    def comb_linked_processes(self):

        #check for the different extraction methods
        related = re.findall(r'(.+RELATED DOCUMENTS[^\n]+\n)', self.text, flags = re.IGNORECASE)
        fmi = re.findall(r'([^.]*For more information[^.]+.)', self.text, flags = re.IGNORECASE)

        #depending on the outcome, use the respective function
        if related:
            return self.find_linked_processes()
        elif fmi:
            return self.find_linked_processes1()
        else:
            return [None]
        
    def extract_description(self):

        text = self.text.replace("..", "")
        text = text.lower()

        numeration_start = ['i', '1']
        numeration_end = ['ii', '2']
        character = ['\.', '\)', ' ', '\:']

        joiner = "".join
        a = [numeration_start,character]
        b = list(itertools.product(*a))
        search_start = [joiner(words) for words in b]
        a = [numeration_end,character]
        b = list(itertools.product(*a))
        search_end = [joiner(words) for words in b]

        description_lst = []

        for i in range(len(search_start)):
            try:
                string = re.search(r'\n{}(.*?)\n{}'.format(search_start[i], search_end[i]), text, re.DOTALL).group(1)
                if any(x in string for x in self.keywords_description_list):
                    substring = string[string.find('\n'):]
                    description = ' '.join(substring.split())
                    if len(description) > 10:
                        description_lst.append(description)
            except: 
                pass
            
        return description_lst


    def create_dict(self):
        d = {}
        d["name"] = self.extract_process_names()
        d["date"] = self.extract_date()
        d["description"] = self.extract_description()
        d["documents (bigrams)"] = self.extract_documents()[0] # show just top 3 most mentioned documents
        d["documents (trigrams)"] = self.extract_documents()[1] # show just top 3 most mentioned documents
        d["linked processes"] = self.comb_linked_processes()

        return d 
    
    def create_df(self):
        
        process_name = self.extract_process_names()
        date = self.extract_date()
        description = self.extract_description()
        documents_bigrams = self.extract_documents()[0] # show just top 3 most mentioned documents
        documents_trigrams = self.extract_documents()[1] # show just top 3 most mentioned documents
        related_documents = self.comb_linked_processes()

        df = pd.DataFrame(columns=["meta information", "value", "count"])
        
        for i in range(len(process_name)):
            df = df.append({'meta information':"name", 'value':process_name[i][0], 'count':int(process_name[i][1])}, ignore_index=True)

        for i in range(len(date)):
            df = df.append({'meta information':date[i][0], 'value':date[i][1], 'count':None}, ignore_index=True)

        for i in range(len(description)):
            if len(description) > 1:
                df = df.append({'meta information':'description'+str(i), 'value':description[i], 'count':None}, ignore_index=True)
            else:
                df = df.append({'meta information':'description', 'value':description[i], 'count':None}, ignore_index=True)

        for i in range(len(documents_bigrams)):
            df = df.append({'meta information':'documents (2-gram)', 'value':documents_bigrams[i][0], 'count':documents_bigrams[i][1]}, ignore_index=True)

        for i in range(len(documents_trigrams)):    
            df = df.append({'meta information':'documents (3-gram)', 'value':documents_trigrams[i][0], 'count':documents_trigrams[i][1]}, ignore_index=True)

        for i in range(len(related_documents)):    
            df = df.append({'meta information':'linked processes', 'value':related_documents[i], 'count':None}, ignore_index=True)
            
        return df 






