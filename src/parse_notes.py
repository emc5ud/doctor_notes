
from itertools import product
from operator import itemgetter
import difflib
import pandas as pd
import sys

TNM_VALUES = {'T': ['TX', 'Tis', 'T1', 'T1mi', 'T1a',
                    'T1b', 'T1c', 'T2', 'T2a', 'T2b',
                    'T3', 'T4'],
              'N': ['Nx', 'N0', 'N1', 'N2', 'N3'],
              'M': ['Mx', 'M0', 'M1', 'M1a', 'M1b', 'M1c']
              }

STAGE_INDICATORS = ['stage', 'stg', 'stge']
STAGE_NUMS = ['I', 'II', 'III', 'IV', '1', '2', '3', '4']
STAGE_SUBCAT = ['A', 'B', 'C']
STAGE_SUBSUBCAT = ['1', '2', '3']


'''
Extract the T, N, and M staging values from a doctor note

Parameters
----------
words: list
    The list of words within the note
Returns
-------
dict
    Dictionary mapping the keys 'T', 'N' and 'M' to their found values 
'''
def extract_TNM(words):
    tnm = dict({'T': 'Not Reported',
                'N': 'Not Reported',
                'M': 'Not Reported'})

    for word in map(str.lower, words):
        new_tnm = {}

        remaining_word = word
        for tnm_key in TNM_VALUES.keys():
            found_values = [value for value in TNM_VALUES[tnm_key] if value.lower() in word]
            if len(found_values) > 0:
                new_tnm[tnm_key] =  max(found_values, key=len)
                remaining_word = remaining_word.replace(new_tnm[tnm_key].lower(), '')

        # only update tnm dict if entire word is composed of the tmn values
        # eliminates the possiblilty of 'Tis' being flagged in 'tissue'
        if len(remaining_word) == 0:
            for key in new_tnm:
                tnm[key] = new_tnm[key]
    return tnm


'''
Extract the detailed stage group information from a doctor note

Parameters
----------
words: list
    The list of words within the note
Returns
-------
str
    String containing the group information
'''
def extract_stage(words):

    stage = 'Not Reported'

    # first attempt to look for words indicating stage will be specified next
    for i in range(len(words) - 1):
        if words[i].lower() in STAGE_INDICATORS:
            potential_stage = words[i+1].upper()
            # ensure that the found stage starts with a valid stage group number
            valid_stage = max(potential_stage.startswith(stage_num)
                              for stage_num in STAGE_NUMS + ['0'])
            if valid_stage:
                stage = potential_stage

    # if no valid stage found, then try to look at each word and check for matches with known stage groups
    stage_options = load_stage_options()
    if stage == 'Not Reported':
        matches = [word.upper() for word in words if word.upper() in stage_options]
        if len(matches) > 0:
            stage = max(matches, key=len)

    # standardize reporting by giving roman numeral of first digit
    conv_dict = {'1': 'I', '2': 'II', '3': 'III', '4': 'IV'}
    if stage[0] in conv_dict:
        stage = conv_dict[stage[0]] + stage[1:]

    return stage


'''
Extract the histology information from a doctor note, using a known list of histology types

Parameters
----------
words: list
    The list of words within the note
    
histologies: list
    The list of phrases describing possible cancer histologies
Returns
-------
str
    string containing the histology type that best matches a sequence in the input note
'''
def extract_histology(words, histologies):

    # list of tuples containing (candidate_sequence, matching_histology, match_score)
    seq_match_score = []
    # contains subsequences within a note
    sequences = []

    # construnct 1, 2, 3 length word sequences within words using consecutive elements
    # eg: ['1', '2', '3'] -> ['1', '1 2', '1 2 3', '2', '2 3', '3']
    for i in range(len(words)):
        sequences += [words[i]]
        if i < len(words) - 1:
            sequences += [' '.join(words[i:i+2])]
        if i < len(words) - 2:
            sequences += [' '.join(words[i:i+3])]

    # find the sequence that best matches a histological phrase in the histologies list
    # if a match with a similarity score of at least .6 is not found, return 'Not Reported'
    for sequence in sequences:
        matches = difflib.get_close_matches(sequence, histologies, n=1, cutoff=.6)
        if len(matches) == 0:
            best_match = 'Not Reported'
            score = 0
        else:
            best_match = matches[0]
            score = difflib.SequenceMatcher(None, sequence, best_match).ratio()
        seq_match_score += [(sequence, best_match, score)]

    return max(seq_match_score, key=itemgetter(2))[1]


'''uses itertools.product to get all possible valid stage group values'''
def load_stage_options():
    stage_options = ['0', '0a', '0is'] + STAGE_NUMS + \
                    list(product(*[STAGE_NUMS, STAGE_SUBCAT, STAGE_SUBSUBCAT])) + \
                    list(product(*[STAGE_NUMS, STAGE_SUBCAT]))
    return [''.join(option).upper() for option in stage_options]


'''
Load in histology types from an external csv. Limit word length of types using max_num_words

Parameters
----------
filename: str
    path to csv contianing histology information
    
max_word_length: list
    limit setting the max number of words in a phrase
    
Returns
-------
list
    list containing ~1000 terms for max_word_length=3
'''
def load_histological_phrases(filename, max_word_length=3):

    try:
        open(filename, 'rb').close()
    except OSError:
        print ("Could not open/read file:", filename)
        sys.exit()

    df = pd.read_csv(filename)

    locations = list(df['Site Description'].str.lower().str.replace(',', '').unique())
    histology_description = list(df['Histology Description'].str.lower().str.replace(',', '').unique())
    histology_behaviour = list(df['Histology/Behavior Description'].str.lower().str.replace(',', '').unique())
    histology_terms = locations + histology_description + histology_behaviour

    short_terms = list(term for term in histology_terms if len(term.split()) <= max_word_length)
    return short_terms


'''read file of doctor notes and extract information'''
def parse_notes_file(filename):

    try:
        open(filename, 'rb').close()
    except OSError:
        print ("Could not open/read file:", filename)
        sys.exit()

    notes = [line.strip() for line in open(filename) if line.strip()]

    histological_phrases = load_histological_phrases('../resources/histologies.csv')

    for note in notes:
        print(note)
        words = note.split()
        tnm = extract_TNM(words)
        stage = extract_stage(words)
        histology = extract_histology(words, histological_phrases)
        print('Histologic Type:', histology)
        print('Stage:', stage)
        print('T:', tnm['T'])
        print('N:', tnm['N'])
        print('M:', tnm['M'])
        print()



if __name__ == '__main__':
    parse_notes_file('../resources/doctor_notes.txt')
