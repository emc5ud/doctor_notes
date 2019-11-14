import unittest
import parse_notes


class TestExtractMethods(unittest.TestCase):

    def test_extract_stage(self):
        words = 'Patient has Stage IIIA1 somethingeomething'.split(' ')
        self.assertEqual(parse_notes.extract_stage(words), 'IIIA1')
        words = 'Patient has Stage IIB3 somethingeomething'.split(' ')
        self.assertEqual(parse_notes.extract_stage(words), 'IIB3')
        words = '4 is the stage of this cancer'.split(' ')
        self.assertEqual(parse_notes.extract_stage(words), 'IV')
        words = 'John Doe has some kind of cancer with a stage grouping of 0is'.split(' ')
        self.assertEqual(parse_notes.extract_stage(words), '0IS')

    def test_extract_TNM(self):
        words = 'Patient has N0 T2a M0'.split()
        tnm = parse_notes.extract_TNM(words)
        self.assertEqual(tnm['T'], 'T2a')
        self.assertEqual(tnm['N'], 'N0')
        self.assertEqual(tnm['M'], 'M0')

        words = 'Patient has stage 3 N0T2a  M0'.split()
        tnm = parse_notes.extract_TNM(words)
        self.assertEqual(tnm['T'], 'T2a')
        self.assertEqual(tnm['N'], 'N0')
        self.assertEqual(tnm['M'], 'M0')

        words = 'Patient has stage 3 N0T2a  M7'.split()
        tnm = parse_notes.extract_TNM(words)
        self.assertEqual(tnm['T'], 'T2a')
        self.assertEqual(tnm['N'], 'N0')
        self.assertEqual(tnm['M'], 'Not Reported')

        words = 'larynx mantis mxxxxxxxxxx'.split()
        tnm = parse_notes.extract_TNM(words)
        self.assertEqual(tnm['T'], 'Not Reported')
        self.assertEqual(tnm['N'], 'Not Reported')
        self.assertEqual(tnm['M'], 'Not Reported')

    def test_histology(self):
        histologies = parse_notes.load_histological_phrases('../resources/histologies.csv')
        words = 'The patient has a Final pathology  revealed a T1a N0 Mx' \
                'stage Ia adenocarcinoma with no associated Carcinoma genetic mutation.'.split()
        self.assertEqual(parse_notes.extract_histology(words, histologies),
                         'adenocarcinoma nos')

        words = 'Patient has Stage 4 Adenocarcinoma in Situ TXN0M1c'.split()
        self.assertEqual(parse_notes.extract_histology(words, histologies),
                         'adenocarcinoma in situ')

        words = 'Patient has Stage 4 TXN0 hodgkn lymphma M1c'.split()
        self.assertEqual(parse_notes.extract_histology(words, histologies),
                         'hodgkin lymphoma')

if __name__ == '__main__':
    unittest.main()