import logging
import pandas as pd
from . import global_utils as gbut
from . import global_vars as gv

logger = logging.getLogger("pipeline.google-search")
# infra
class EvaluationInfra:
    def set_data_dir(self):
        return gv.CSV_DIR
    
    def set_fn_load(self):
        return "output-google-search-level-2_1.csv"
    
    def set_fn_save(self):
        return "evaluation-google-search.csv"

    def load_csv(self, path):
        return pd.read_csv(path, encoding="utf-8-sig")

    def save_df(self, path, df):
        gbut.save_csv(path, df)


class PrepSearchInfra:
    def set_url(self, url_format, main_word, additional_word) -> list:
        return [
            url_format.format(word1=word, word2=add)
            for word, add in zip(main_word, additional_word)
        ]
    
    def set_save_dir(self):
        return gv.CSV_DIR

    def set_fn_save(self):
        return f"output-google-search-level-1_1.csv"
    
    def save_csv(self, path, df):
        gbut.save_csv(path, df) 
