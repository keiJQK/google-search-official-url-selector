import logging, itertools
import pandas as pd
from urllib.parse import urlparse
from . import global_utils  as gbut
logger = logging.getLogger("pipeline.google-search")

class PrepSearchUsecase:
    '''
    Responsiblity
    -----
    Create and save pd.DataFrame for the subsequent step of scraping.
        
    '''
    def __init__(self, session):
        '''
        input:
            - session(infra)
        '''
        self.infra = session
        
        # from .google_search_infrastructure import PrepSearchInfra
        # self.infra = PrepSearchInfra() 

    def run(self, ctx):
        '''
            input:
            - ctx(DTO):
                - main_word(list) 
                - additional_word(list)
                - url_format(str)
        output:
            - csv(saved)
                title(main word), URL for subsequent step of scraping
        '''
        main_word:list = ctx.main_word 
        additional_word:list = ctx.additional_word
        url_format:str = ctx.url_format


        save_path = self.create_save_path()
        search_url = self.infra.set_url(
            url_format=url_format,
            main_word=main_word, 
            additional_word=additional_word
            )
        df = self.create_df(main_word, search_url)
        df = self.add_columns(df=df)
        self.infra.save_csv(save_path, df)        
    
    def create_save_path(self):
        save_dir = self.infra.set_save_dir()
        fn_save = self.infra.set_fn_save()
        return save_dir / fn_save

    def create_df(self, main_word, search_url):
        data = {
            "title": main_word,
            "url": search_url
        }
        return pd.DataFrame(data)

    def add_columns(self, df):
        df.insert(0, "index", 1)
        df.insert(1, "sq", range(1, len(df)+1))
        return df

class EvalSetup:
    '''
    Responsibility
    -----
    Set load and save paths into ctx(DTO)
    '''
    def __init__(self, session):
        '''
        input:
            - session(infra)
        '''
        self.infra = session

        # from .google_search_infrastructure import EvaluationInfra
        # self.infra = EvaluationInfra()
    def run(self, ctx):
        '''
        input:
            - ctx(DTO)
                Nothing
        output:
            - ctx.path_load
            - ctx.path_save
        '''
        data_dir = self.infra.set_data_dir()
        fn_load = self.infra.set_fn_load()
        path_load = data_dir / fn_load

        fn_save = self.infra.set_fn_save()
        path_save = data_dir / fn_save
        
        ctx.path_load = path_load
        ctx.path_save = path_save

class EvalCreateDataset:
    '''
    Responsiblity
    -----
    Create dataset dict to evaluate searching results
    '''
    def __init__(self, session):
        '''
        input:
            - session(infra)
        '''
        self.infra = session

        # from .google_search_infrastructure import EvaluationInfra
        # self.infra = EvaluationInfra()

    def run(self, ctx):
        '''
        input:
            - ctx(DTO)
                path_load(Path)
                main_word(list)
                words_evaluated(list)

        output:
            - ctx.dataset:dict
                e.g {1: 
                        {
                            'data': pd.Dataframe,
                            'main_word': ,
                            'words_eval': 
                        }
                    }
        '''
        path_load = ctx.path_load
        main_word = ctx.main_word
        words_evaluated = ctx.words_evaluated


        df = self.infra.load_csv(path_load)
        df = self.setup_df(df)
        dataset = self.create_dataset(df)
        dataset = self.add_dataset(main_word, words_evaluated, dataset)        
        ctx.dataset = dataset

    def setup_df(self, df):
        df["score"] = 0
        df["is_access"] = False
        return df
    
    def create_dataset(self, df):
        dataset = {}
        unique_indices = df["index"].unique()
        for idx in unique_indices:
            small = df.loc[df["index"] == idx]
            dataset[int(idx)] = {}
            dataset[int(idx)]["data"] = small
        return dataset

    def add_dataset(self, main_word, words_evaluated, dataset):
        gbut.log_print(logger, main_word)
        for i, n, w in zip(range(1, len(main_word)+1), main_word, words_evaluated):
            dataset[i]["main_word"] = n
            dataset[i]["words_eval"] = w
        return dataset

class EvalOneFlow:
    '''
    Responsibility
    -----
    Select one website as official throught evaluation
    '''
    def __init__(self, session):
        '''
        input:
            - session(infra)
        '''
        self.infra = session
        # from .google_search_infrastructure import EvaluationInfra
        # self.infra = EvaluationInfra()

    def run(self, ctx):
        '''
        input:
            - ctx(DTO)
                - dataset(dict)
                - path_save(Path)
        output:
            - csv(saved)
        '''
        dataset = ctx.dataset
        path_save = ctx.path_save

        df_save_list = []
        for data in dataset.values():
            df = data["data"]
            name_patterns = self.generate_name_patterns(data["main_word"])
            df = self.one_flow(data, name_patterns, df)
            df_save_list.append(df)
        df_concat = pd.concat(df_save_list, ignore_index=True)
        self.infra.save_df(path_save, df_concat)

    def generate_name_patterns(self, main_word):
        '''
        company name: Nice Restaurant
        -> For evaluation of URL, create name pattern like [nice-restaurant, nice_restaurant, nicerestaurant]
        '''
        name_patterns = []

        # Check if company name is one single word 
        parts = main_word.lower().split()
        if len(parts) == 1:
            name_patterns = parts
            return name_patterns
        
        # Create name patters of company name with 2+ words
        connectors = ['-', '_', '']  

        for combo in itertools.product(connectors, repeat=len(parts) - 1):
            joined = ''.join(p + c for p, c in zip(parts, combo)) + parts[-1]
            name_patterns.append(joined)
        return name_patterns

    def one_flow(self, data, name_patterns, df):
        score_dict = {}
        for _, row in data["data"].iterrows():
            score = self._calc_official_score(row, name_patterns, data["words_eval"])
            score_dict[row["sq"]] = score

        for sq, sc in score_dict.items():            
            df = self._set_score(sq, sc, df)

        max_score = self._get_highest_score(score_dict)
        best_sq = self._get_sq_of_upper_result(score_dict, max_score)
        df = self._set_access_flag(df, best_sq)
        return df

    def _calc_official_score(self, row, name_patterns, words_eval):
        score = 0
        title = row["title"]
        snippet = row["snippet"]
        url = row["url"]

        parsed = urlparse(url)
        domain_part = parsed.netloc.lower() 

        # Base point
        url_score = 5 if any(name in domain_part for name in name_patterns) else 0
        domain_score = 1 if any(url.endswith(tld) for tld in [".co.jp", ".jp", ".com"]) else 0
        official_score = 4 if any(k in snippet for k in ["公式", "オフィシャル", "official"]) else 0
        corporate_score = 2 if any(k in snippet for k in ["企業情報", "会社概要"]) else 0
        words = words_eval or []
        for w in set(words):
            if w in snippet:
                score += 1
        score += (url_score + domain_score + official_score + corporate_score)

        # Additional point
        if url_score > 0 and official_score > 0:
            score += 3  

        if any(k in url for k in ["recruit", "facebook", "x.com", "instagram", "note.", "youtube", "blog", "wikipedia"]):
            score = 0
            # logger.info(f"snippet_exclusion - {score}")
        return score
        
    def _set_score(self, sq, score, df):
        df.loc[df["sq"] == sq, "score"] = score
        return df

    def _get_highest_score(self, score_dict):
        # Select highest score of url
        return max(score_dict.values()) if score_dict else 0
    
    def _get_sq_of_upper_result(self, score_dict, max_score):
        # Select upper search result if highest score is the same
        return min([sq for sq, sc in score_dict.items() if sc == max_score])

    def _set_access_flag(self, df, best_sq):
        df.loc[df["sq"] == best_sq, "is_access"] = True
        return df

# For check to evaluate weight of each point
def combo():
    factors = ["url", "domain", "official", "corporate", "words"]
    patterns = []
    for combo in itertools.product([0, 1], repeat=len(factors)):
        url, domain, official, corporate, words = combo
        score = url*5 + domain*1 + official*4 + corporate*2 + words*1 
        if url == 1 and official == 1:
            score += 2
        patterns.append({
            "url": url,
            "domain": domain,
            "official": official,
            "corporate": corporate,
            "words": words,
            "score": score
        })
    patterns_sorted = sorted(patterns, key=lambda x: x["score"], reverse=True)
    for p in patterns_sorted:
        print(p)


    

